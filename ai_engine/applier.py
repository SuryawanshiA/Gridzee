"""Apply a generate or heal proposal to the project, after confirmation.

Shows the files and a diff summary, re-checks every path against the stage's
allowed folders, blocks proposals with syntax errors, and asks before writing.
Optionally creates a git branch first, so the change can be reviewed as a pull request.
"""

import re
import subprocess
from pathlib import Path

from ai_engine.settings import GENERATOR_ALLOWED, HEALER_ALLOWED, ROOT
from ai_engine.workspace import check_path, confirm, read_json, write_json

_ALLOWED = {"generate": GENERATOR_ALLOWED, "heal": HEALER_ALLOWED}


def apply(proposal_dir: Path, branch: str | None = None) -> list[str]:
    manifest = read_json(proposal_dir / "manifest.json")
    if manifest.get("applied"):
        raise ValueError("This proposal was already applied.")
    if manifest["syntax_errors"]:
        raise ValueError("Proposal has syntax errors; it cannot be applied:\n" + "\n".join(manifest["syntax_errors"]))
    allowed = _ALLOWED[manifest["kind"]]

    diff = (proposal_dir / "proposal.diff").read_text(encoding="utf-8")
    added = sum(1 for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff.splitlines() if line.startswith("-") and not line.startswith("---"))
    print(f"\n{manifest['kind']} proposal: {proposal_dir}")
    for entry in manifest["files"]:
        print(f"  {entry['status']:9} {entry['path']}")
    if manifest.get("markers"):
        print("  markers   " + ", ".join(m["name"] for m in manifest["markers"]))
    print(f"  diff: +{added} / -{removed} lines (full diff: {proposal_dir / 'proposal.diff'})")

    if not confirm("Apply these changes to the project?"):
        print("Not applied.")
        return []

    if branch:
        subprocess.run(["git", "checkout", "-b", branch], cwd=ROOT, check=True)

    written = []
    for entry in manifest["files"]:
        relative = check_path(entry["path"], allowed)
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        _ensure_packages(target)
        target.write_text((proposal_dir / "files" / relative).read_text(encoding="utf-8"), encoding="utf-8")
        written.append(relative)

    for marker in manifest.get("markers", []):
        _add_marker(marker["name"], marker.get("description", ""))

    manifest["applied"] = True
    write_json(proposal_dir / "manifest.json", manifest)
    print(f"Applied {len(written)} file(s).")
    return written


def _ensure_packages(target: Path) -> None:
    """Python folders under src/ need __init__.py to be importable."""
    src = ROOT / "src" / "gridzee_qa"
    if src not in target.parents:
        return
    folder = target.parent
    while folder != src:
        init = folder / "__init__.py"
        if not init.exists():
            init.write_text("", encoding="utf-8")
        folder = folder.parent


def _add_marker(name: str, description: str) -> None:
    if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
        raise ValueError(f"Invalid marker name: {name}")
    ini = ROOT / "pytest.ini"
    text = ini.read_text(encoding="utf-8")
    if re.search(rf"^\s+{name}:", text, re.MULTILINE):
        return
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "markers =")
    end = start + 1
    while end < len(lines) and lines[end].startswith((" ", "\t")) and lines[end].strip():
        end += 1
    lines.insert(end, f"    {name}: {description}".rstrip())
    ini.write_text("\n".join(lines) + "\n", encoding="utf-8")
