from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

from .config import QuestConverseConfig


@dataclass
class CampaignState:
    campaign_id: str = "default"
    session_id: str = "session-001"
    scene_id: str = "scene-001"
    hero_name: str = "Hero"
    world_summary: str = ""
    journal: list[str] | None = None
    inventory: list[str] | None = None
    flags: dict[str, Any] | None = None

    @classmethod
    def load(cls, campaign_root: str | Path) -> "CampaignState":
        root = Path(campaign_root)
        path = root / "questforge.json"
        if not path.exists():
            return cls(journal=[], inventory=[], flags={})
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            campaign_id=data.get("campaign_id", "default"),
            session_id=data.get("session_id", "session-001"),
            scene_id=data.get("scene_id", "scene-001"),
            hero_name=data.get("hero_name", "Hero"),
            world_summary=data.get("world_summary", ""),
            journal=data.get("journal", []),
            inventory=data.get("inventory", []),
            flags=data.get("flags", {}),
        )

    def save(self, campaign_root: str | Path) -> Path:
        root = Path(campaign_root)
        root.mkdir(parents=True, exist_ok=True)
        payload = {
            "campaign_id": self.campaign_id,
            "session_id": self.session_id,
            "scene_id": self.scene_id,
            "hero_name": self.hero_name,
            "world_summary": self.world_summary,
            "journal": self.journal or [],
            "inventory": self.inventory or [],
            "flags": self.flags or {},
        }
        path = root / "questforge.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def append_journal(self, entry: str) -> None:
        if self.journal is None:
            self.journal = []
        self.journal.append(entry)
