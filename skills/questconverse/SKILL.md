---
name: questconverse
description: Host-agnostic local RPG runtime for LM Studio. Use when the user wants to start, continue, or build a Questforge-style campaign with local tools and persistent campaign files.
---

# QuestConverse

Use this skill as the main entry point for a local tabletop RPG session.

## Core behavior
- Treat the campaign files as the source of truth.
- Use the same language as the player.
- Keep narration vivid, concise, and action-ready.
- End scene beats with a clear question or decision point.
- Preserve continuity across sessions, checkpoints, and saves.

## Companion skills
- Use `questconverse-save` for saves, resume, export, and conflict handling.
- Use `questconverse-campaign` for world state, NPCs, factions, clues, and sessions.
- Use `questconverse-rules` for dice, DCs, combat, and uncertainty.
- Use `questconverse-visuals` for optional images, maps, and scene media.

## Tool guidance
- Prefer local file tools for canonical state.
- Use shell, browser, screenshots, and web lookup only when the host exposes them.
- Never silently overwrite a newer save or an unknown campaign.
- Ask for player intent before major irreversible changes.

## Canonical files
- `questforge.json`
- `game-state.json`
- `player-journal.md`
- `sessions/`
- `checkpoints/`
- `dm/`
- `images/`

## First turn
Start with a short opening scene, the current problem, and one clear question:
what do you do?
