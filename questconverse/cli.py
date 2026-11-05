from __future__ import annotations

from pathlib import Path
import typer

from .config import QuestConverseConfig
from .engine import QuestConverseEngine

app = typer.Typer(add_completion=False)


@app.command()
def run(config: Path = typer.Option(Path("config.json"), help="Path to config.json")) -> None:
    runtime_config = QuestConverseConfig.from_file(config)
    engine = QuestConverseEngine(runtime_config)
    output = engine.run_turn()
    typer.echo(output)


if __name__ == "__main__":
    app()
