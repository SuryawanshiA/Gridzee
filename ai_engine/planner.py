"""Stage 2, plan: turn an exploration snapshot into proposed test scenarios.

The snapshot is sanitized before it is sent. The plan is saved as JSON (the
source of truth) and Markdown (for reading). Every scenario starts as
``proposed``. Nothing is generated until scenarios are ``approved``.

Output: ai_workspace/plans/<plan id>/plan.json and plan.md
"""

import json
from pathlib import Path
from typing import Any

from ai_engine import llm
from ai_engine.sanitizer import sanitize
from ai_engine.settings import PLANS_DIR
from ai_engine.workspace import new_id, read_json, write_json

STATUSES = ("proposed", "approved", "rejected")


def create_plan(snapshot_path: Path, id_prefix: str, notes: str = "") -> Path:
    snapshot = sanitize(read_json(snapshot_path))
    system = llm.load_prompt("planner")
    user = (
        f"ID prefix for scenarios: {id_prefix}\n\n"
        f"Instructions from the tester:\n{notes or '(none)'}\n\n"
        f"Exploration snapshot (JSON, sanitized):\n{json.dumps(snapshot, ensure_ascii=False)}"
    )
    plan = llm.complete_json(system, user)

    plan_id = new_id("plan")
    plan.update({
        "plan_id": plan_id,
        "navigation": snapshot["navigation"],
        "snapshot": str(snapshot_path),
        "notes": notes,
    })
    for scenario in plan.get("scenarios", []):
        scenario["status"] = "proposed"

    directory = PLANS_DIR / plan_id
    save_plan(directory, plan)
    return directory


def save_plan(directory: Path, plan: dict[str, Any]) -> None:
    write_json(directory / "plan.json", plan)
    (directory / "plan.md").write_text(render_markdown(plan), encoding="utf-8")


def load_plan(plan_id: str) -> tuple[Path, dict[str, Any]]:
    directory = PLANS_DIR / plan_id
    if not (directory / "plan.json").is_file():
        raise FileNotFoundError(f"No plan '{plan_id}' in {PLANS_DIR}")
    return directory, read_json(directory / "plan.json")


def set_status(plan_id: str, ids: list[str] | None, status: str) -> list[str]:
    """Set ``status`` on the given scenario ids, or on all when ``ids`` is None. Returns changed ids."""
    if status not in STATUSES:
        raise ValueError(f"Status must be one of {STATUSES}")
    directory, plan = load_plan(plan_id)
    known = {s["id"] for s in plan["scenarios"]}
    unknown = sorted(set(ids or []) - known)
    if unknown:
        raise ValueError(f"Unknown scenario ids: {', '.join(unknown)}")
    changed = []
    for scenario in plan["scenarios"]:
        if ids is None or scenario["id"] in ids:
            scenario["status"] = status
            changed.append(scenario["id"])
    save_plan(directory, plan)
    return changed


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        f"# Test plan {plan.get('plan_id', '')}: {' > '.join(plan.get('navigation', []))}",
        "",
        plan.get("summary", ""),
        "",
        "Review this plan. Approve with `python -m ai_engine approve <plan id> --ids ID1,ID2` or `--all`.",
        "You may also edit plan.json directly; plan.md is regenerated from it.",
        "",
    ]
    if plan.get("open_questions"):
        lines += ["## Open questions", *[f"- {q}" for q in plan["open_questions"]], ""]
    lines += ["## Scenarios", "", "| ID | Status | Pri | Group | Type | Title |", "|---|---|---|---|---|---|"]
    for s in plan.get("scenarios", []):
        lines.append(f"| {s['id']} | {s.get('status')} | {s.get('priority', '')} | {s.get('group', '')} | {s.get('type', '')} | {s.get('title', '')} |")
    lines.append("")
    for s in plan.get("scenarios", []):
        lines += [f"### {s['id']}: {s.get('title', '')}", ""]
        if s.get("preconditions"):
            lines += [f"**Preconditions:** {s['preconditions']}", ""]
        lines += ["**Steps**", *[f"{n}. {step}" for n, step in enumerate(s.get("steps", []), start=1)], ""]
        lines += [f"**Expected:** {s.get('expected', '')}", ""]
        if s.get("data"):
            lines += [f"**Data:** {s['data']}", ""]
    return "\n".join(lines)
