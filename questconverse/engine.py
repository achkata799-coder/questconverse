from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .config import QuestConverseConfig
from .lmstudio import LMStudioClient
from .state import CampaignState
from .tools import execute_tool


class QuestConverseEngine:
    def __init__(self, config: QuestConverseConfig) -> None:
        self.config = config
        self.client = LMStudioClient(config.lmstudio)
        self.campaign_root = config.campaign_root
        self.state = CampaignState.load(self.campaign_root)
        self.state.ensure_layout(self.campaign_root)
        self.prompt_bundle = self._load_prompt_bundle()

    def _read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def _load_prompt_bundle(self) -> list[str]:
        paths = [
            self.config.system_prompt_path,
            self.config.save_policy_path,
            self.config.tool_policy_path,
            self.config.rules_policy_path,
            self.config.campaign_policy_path,
            self.config.visual_policy_path,
            self.config.session_policy_path,
        ]
        bundle = []
        for path in paths:
            text = self._read_text(path)
            if text.strip():
                bundle.append(text.strip())
        return bundle

    def _tools_schema(self) -> list[dict[str, Any]]:
        return [
            self._tool_schema("fs.read_file", "Read a UTF-8 text file inside the campaign root.", {"path": {"type": "string"}}, ["path"]),
            self._tool_schema(
                "fs.write_file",
                "Write a UTF-8 text file inside the campaign root.",
                {"path": {"type": "string"}, "content": {"type": "string"}},
                ["path", "content"],
            ),
            self._tool_schema(
                "fs.append_file",
                "Append UTF-8 text to a file inside the campaign root.",
                {"path": {"type": "string"}, "content": {"type": "string"}},
                ["path", "content"],
            ),
            self._tool_schema("fs.list_dir", "List files and folders inside the campaign root.", {"path": {"type": "string"}}, []),
            self._tool_schema("fs.make_dir", "Create a directory inside the campaign root.", {"path": {"type": "string"}}, ["path"]),
            self._tool_schema("fs.read_json", "Read a JSON file inside the campaign root.", {"path": {"type": "string"}}, ["path"]),
            self._tool_schema(
                "fs.write_json",
                "Write a JSON file inside the campaign root.",
                {"path": {"type": "string"}, "data": {"type": "object"}},
                ["path", "data"],
            ),
            self._tool_schema("dice.roll", "Roll dice using NdM+K notation.", {"expression": {"type": "string"}}, ["expression"]),
            self._tool_schema("shell.run", "Run a shell command from the campaign root.", {"command": {"type": "string"}}, ["command"]),
            self._tool_schema("web.search", "Run a configured web search command.", {"query": {"type": "string"}}, ["query"]),
            self._tool_schema("web.open", "Run a configured web open command.", {"url": {"type": "string"}}, ["url"]),
            self._tool_schema(
                "browser.screenshot",
                "Run a configured screenshot command.",
                {"url": {"type": "string"}, "path": {"type": "string"}},
                ["url", "path"],
            ),
            self._tool_schema("state.get", "Read the canonical campaign state.", {}, []),
            self._tool_schema(
                "state.patch",
                "Patch the canonical campaign state with a partial object.",
                {"patch": {"type": "object"}},
                ["patch"],
            ),
            self._tool_schema(
                "campaign.create_checkpoint",
                "Create a named checkpoint in the campaign root.",
                {"label": {"type": "string"}, "reason": {"type": "string"}},
                ["label"],
            ),
            self._tool_schema(
                "campaign.export_zip",
                "Export the campaign root as a portable ZIP file.",
                {"output": {"type": "string"}},
                [],
            ),
        ]

    def _tool_schema(self, name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
        schema: dict[str, Any] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {"type": "object", "properties": properties},
            },
        }
        if required:
            schema["function"]["parameters"]["required"] = required
        return schema

    def _system_messages(self) -> list[dict[str, Any]]:
        messages = []
        if self.prompt_bundle:
            for prompt in self.prompt_bundle:
                messages.append({"role": "system", "content": prompt})
        messages.append({"role": "system", "content": f"Canonical campaign state: {json.dumps(self.state.to_dict(), ensure_ascii=False)}"})
        messages.append({"role": "system", "content": f"Campaign root: {self.campaign_root}"})
        return messages

    def _recent_history(self) -> list[dict[str, Any]]:
        history = self.state.session_log[-self.config.max_history_turns :]
        return [{"role": item.get("role", "assistant"), "content": item.get("content", "")} for item in history]

    def _build_messages(self, user_text: str) -> list[dict[str, Any]]:
        messages = self._system_messages()
        messages.extend(self._recent_history())
        messages.append({"role": "user", "content": user_text})
        return messages

    def step(self, user_text: str) -> str:
        messages = self._build_messages(user_text)
        tools = self._tools_schema()
        final_text = ""

        for _ in range(self.config.max_tool_rounds):
            response = self.client.chat(messages, tools=tools)
            choice = response.choices[0].message
            assistant_message = choice.model_dump(exclude_none=True)
            messages.append(assistant_message)

            tool_calls = getattr(choice, "tool_calls", None) or []
            if not tool_calls:
                final_text = choice.content or final_text
                break

            for tool_call in tool_calls:
                arguments = tool_call.function.arguments or "{}"
                try:
                    parsed_arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    parsed_arguments = {"raw_arguments": arguments}
                result = execute_tool(tool_call.function.name, parsed_arguments, self.campaign_root, self.config)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
                self.state.append_session_entry("tool", f"{tool_call.function.name}: {result.get('summary', '')}")

                if result.get("ok") and tool_call.function.name in {"fs.write_file", "fs.append_file", "fs.write_json", "state.patch", "campaign.create_checkpoint", "campaign.export_zip"}:
                    self.state.append_journal(result.get("summary", tool_call.function.name))

        if not final_text:
            final_text = "I’m ready. What do you do next?"

        self.state.append_session_entry("user", user_text)
        self.state.append_session_entry("assistant", final_text)
        self.state.append_journal(final_text)
        self.state.save(self.campaign_root)
        return final_text

    def save(self) -> Path:
        return self.state.save(self.campaign_root)

    def status(self) -> str:
        data = self.state.to_dict()
        lines = [
            f"Campaign: {data.get('campaign_name', 'QuestConverse Campaign')} ({data.get('campaign_id', 'default')})",
            f"Hero: {data.get('hero_name', 'Hero')}",
            f"Location: {data.get('location') or 'Unknown'}",
            f"Objective: {data.get('objective') or 'None'}",
            f"Scene: {data.get('scene_id')} / Turn {data.get('turn_index')}",
            f"Inventory: {', '.join(data.get('inventory', [])) or 'Empty'}",
            f"Clues: {len(data.get('clues', []))}",
            f"Checkpoints: {len(data.get('checkpoints', []))}",
        ]
        return "\n".join(lines)
