from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import json
import subprocess


ToolHandler = Callable[[dict[str, Any], Path], dict[str, Any]]


def read_file(args: dict[str, Any], campaign_root: Path) -> dict[str, Any]:
    path = (campaign_root / args["path"]).resolve()
    text = path.read_text(encoding="utf-8")
    return {"ok": True, "tool_name": "read_file", "path": str(path), "content": text}


def write_file(args: dict[str, Any], campaign_root: Path) -> dict[str, Any]:
    path = (campaign_root / args["path"]).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = args.get("content", "")
    path.write_text(content, encoding="utf-8")
    return {"ok": True, "tool_name": "write_file", "path": str(path), "bytes_written": len(content.encode("utf-8"))}


def list_dir(args: dict[str, Any], campaign_root: Path) -> dict[str, Any]:
    path = (campaign_root / args.get("path", ".")).resolve()
    items = []
    for child in sorted(path.iterdir()):
        items.append({"name": child.name, "is_dir": child.is_dir()})
    return {"ok": True, "tool_name": "list_dir", "path": str(path), "items": items}


def run_shell(args: dict[str, Any], campaign_root: Path) -> dict[str, Any]:
    command = args["command"]
    completed = subprocess.run(
        command,
        cwd=campaign_root,
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": completed.returncode == 0,
        "tool_name": "run_shell",
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def load_json(args: dict[str, Any], campaign_root: Path) -> dict[str, Any]:
    path = (campaign_root / args["path"]).resolve()
    return {"ok": True, "tool_name": "load_json", "path": str(path), "data": json.loads(path.read_text(encoding="utf-8"))}


def save_json(args: dict[str, Any], campaign_root: Path) -> dict[str, Any]:
    path = (campaign_root / args["path"]).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(args["data"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"ok": True, "tool_name": "save_json", "path": str(path)}


TOOL_HANDLERS: dict[str, ToolHandler] = {
    "fs.read_file": read_file,
    "fs.write_file": write_file,
    "fs.list_dir": list_dir,
    "shell.run": run_shell,
    "state.load_json": load_json,
    "state.save_json": save_json,
}


def execute_tool(name: str, args: dict[str, Any], campaign_root: Path) -> dict[str, Any]:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return {"ok": False, "tool_name": name, "error": f"Unknown tool: {name}"}
    try:
        return handler(args, campaign_root)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "tool_name": name, "error": str(exc)}
