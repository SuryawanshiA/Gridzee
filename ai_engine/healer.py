"""Stage 5, heal: propose fixes for tests that failed on every attempt.

For each failed test the AI receives the sanitized failure text, the test file,
the framework files it imports, and the latest exploration snapshot of the
feature (to compare locators with the live page). It must first classify the
cause. Only locator and timing problems in page objects or components may be
changed. Tests, assertions and expected values are never changed. A suspected
application bug is reported, not "fixed".

Output: ai_workspace/heal/<run id>/<heal id>/ (heal.md, proposal.diff, manifest.json)
"""

import json
import re
from pathlib import Path

from ai_engine import llm
from ai_engine.sanitizer import mask_text, sanitize
from ai_engine.settings import EXPLORATION_DIR, HEAL_DIR, HEALER_ALLOWED, MAX_CONTEXT_CHARS, ROOT, RUNS_DIR
from ai_engine.workspace import new_id, read_json, write_proposal

_IMPORT = re.compile(r"^\s*from\s+(gridzee_qa(?:\.\w+)+)\s+import", re.MULTILINE)


def _module_file(module: str) -> str | None:
    path = ROOT / "src" / Path(*module.split("."))
    for candidate in (path.with_suffix(".py"), path / "__init__.py"):
        if candidate.is_file():
            return str(candidate.relative_to(ROOT)).replace("\\", "/")
    return None


def _related_files(test_file: str) -> list[str]:
    """The test file, the conftest files above it, and gridzee_qa modules they import (two levels)."""
    files = [test_file]
    folder = (ROOT / test_file).parent
    while folder != ROOT and ROOT in folder.parents:
        conftest = folder / "conftest.py"
        if conftest.is_file():
            files.append(str(conftest.relative_to(ROOT)).replace("\\", "/"))
        folder = folder.parent
    for _ in range(2):
        for relative in list(files):
            text = (ROOT / relative).read_text(encoding="utf-8")
            for module in _IMPORT.findall(text):
                if (found := _module_file(module)) and found not in files:
                    files.append(found)
    return files


def _latest_snapshot(test_file: str) -> dict | None:
    """Match tests/ui/<slug>/... to ai_workspace/exploration/<slug>/<latest>/snapshot.json."""
    parts = Path(test_file).parts
    if len(parts) < 3 or parts[:2] != ("tests", "ui"):
        return None
    folder = EXPLORATION_DIR / Path(*parts[2:-1])
    snapshots = sorted(folder.glob("*/snapshot.json")) if folder.is_dir() else []
    return sanitize(read_json(snapshots[-1])) if snapshots else None


def heal(run_id: str, only: list[str] | None = None) -> Path:
    summary = read_json(RUNS_DIR / run_id / "summary.json")
    failed = {n: t for n, t in summary["tests"].items() if t["label"] == "failed" and (not only or n in only)}
    if not failed:
        raise ValueError(f"Run {run_id} has no tests that failed on every attempt.")

    by_file: dict[str, list[str]] = {}
    for node_id in failed:
        by_file.setdefault(node_id.split("::", 1)[0], []).append(node_id)

    sections, files, snapshots = [], ["docs/conventions.md"], {}
    for test_file, node_ids in by_file.items():
        files += _related_files(test_file)
        if (snap := _latest_snapshot(test_file)) is not None:
            snapshots[test_file] = snap
        for node_id in node_ids:
            sections.append(f"--- FAILED: {node_id}\n{mask_text(failed[node_id]['last_failure'])}")

    budget, used, context = MAX_CONTEXT_CHARS, 0, []
    for relative in dict.fromkeys(files):
        block = f"\n===== FILE: {relative} =====\n{(ROOT / relative).read_text(encoding='utf-8')}"
        if used + len(block) <= budget:
            context.append(block)
            used += len(block)

    system = llm.load_prompt("healer", allowed=", ".join(HEALER_ALLOWED))
    user = (
        "Failures (sanitized):\n" + "\n\n".join(sections)
        + f"\n\nLatest exploration snapshots (sanitized):\n{json.dumps(snapshots, ensure_ascii=False)}"
        + "\n\nProject files:" + "".join(context)
    )
    result = llm.complete_json(system, user)

    directory = HEAL_DIR / run_id / new_id("heal")
    manifest = write_proposal(
        directory,
        kind="heal",
        files=result.get("files", []),
        allowed=HEALER_ALLOWED,
        extra={"run_id": run_id, "tests": list(failed), "diagnoses": result.get("diagnoses", [])},
    )
    (directory / "heal.md").write_text(_report(manifest), encoding="utf-8")
    return directory


def _report(manifest: dict) -> str:
    lines = [f"# Heal proposal for {manifest['run_id']}", "", "| Test | Cause | Diagnosis |", "|---|---|---|"]
    for d in manifest["diagnoses"]:
        lines.append(f"| `{d.get('test', '')}` | {d.get('cause', '')} | {d.get('diagnosis', '').replace('|', '/')} |")
    bugs = [d for d in manifest["diagnoses"] if d.get("cause") == "app-bug"]
    if bugs:
        lines += ["", "## Possible application defects (no code change proposed)", *[f"- `{d['test']}`: {d.get('diagnosis', '')}" for d in bugs]]
    lines += ["", "## Files", *([f"- {f['status']}: `{f['path']}`" for f in manifest["files"]] or ["- none"])]
    if manifest["syntax_errors"]:
        lines += ["", "## Syntax errors (apply is blocked)", *[f"- {e}" for e in manifest["syntax_errors"]]]
    lines += ["", "Review `proposal.diff`, then run `python -m ai_engine apply <this folder>`, then re-run the tests."]
    return "\n".join(lines) + "\n"
