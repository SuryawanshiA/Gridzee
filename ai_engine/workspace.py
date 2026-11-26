"""Shared helpers: ids, JSON files, navigation slugs, path checks, proposals and diffs."""

import difflib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_engine.settings import ALWAYS_BLOCKED, ROOT


def new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now():%Y%m%d-%H%M%S}"


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def parse_navigation(text: str) -> list[str]:
    """``"Settings > General > Users > Admin"`` or with ``-->`` becomes a list of menu labels."""
    parts = [p.strip() for p in re.split(r"-*>+", text) if p.strip()]
    if not parts:
        raise ValueError(f"No menu path in '{text}'.")
    return parts


def slug(navigation: list[str]) -> str:
    """``["Settings", "General", "Users", "Admin"]`` becomes ``settings/general/users/admin``."""
    return "/".join(re.sub(r"[^a-z0-9]+", "_", part.lower()).strip("_") for part in navigation)


def check_path(relative: str, allowed: tuple[str, ...]) -> str:
    """Return a normalized relative path, or raise if it is outside ``allowed``."""
    normalized = relative.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    target = (ROOT / normalized).resolve()
    if ROOT.resolve() not in target.parents:
        raise ValueError(f"Path leaves the project: {relative}")
    if ".." in Path(normalized).parts:
        raise ValueError(f"Path contains '..': {relative}")
    if any(normalized == b or normalized.startswith(b) for b in ALWAYS_BLOCKED):
        raise ValueError(f"Path is never writable by the AI engine: {relative}")
    if not normalized.startswith(allowed):
        raise ValueError(f"Path not allowed for this stage: {relative}. Allowed: {', '.join(allowed)}")
    return normalized


def unified_diff(relative: str, new_content: str) -> str:
    current = ROOT / relative
    old = current.read_text(encoding="utf-8").splitlines(keepends=True) if current.is_file() else []
    return "".join(
        difflib.unified_diff(old, new_content.splitlines(keepends=True), fromfile=f"a/{relative}", tofile=f"b/{relative}")
    )


def syntax_errors(relative: str, content: str) -> str | None:
    """Compile Python source without running it. Return the error, or None."""
    if not relative.endswith(".py"):
        return None
    try:
        compile(content, relative, "exec")
    except SyntaxError as error:
        return f"{relative}:{error.lineno}: {error.msg}"
    return None


def write_proposal(directory: Path, kind: str, files: list[dict[str, str]], allowed: tuple[str, ...], extra: dict[str, Any]) -> dict[str, Any]:
    """Store proposed files, a combined diff and a manifest. Nothing in the project is changed."""
    directory.mkdir(parents=True, exist_ok=True)
    entries, diffs, errors = [], [], []
    for item in files:
        relative = check_path(item["path"], allowed)
        content = item["content"]
        if not content.endswith("\n"):
            content += "\n"
        stored = directory / "files" / relative
        stored.parent.mkdir(parents=True, exist_ok=True)
        stored.write_text(content, encoding="utf-8")
        entries.append({"path": relative, "status": "modified" if (ROOT / relative).is_file() else "new"})
        diffs.append(unified_diff(relative, content))
        if error := syntax_errors(relative, content):
            errors.append(error)
    (directory / "proposal.diff").write_text("".join(diffs), encoding="utf-8")
    manifest = {"kind": kind, "files": entries, "syntax_errors": errors, "applied": False, **extra}
    write_json(directory / "manifest.json", manifest)
    return manifest


def confirm(question: str) -> bool:
    """Ask a yes/no question on the terminal. Anything but y/yes means no."""
    try:
        answer = input(f"{question} [y/N]: ")
    except EOFError:
        return False
    return answer.strip().lower() in {"y", "yes"}
