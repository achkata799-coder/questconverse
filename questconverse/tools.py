from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import json
import random
import re
import shlex
import subprocess
import tempfile
import zipfile

from .config import QuestConverseConfig
from .state import CampaignState


ToolHandler = Callable[[dict[str, Any], Path, QuestConverseConfig], dict[str, Any]]


def _safe_path(campaign_root: Path, rel_path: str) -> Path:
    root = campaign_root.resolve()
    target = (root / rel_path).resolve()
    if target == root or root in target.parents:
        return target
    raise ValueError(f"Path escapes campaign root: {rel_path}")


def _result(tool_name: str, ok: bool, **payload: Any) -> dict[str, Any]:
    data = {"ok": ok, "tool_name": tool_name, **payload}
    summary = payload.get("summary")
    if summary is None:
        if ok:
            summary = f"{tool_name} completed"
        else:
            summary = f"{tool_name} failed"
    data["summary"] = summary
    return data


def read_file(args: dict[str, Any], campaign_root: Path, _: QuestConverseConfig) -> dict[str, Any]:
    path = _safe_path(campaign_root, str(args["path"]))
    text = path.read_text(encoding="utf-8")
    return _result("fs.read_file", True, path=str(path), content=text, summary=f"Read {path.name}")


def write_file(args: dict[str, Any], campaign_root: Path, _: QuestConverseConfig) -> dict[str, Any]:
    path = _safe_path(campaign_root, str(args["path"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    content = str(args.get("content", ""))
    path.write_text(content, encoding="utf-8")
    return _result(
        "fs.write_file",
        True,
        path=str(path),
        bytes_written=len(content.encode("utf-8")),
        files_changed=[str(path)],
        summary=f"Wrote {path.name}",
    )


def append_file(args: dict[str, Any], campaign_root: Path, _: QuestConverseConfig) -> dict[str, Any]:
    path = _safe_path(campaign_root, str(args["path"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    content = str(args.get("content", ""))
    with path.open("a", encoding="utf-8") as handle:
        handle.write(content)
    return _result(
        "fs.append_file",
        True,
        path=str(path),
        bytes_written=len(content.encode("utf-8")),
        files_changed=[str(path)],
        summary=f"Appended to {path.name}",
    )


def list_dir(args: dict[str, Any], campaign_root: Path, _: QuestConverseConfig) -> dict[str, Any]:
    path = _safe_path(campaign_root, str(args.get("path", ".")))
    items = []
    for child in sorted(path.iterdir()):
        items.append({"name": child.name, "is_dir": child.is_dir()})
    return _result("fs.list_dir", True, path=str(path), items=items, summary=f"Listed {len(items)} item(s)")


def make_dir(args: dict[str, Any], campaign_root: Path, _: QuestConverseConfig) -> dict[str, Any]:
    path = _safe_path(campaign_root, str(args["path"]))
    path.mkdir(parents=True, exist_ok=True)
    return _result("fs.make_dir", True, path=str(path), summary=f"Created {path.name}")


def read_json(args: dict[str, Any], campaign_root: Path, _: QuestConverseConfig) -> dict[str, Any]:
    path = _safe_path(campaign_root, str(args["path"]))
    data = json.loads(path.read_text(encoding="utf-8"))
    return _result("fs.read_json", True, path=str(path), data=data, summary=f"Read JSON {path.name}")


def write_json(args: dict[str, Any], campaign_root: Path, _: QuestConverseConfig) -> dict[str, Any]:
    path = _safe_path(campaign_root, str(args["path"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    data = args.get("data", {})
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return _result(
        "fs.write_json",
        True,
        path=str(path),
        files_changed=[str(path)],
        summary=f"Wrote JSON {path.name}",
    )


_DICE_PATTERN = re.compile(r"^(?P<count>\d*)d(?P<sides>\d+)(?P<mod>[+-]\d+)?$", re.IGNORECASE)


def roll_dice(args: dict[str, Any], campaign_root: Path, _: QuestConverseConfig) -> dict[str, Any]:
    expression = str(args["expression"]).strip().replace(" ", "")
    match = _DICE_PATTERN.match(expression)
    if not match:
        raise ValueError(f"Unsupported dice expression: {expression}")
    count = int(match.group("count") or 1)
    sides = int(match.group("sides"))
    modifier = int(match.group("mod") or 0)
    if count < 1 or sides < 2:
        raise ValueError("Dice expression must contain at least one die and two sides")
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls) + modifier
    return _result(
        "dice.roll",
        True,
        expression=expression,
        rolls=rolls,
        modifier=modifier,
        total=total,
        summary=f"Rolled {expression} = {total}",
    )


def run_shell(args: dict[str, Any], campaign_root: Path, config: QuestConverseConfig) -> dict[str, Any]:
    if not config.allow_shell:
        return _result("shell.run", False, error="Shell execution disabled in config")
    command = str(args["command"])
    completed = subprocess.run(
        command,
        cwd=campaign_root,
        shell=True,
        capture_output=True,
        text=True,
        timeout=config.tool_timeout_seconds,
        check=False,
    )
    return _result(
        "shell.run",
        completed.returncode == 0,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        summary=f"Shell exited with code {completed.returncode}",
    )


def _run_template(command_template: str, mapping: dict[str, Any], campaign_root: Path, timeout: int) -> dict[str, Any]:
    if not command_template:
        return {"ok": False, "error": "Tool command not configured"}
    command = command_template.format(**mapping)
    completed = subprocess.run(
        command,
        cwd=campaign_root,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "command": command,
    }


def web_search(args: dict[str, Any], campaign_root: Path, config: QuestConverseConfig) -> dict[str, Any]:
    if not config.allow_web:
        return _result("web.search", False, error="Web tools disabled in config")
    result = _run_template(
        config.web_search_command,
        {"query": args.get("query", ""), "root": str(campaign_root)},
        campaign_root,
        config.tool_timeout_seconds,
    )
    if not result.get("ok"):
        return _result("web.search", False, error=result.get("error", "Web search command not configured"))
    return _result("web.search", True, **result, summary="Web search executed")


def web_open(args: dict[str, Any], campaign_root: Path, config: QuestConverseConfig) -> dict[str, Any]:
    if not config.allow_web:
        return _result("web.open", False, error="Web tools disabled in config")
    result = _run_template(
        config.web_open_command,
        {"url": args.get("url", ""), "root": str(campaign_root)},
        campaign_root,
        config.tool_timeout_seconds,
    )
    if not result.get("ok"):
        return _result("web.open", False, error=result.get("error", "Web open command not configured"))
    return _result("web.open", True, **result, summary="Opened web page")


def browser_screenshot(args: dict[str, Any], campaign_root: Path, config: QuestConverseConfig) -> dict[str, Any]:
    result = _run_template(
        config.browser_screenshot_command,
        {"url": args.get("url", ""), "path": args.get("path", ""), "root": str(campaign_root)},
        campaign_root,
        config.tool_timeout_seconds,
    )
    if not result.get("ok"):
        return _result("browser.screenshot", False, error=result.get("error", "Screenshot command not configured"))
    return _result("browser.screenshot", True, **result, summary="Captured screenshot")


def state_get(args: dict[str, Any], campaign_root: Path, _: QuestConverseConfig) -> dict[str, Any]:
    state = CampaignState.load(campaign_root)
    return _result("state.get", True, data=state.to_dict(), summary="Loaded campaign state")


def state_patch(args: dict[str, Any], campaign_root: Path, _: QuestConverseConfig) -> dict[str, Any]:
    state = CampaignState.load(campaign_root)
    patch = dict(args.get("patch", {}))
    current = state.to_dict()
    current.update(patch)
    updated = CampaignState.from_dict(current)
    updated.save(campaign_root)
    return _result("state.patch", True, data=updated.to_dict(), summary="Patched campaign state")


def create_checkpoint(args: dict[str, Any], campaign_root: Path, _: QuestConverseConfig) -> dict[str, Any]:
    state = CampaignState.load(campaign_root)
    label = str(args.get("label", "checkpoint"))
    reason = str(args.get("reason", ""))
    path = state.create_checkpoint(campaign_root, label=label, reason=reason)
    state.save(campaign_root)
    return _result("campaign.create_checkpoint", True, path=str(path), summary=f"Created checkpoint {path.name}")


def export_zip(args: dict[str, Any], campaign_root: Path, _: QuestConverseConfig) -> dict[str, Any]:
    output = args.get("output")
    if output:
        output_path = _safe_path(campaign_root.parent, str(output))
    else:
        fd, tmp_name = tempfile.mkstemp(prefix="questconverse-", suffix=".zip")
        Path(tmp_name).unlink(missing_ok=True)
        output_path = Path(tmp_name)
    state = CampaignState.load(campaign_root)
    output_zip = state.export_zip(campaign_root, output_path)
    return _result("campaign.export_zip", True, path=str(output_zip), summary=f"Exported {output_zip.name}")


TOOL_HANDLERS: dict[str, ToolHandler] = {
    "fs.read_file": read_file,
    "fs.write_file": write_file,
    "fs.append_file": append_file,
    "fs.list_dir": list_dir,
    "fs.make_dir": make_dir,
    "fs.read_json": read_json,
    "fs.write_json": write_json,
    "dice.roll": roll_dice,
    "shell.run": run_shell,
    "web.search": web_search,
    "web.open": web_open,
    "browser.screenshot": browser_screenshot,
    "state.get": state_get,
    "state.patch": state_patch,
    "campaign.create_checkpoint": create_checkpoint,
    "campaign.export_zip": export_zip,
}


def execute_tool(name: str, args: dict[str, Any], campaign_root: Path, config: QuestConverseConfig) -> dict[str, Any]:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return _result(name, False, error=f"Unknown tool: {name}")
    try:
        return handler(args, campaign_root, config)
    except Exception as exc:  # noqa: BLE001
        return _result(name, False, error=str(exc))
