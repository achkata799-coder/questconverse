# QuestConverse

QuestConverse is a host-agnostic local RPG runtime and skill bundle for LM Studio.
It keeps the Questforge-style game loop, but moves the host layer out of
ChatGPT/Codex and into a local controller that can call tools on your machine.

## What this repo contains

- a local runtime that talks to an OpenAI-compatible LM Studio server
- a prompt bundle for the GM, save, rules, campaign, session, and tool policies
- a skill bundle you can load into an LM Studio agent workflow
- a tool registry for local files and shell actions, with extension points for web and browser tools
- campaign state files stored on disk
- a CLI for starting, initializing, and inspecting a campaign

## Architecture

- **Model backend:** LM Studio
- **Game orchestrator:** QuestConverse controller
- **Tools:** local filesystem, shell, optional external web/browser adapters
- **Canonical memory:** campaign files in a local workspace
- **Skill surface:** `skills/questconverse/SKILL.md` and companion skills

## Quick start

1. Install Python 3.11+.
2. Start LM Studio and enable the OpenAI-compatible server.
3. Copy `config.example.json` to `config.json`.
4. Edit the config with your LM Studio base URL and model name.
5. Install dependencies:

```bash
pip install -r requirements.txt
```

6. Initialize a campaign workspace:

```bash
python -m questconverse.cli init --config config.json
```

7. Run the interactive session:

```bash
python -m questconverse.cli run --config config.json
```

## Configuration

The default config expects an LM Studio server at:

```text
http://localhost:1234/v1
```

QuestConverse sends the system prompt, save policy, rules policy, campaign policy,
session policy, and tool policy to the model. The controller then executes any
requested tools and feeds the results back into the conversation.

## Skill bundle

If your LM Studio workflow can load instruction files directly, use:

- `skills/questconverse/SKILL.md` for the main entry point
- `skills/questconverse-save/SKILL.md` for save and resume behavior
- `skills/questconverse-campaign/SKILL.md` for continuity and state handling
- `skills/questconverse-rules/SKILL.md` for rules and dice behavior
- `skills/questconverse-visuals/SKILL.md` for optional media handling

## Files on disk

Recommended campaign layout:

```text
campaigns/<campaign-name>/
  questforge.json
  game-state.json
  player-journal.md
  dm/
    adventure-spine.md
  sessions/
  checkpoints/
  images/
```

## Status

This repo is a working LM Studio adapter and skill scaffold. It is ready to
extend with your own web, browser, screenshot, or image-generation adapters
without changing the core campaign format.