from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .config import QuestConverseConfig
from .engine import QuestConverseEngine

app = typer.Typer(add_completion=False, help="QuestConverse LM Studio runtime")
console = Console()


@app.command()
def run(
    config: Path = typer.Option(Path("config.json"), help="Path to config.json"),
    once: bool = typer.Option(False, help="Run a single assistant turn and exit"),
) -> None:
    runtime_config = QuestConverseConfig.from_file(config)
    engine = QuestConverseEngine(runtime_config)

    if once:
        output = engine.step(runtime_config.opening_prompt)
        console.print(output)
        return

    console.print("[bold]QuestConverse[/bold] ready. Type /exit to quit, /status to inspect state.")
    opening = engine.step(runtime_config.opening_prompt)
    console.print(opening)

    while True:
        try:
            user_text = typer.prompt("You")
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye.")
            break

        text = user_text.strip()
        if not text:
            continue
        if text.lower() in {"/exit", "/quit", "exit", "quit"}:
            console.print("Goodbye.")
            break
        if text.lower() == "/status":
            console.print(engine.status())
            continue
        if text.lower() == "/save":
            engine.save()
            console.print("Saved.")
            continue

        reply = engine.step(text)
        console.print(reply)


if __name__ == "__main__":
    app()
