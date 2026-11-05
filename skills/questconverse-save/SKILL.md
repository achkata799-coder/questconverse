---
name: questconverse-save
description: Save, resume, migrate, export, and conflict-handle QuestConverse campaigns in local folders or authorized storage.
---

# QuestConverse Save

Use this skill when the player asks to save, resume, export, migrate, or recover a campaign.

## Rules
- Treat the local campaign folder as canonical first.
- Write `questforge.json` last when saving.
- Read before overwrite and stop on a newer or divergent copy.
- Keep portable ZIP export available for backup and transfer.
- Never delete a legacy copy during migration without explicit user direction.
- Keep save reports short and factual.

## Scope
- Local campaign root
- Optional mounted cloud or synced folder when authorized
- Portable ZIP export when direct sync is unavailable

## Typical outputs
- current session and scene
- save status
- missing files or conflicts
- export path when available
