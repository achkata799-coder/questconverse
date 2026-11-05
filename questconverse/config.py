from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


@dataclass
class LMStudioConfig:
    base_url: str = "http://localhost:1234/v1"
    api_key: str = "lm-studio"
    model: str = "local-model"
    temperature: float = 0.7
    max_tokens: int = 1200


@dataclass
class QuestConverseConfig:
    lmstudio: LMStudioConfig = field(default_factory=LMStudioConfig)
    campaign_root: Path = Path("campaigns/default")
    system_prompt_path: Path = Path("prompts/questforge_system.md")
    save_policy_path: Path = Path("prompts/save_policy.md")
    tool_policy_path: Path = Path("prompts/tool_policy.md")
    campaign_policy_path: Path = Path("prompts/campaign_policy.md")
    rules_policy_path: Path = Path("prompts/rules_policy.md")
    visual_policy_path: Path = Path("prompts/visual_policy.md")
    session_policy_path: Path = Path("prompts/session_policy.md")
    allow_shell: bool = True
    allow_web: bool = True
    tool_timeout_seconds: int = 180
    web_search_command: str = ""
    web_open_command: str = ""
    browser_screenshot_command: str = ""
    max_turn_tokens: int = 1200
    max_tool_rounds: int = 8
    max_history_turns: int = 24
    opening_prompt: str = "Begin a vivid opening scene and ask the player what they do."

    @classmethod
    def from_file(cls, path: str | Path) -> "QuestConverseConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        lm = data.get("lmstudio", {})
        return cls(
            lmstudio=LMStudioConfig(
                base_url=lm.get("base_url", "http://localhost:1234/v1"),
                api_key=lm.get("api_key", "lm-studio"),
                model=lm.get("model", "local-model"),
                temperature=float(lm.get("temperature", 0.7)),
                max_tokens=int(lm.get("max_tokens", 1200)),
            ),
            campaign_root=Path(data.get("campaign_root", "campaigns/default")),
            system_prompt_path=Path(data.get("system_prompt_path", "prompts/questforge_system.md")),
            save_policy_path=Path(data.get("save_policy_path", "prompts/save_policy.md")),
            tool_policy_path=Path(data.get("tool_policy_path", "prompts/tool_policy.md")),
            campaign_policy_path=Path(data.get("campaign_policy_path", "prompts/campaign_policy.md")),
            rules_policy_path=Path(data.get("rules_policy_path", "prompts/rules_policy.md")),
            visual_policy_path=Path(data.get("visual_policy_path", "prompts/visual_policy.md")),
            session_policy_path=Path(data.get("session_policy_path", "prompts/session_policy.md")),
            allow_shell=bool(data.get("allow_shell", True)),
            allow_web=bool(data.get("allow_web", True)),
            tool_timeout_seconds=int(data.get("tool_timeout_seconds", 180)),
            web_search_command=str(data.get("web_search_command", "")),
            web_open_command=str(data.get("web_open_command", "")),
            browser_screenshot_command=str(data.get("browser_screenshot_command", "")),
            max_turn_tokens=int(data.get("max_turn_tokens", 1200)),
            max_tool_rounds=int(data.get("max_tool_rounds", 8)),
            max_history_turns=int(data.get("max_history_turns", 24)),
            opening_prompt=str(data.get("opening_prompt", "Begin a vivid opening scene and ask the player what they do.")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "lmstudio": {
                "base_url": self.lmstudio.base_url,
                "api_key": self.lmstudio.api_key,
                "model": self.lmstudio.model,
                "temperature": self.lmstudio.temperature,
                "max_tokens": self.lmstudio.max_tokens,
            },
            "campaign_root": str(self.campaign_root),
            "system_prompt_path": str(self.system_prompt_path),
            "save_policy_path": str(self.save_policy_path),
            "tool_policy_path": str(self.tool_policy_path),
            "campaign_policy_path": str(self.campaign_policy_path),
            "rules_policy_path": str(self.rules_policy_path),
            "visual_policy_path": str(self.visual_policy_path),
            "session_policy_path": str(self.session_policy_path),
            "allow_shell": self.allow_shell,
            "allow_web": self.allow_web,
            "tool_timeout_seconds": self.tool_timeout_seconds,
            "web_search_command": self.web_search_command,
            "web_open_command": self.web_open_command,
            "browser_screenshot_command": self.browser_screenshot_command,
            "max_turn_tokens": self.max_turn_tokens,
            "max_tool_rounds": self.max_tool_rounds,
            "max_history_turns": self.max_history_turns,
            "opening_prompt": self.opening_prompt,
        }
