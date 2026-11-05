# QuestConverse

QuestConverse is a host-agnostic local RPG runtime for LM Studio.
It keeps the Questforge-style game loop, but moves the host layer out of
ChatGPT/Codex and into a local controller that can call tools on your machine.

## What this repo contains

- a local runtime that talks to an OpenAI-compatible LM Studio server
- a tool registry for file I/O, web search, shell, and browser actions
- campaign state files stored on disk
- prompt modules for the GM policy, save policy, and tool policy
- a minimal CLI to start a session

## Architecture

- **Model backend:** LM Studio
- **Game orchestrator:** QuestConverse controller
- **Tools:** local filesystem, web search, browser, screenshots, shell
- **Canonical memory:** campaign files in a local workspace

## Quick start

1. Install Python 3.11+.
2. Start LM Studio and enable the OpenAI-compatible server.
3. Copy `config.example.json` to `config.json`.
4. Edit the config with your LM Studio base URL and model name.
5. Install dependencies:

```bash
pip install -r requirements.txt
```

6. Run the CLI:

```bash
python -m questconverse.cli run --config config.json
```

## Configuration

The default config expects an LM Studio server at:

```text
http://localhost:1234/v1
```

QuestConverse uses tool calls when the model requests them. Your local adapter
is responsible for executing the tools and returning the results back into the
conversation.

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

This repo is a scaffold. The runtime is intentionally small and can be extended
for your own tools, prompts, and save rules.
