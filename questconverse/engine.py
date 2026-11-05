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
        self.campaign_root.mkdir(parents=True, exist_ok=True)
        self.state = CampaignState.load(self.campaign_root)
        self.system_prompt = self._read_text(config.system_prompt_path)
        self.save_policy = self._read_text(config.save_policy_path)
        self.tool_policy = self._read_text(config.tool_policy_path)

    def _read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def _tools_schema(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "fs.read_file",
                    "description": "Read a UTF-8 text file inside the campaign root.",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fs.write_file",
                    "description": "Write a UTF-8 text file inside the campaign root.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fs.list_dir",
                    "description": "List files and folders inside the campaign root.",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "shell.run",
                    "description": "Run a shell command from the campaign root.",
                    "parameters": {
                        "type": "object",
                        "properties": {"command": {"type": "string"}},
                        "required": ["command"],
                    },
                },
            },
        ]

    def _messages(self) -> list[dict[str, Any]]:
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": self.save_policy},
            {"role": "system", "content": self.tool_policy},
            {
                "role": "system",
                "content": f"Current campaign state: {json.dumps(self.state.__dict__, ensure_ascii=False)}",
            },
            {
                "role": "user",
                "content": "Begin a Questforge-style scene for this campaign and ask the player what they do.",
            },
        ]

    def run_turn(self) -> str:
        messages = self._messages()
        tools = self._tools_schema()
        response = self.client.chat(messages, tools=tools)
        choice = response.choices[0].message

        if choice.tool_calls:
            messages.append(choice.model_dump())
            for tool_call in choice.tool_calls:
                result = execute_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments or "{}"),
                    self.campaign_root,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
            response = self.client.chat(messages, tools=tools)
            choice = response.choices[0].message

        final_text = choice.content or ""
        self.state.append_journal(final_text)
        self.state.save(self.campaign_root)
        return final_text
