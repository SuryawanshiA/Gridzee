"""Stage 3, generate: write page objects, flow, data and tests for approved scenarios.

Only scenarios with status ``approved`` are sent. The AI receives the framework
rules (README), the shared code it must reuse, existing code for the same
navigation folder, and a reference feature as a style example.

The result is a proposal. Nothing in the project changes until ``apply``.
Output: ai_workspace/generated/<plan id>/<generation id>/ (files, proposal.diff, manifest.json)
"""

import json
from pathlib import Path

from ai_engine import llm
from ai_engine.planner import load_plan
from ai_engine.settings import GENERATED_DIR, GENERATOR_ALLOWED, MAX_CONTEXT_CHARS, ROOT
from ai_engine.workspace import new_id, slug, write_proposal

# Shared code every generated feature must reuse.
SHARED_FILES = [
    "docs/conventions.md",
    "README.md",
    "pytest.ini",
    "config/base.yaml",
    "src/gridzee_qa/core/base_page.py",
    "src/gridzee_qa/core/base_component.py",
    "src/gridzee_qa/core/config_loader.py",
    "src/gridzee_qa/components/side_menu.py",
    "src/gridzee_qa/components/bottom_toolbar.py",
    "src/gridzee_qa/components/message_box.py",
    "src/gridzee_qa/flows/auth_flow.py",
    "src/gridzee_qa/utils/credential_store.py",
    "src/gridzee_qa/utils/data_generator.py",
    "tests/conftest.py",
    "tests/ui/conftest.py",
]

# A finished feature used as the style reference.
REFERENCE_FILES = [
    "src/gridzee_qa/pages/settings/general/users/admin/admin_overview_page.py",
    "src/gridzee_qa/pages/settings/general/users/admin/admin_form_page.py",
    "src/gridzee_qa/flows/settings/general/users/admin_flow.py",
    "src/gridzee_qa/factories/admin_factory.py",
    "tests/ui/settings/general/users/admin/conftest.py",
    "tests/ui/settings/general/users/admin/test_admin_validation.py",
    "tests/ui/settings/general/users/admin/test_admin_create.py",
]


def _feature_files(feature_slug: str) -> list[str]:
    parent = feature_slug.rsplit("/", 1)[0] if "/" in feature_slug else ""
    roots = [
        ROOT / "src/gridzee_qa/pages" / feature_slug,
        ROOT / "tests/ui" / feature_slug,
        ROOT / "data" / feature_slug,
    ]
    found = [p for r in roots if r.is_dir() for p in r.rglob("*") if p.suffix in {".py", ".json", ".yaml"}]
    flow_dir = ROOT / "src/gridzee_qa/flows" / parent
    if flow_dir.is_dir():
        found += [p for p in flow_dir.glob("*_flow.py")]
    return sorted({str(p.relative_to(ROOT)).replace("\\", "/") for p in found})


def _context(paths: list[str], budget: int) -> tuple[str, list[str]]:
    """Concatenate files until the character budget runs out. Returns text and skipped paths."""
    parts, skipped, used = [], [], 0
    for relative in dict.fromkeys(paths):
        file = ROOT / relative
        if not file.is_file():
            continue
        text = file.read_text(encoding="utf-8")
        block = f"\n===== FILE: {relative} =====\n{text}"
        if used + len(block) > budget:
            skipped.append(relative)
            continue
        parts.append(block)
        used += len(block)
    return "".join(parts), skipped


def generate(plan_id: str) -> Path:
    _, plan = load_plan(plan_id)
    approved = [s for s in plan["scenarios"] if s.get("status") == "approved"]
    if not approved:
        raise ValueError(f"Plan {plan_id} has no approved scenarios. Approve some first.")

    feature_slug = slug(plan["navigation"])
    feature_files = _feature_files(feature_slug)
    context, skipped = _context(SHARED_FILES + feature_files + REFERENCE_FILES, MAX_CONTEXT_CHARS)

    system = llm.load_prompt(
        "generator",
        navigation=" > ".join(plan["navigation"]),
        slug=feature_slug,
        allowed=", ".join(GENERATOR_ALLOWED),
    )
    user = (
        f"Approved scenarios (JSON):\n{json.dumps(approved, ensure_ascii=False, indent=1)}\n\n"
        f"Tester notes: {plan.get('notes') or '(none)'}\n\n"
        f"Existing files for this feature: {', '.join(feature_files) or '(none)'}\n\n"
        f"Project files:{context}"
    )
    result = llm.complete_json(system, user)

    directory = GENERATED_DIR / plan_id / new_id("gen")
    manifest = write_proposal(
        directory,
        kind="generate",
        files=result.get("files", []),
        allowed=GENERATOR_ALLOWED,
        extra={
            "plan_id": plan_id,
            "scenarios": [s["id"] for s in approved],
            "markers": result.get("markers", []),
            "notes": result.get("notes", ""),
            "context_skipped": skipped,
        },
    )
    (directory / "README.md").write_text(_summary(manifest), encoding="utf-8")
    return directory


def _summary(manifest: dict) -> str:
    lines = [f"# Generated proposal for {manifest['plan_id']}", "", f"Scenarios: {', '.join(manifest['scenarios'])}", "", "## Files"]
    lines += [f"- {f['status']}: `{f['path']}`" for f in manifest["files"]]
    if manifest["markers"]:
        lines += ["", "## Markers to add to pytest.ini", *[f"- `{m['name']}`: {m.get('description', '')}" for m in manifest["markers"]]]
    if manifest["syntax_errors"]:
        lines += ["", "## Syntax errors (apply is blocked)", *[f"- {e}" for e in manifest["syntax_errors"]]]
    if manifest["notes"]:
        lines += ["", "## Notes from the generator", manifest["notes"]]
    lines += ["", "Review `proposal.diff`, then run `python -m ai_engine apply <this folder>`."]
    return "\n".join(lines) + "\n"
