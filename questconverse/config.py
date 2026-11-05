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


@dataclass
class QuestConverseConfig:
    lmstudio: LMStudioConfig = field(default_factory=LMStudioConfig)
    campaign_root: Path = Path("campaigns/default")
    system_prompt_path: Path = Path("prompts/questforge_system.md")
    save_policy_path: Path = Path("prompts/save_policy.md")
    tool_policy_path: Path = Path("prompts/tool_policy.md")
    temperature: float = 0.7
    max_turn_tokens: int = 900

    @classmethod
    def from_file(cls, path: str | Path) -> "QuestConverseConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        lm = data.get("lmstudio", {})
        return cls(
            lmstudio=LMStudioConfig(
                base_url=lm.get("base_url", "http://localhost:1234/v1"),
                api_key=lm.get("api_key", "lm-studio"),
                model=lm.get("model", "local-model"),
            ),
            campaign_root=Path(data.get("campaign_root", "campaigns/default")),
            system_prompt_path=Path(data.get("system_prompt_path", "prompts/questforge_system.md")),
            save_policy_path=Path(data.get("save_policy_path", "prompts/save_policy.md")),
            tool_policy_path=Path(data.get("tool_policy_path", "prompts/tool_policy.md")),
            temperature=float(data.get("temperature", 0.7)),
            max_turn_tokens=int(data.get("max_turn_tokens", 900)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "lmstudio": {
                "base_url": self.lmstudio.base_url,
                "api_key": self.lmstudio.api_key,
                "model": self.lmstudio.model,
            },
            "campaign_root": str(self.campaign_root),
            "system_prompt_path": str(self.system_prompt_path),
            "save_policy_path": str(self.save_policy_path),
            "tool_policy_path": str(self.tool_policy_path),
            "temperature": self.temperature,
            "max_turn_tokens": self.max_turn_tokens,
        }
