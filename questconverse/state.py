from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import shutil


@dataclass
class CampaignState:
    campaign_id: str = "default"
    campaign_name: str = "QuestConverse Campaign"
    session_id: str = "session-001"
    scene_id: str = "scene-001"
    turn_index: int = 0
    hero_name: str = "Hero"
    location: str = ""
    objective: str = ""
    world_summary: str = ""
    current_scene: str = ""
    inventory: list[str] = field(default_factory=list)
    clues: list[str] = field(default_factory=list)
    checkpoints: list[dict[str, Any]] = field(default_factory=list)
    factions: dict[str, int] = field(default_factory=dict)
    clocks: dict[str, Any] = field(default_factory=dict)
    flags: dict[str, Any] = field(default_factory=dict)
    journal: list[str] = field(default_factory=list)
    session_log: list[dict[str, str]] = field(default_factory=list)
    hidden_gm_notes: str = ""

    @classmethod
    def load(cls, campaign_root: str | Path) -> "CampaignState":
        root = Path(campaign_root)
        quest_path = root / "questforge.json"
        if quest_path.exists():
            data = json.loads(quest_path.read_text(encoding="utf-8"))
            return cls.from_dict(data)

        game_state = root / "game-state.json"
        if game_state.exists():
            data = json.loads(game_state.read_text(encoding="utf-8"))
            return cls.from_dict(data)

        return cls()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CampaignState":
        return cls(
            campaign_id=str(data.get("campaign_id", "default")),
            campaign_name=str(data.get("campaign_name", "QuestConverse Campaign")),
            session_id=str(data.get("session_id", "session-001")),
            scene_id=str(data.get("scene_id", "scene-001")),
            turn_index=int(data.get("turn_index", 0)),
            hero_name=str(data.get("hero_name", "Hero")),
            location=str(data.get("location", "")),
            objective=str(data.get("objective", "")),
            world_summary=str(data.get("world_summary", "")),
            current_scene=str(data.get("current_scene", "")),
            inventory=list(data.get("inventory", [])),
            clues=list(data.get("clues", [])),
            checkpoints=list(data.get("checkpoints", [])),
            factions=dict(data.get("factions", {})),
            clocks=dict(data.get("clocks", {})),
            flags=dict(data.get("flags", {})),
            journal=list(data.get("journal", [])),
            session_log=list(data.get("session_log", [])),
            hidden_gm_notes=str(data.get("hidden_gm_notes", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "session_id": self.session_id,
            "scene_id": self.scene_id,
            "turn_index": self.turn_index,
            "hero_name": self.hero_name,
            "location": self.location,
            "objective": self.objective,
            "world_summary": self.world_summary,
            "current_scene": self.current_scene,
            "inventory": self.inventory,
            "clues": self.clues,
            "checkpoints": self.checkpoints,
            "factions": self.factions,
            "clocks": self.clocks,
            "flags": self.flags,
            "journal": self.journal,
            "session_log": self.session_log,
            "hidden_gm_notes": self.hidden_gm_notes,
        }

    def ensure_layout(self, campaign_root: str | Path) -> None:
        root = Path(campaign_root)
        for path in [
            root,
            root / "sessions",
            root / "checkpoints",
            root / "images",
            root / "dm",
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def append_journal(self, entry: str) -> None:
        if entry:
            self.journal.append(entry)

    def append_session_entry(self, role: str, content: str) -> None:
        self.session_log.append({"role": role, "content": content})
        self.turn_index += 1

    def create_checkpoint(self, campaign_root: str | Path, label: str, reason: str = "") -> Path:
        root = Path(campaign_root)
        self.ensure_layout(root)
        payload = {
            "label": label,
            "reason": reason,
            "state": self.to_dict(),
        }
        path = root / "checkpoints" / f"{self.scene_id}-{self.turn_index:04d}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.checkpoints.append({"label": label, "reason": reason, "path": str(path)})
        return path

    def export_zip(self, campaign_root: str | Path, output_path: str | Path) -> Path:
        root = Path(campaign_root)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.make_archive(str(output.with_suffix("")), "zip", root)
        return output if output.suffix == ".zip" else output.with_suffix(".zip")

    def save(self, campaign_root: str | Path) -> Path:
        root = Path(campaign_root)
        self.ensure_layout(root)
        payload = self.to_dict()
        quest_path = root / "questforge.json"
        quest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        game_state = root / "game-state.json"
        game_state.write_text(
            json.dumps(
                {
                    "campaign_id": self.campaign_id,
                    "session_id": self.session_id,
                    "scene_id": self.scene_id,
                    "turn_index": self.turn_index,
                    "hero_name": self.hero_name,
                    "location": self.location,
                    "objective": self.objective,
                    "world_summary": self.world_summary,
                    "current_scene": self.current_scene,
                    "inventory": self.inventory,
                    "clues": self.clues,
                    "checkpoints": self.checkpoints,
                    "factions": self.factions,
                    "clocks": self.clocks,
                    "flags": self.flags,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        journal = root / "player-journal.md"
        journal_lines = [
            f"# {self.campaign_name}",
            "",
            f"Hero: {self.hero_name}",
            f"Location: {self.location or 'Unknown'}",
            f"Objective: {self.objective or 'None yet'}",
            "",
            "## Journal",
        ]
        journal_lines.extend(f"- {entry}" for entry in self.journal[-20:])
        journal.write_text("\n".join(journal_lines).rstrip() + "\n", encoding="utf-8")

        spine = root / "dm" / "adventure-spine.md"
        spine_text = [
            f"# {self.campaign_name}",
            "",
            f"Location: {self.location}",
            f"Objective: {self.objective}",
            "",
            "## Hidden GM Notes",
            self.hidden_gm_notes or "",
        ]
        spine.write_text("\n".join(spine_text).rstrip() + "\n", encoding="utf-8")

        session_file = root / "sessions" / f"{self.session_id}.md"
        session_lines = [f"# Session {self.session_id}", ""]
        for turn in self.session_log:
            session_lines.append(f"**{turn.get('role', 'unknown').title()}:** {turn.get('content', '')}")
            session_lines.append("")
        session_file.write_text("\n".join(session_lines).rstrip() + "\n", encoding="utf-8")

        return quest_path
