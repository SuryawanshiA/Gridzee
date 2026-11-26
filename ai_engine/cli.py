"""Command line for the AI engine. Run from the project root with the virtual environment active.

    python -m ai_engine explore  --nav "Settings > General > Users > Admin" [--open-new] [--tabs "My Account,Data Access"]
    python -m ai_engine plan     <snapshot.json> --id-prefix ADM [--notes "what to cover"]
    python -m ai_engine approve  <plan id> (--ids ADM-001,ADM-002 | --all) [--reject]
    python -m ai_engine generate <plan id>
    python -m ai_engine apply    <proposal folder> [--branch ai/<name>]
    python -m ai_engine run      [targets...] [-m MARKER] [--env qa] [--browser chromium] [--headed] [--retries 3] [--confirm-retries]
    python -m ai_engine heal     <run id> [--tests NODEID ...]
    python -m ai_engine status

Approval gates: plan -> approve -> generate -> apply; run asks before each retry; heal -> apply.
"""

import argparse
from pathlib import Path

from ai_engine import settings


def _explore(args: argparse.Namespace) -> None:
    from ai_engine.explorer import explore
    from ai_engine.workspace import parse_navigation

    tabs = [t.strip() for t in args.tabs.split(",")] if args.tabs else None
    path = explore(parse_navigation(args.nav), env=args.env, role=args.role, open_new=args.open_new, tabs=tabs, headed=args.headed)
    print(f"Snapshot: {path}\nNext: python -m ai_engine plan \"{path}\" --id-prefix <PREFIX>")


def _plan(args: argparse.Namespace) -> None:
    from ai_engine.planner import create_plan

    directory = create_plan(Path(args.snapshot), args.id_prefix, args.notes or "")
    print(f"Plan: {directory / 'plan.md'}\nReview it, then: python -m ai_engine approve {directory.name} --ids ... | --all")


def _approve(args: argparse.Namespace) -> None:
    from ai_engine.planner import set_status

    if not args.all and not args.ids:
        raise SystemExit("Give --ids ID1,ID2 or --all.")
    ids = None if args.all else [i.strip() for i in args.ids.split(",") if i.strip()]
    changed = set_status(args.plan_id, ids, "rejected" if args.reject else "approved")
    print(f"{'Rejected' if args.reject else 'Approved'}: {', '.join(changed)}")


def _generate(args: argparse.Namespace) -> None:
    from ai_engine.generator import generate

    directory = generate(args.plan_id)
    print(f"Proposal: {directory}\nReview README.md and proposal.diff, then: python -m ai_engine apply \"{directory}\"")


def _apply(args: argparse.Namespace) -> None:
    from ai_engine.applier import apply

    apply(Path(args.proposal), branch=args.branch)


def _run(args: argparse.Namespace) -> None:
    from ai_engine.runner import run

    run(args.targets, marker=args.marker, env=args.env, browsers=args.browser, headed=args.headed,
        max_retries=args.retries, confirm_retries=args.confirm_retries)


def _heal(args: argparse.Namespace) -> None:
    from ai_engine.healer import heal

    directory = heal(args.run_id, only=args.tests)
    print(f"Heal proposal: {directory / 'heal.md'}\nReview it, then: python -m ai_engine apply \"{directory}\"")


def _status(_: argparse.Namespace) -> None:
    from ai_engine.workspace import read_json

    print("Plans:")
    for plan in sorted(settings.PLANS_DIR.glob("*/plan.json")):
        data = read_json(plan)
        statuses = [s.get("status") for s in data.get("scenarios", [])]
        print(f"  {plan.parent.name}: {' > '.join(data.get('navigation', []))} | "
              + ", ".join(f"{s} {statuses.count(s)}" for s in ("proposed", "approved", "rejected")))
    print("Proposals:")
    for manifest in sorted([*settings.GENERATED_DIR.glob("*/*/manifest.json"), *settings.HEAL_DIR.glob("*/*/manifest.json")]):
        data = read_json(manifest)
        print(f"  {manifest.parent}: {data['kind']}, {len(data['files'])} file(s), applied={data['applied']}")
    print("Runs:")
    for summary in sorted(settings.RUNS_DIR.glob("*/summary.json")):
        counts = read_json(summary)["counts"]
        print(f"  {summary.parent.name}: " + ", ".join(f"{k} {v}" for k, v in counts.items()))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m ai_engine", description="AI-assisted test automation with approval gates.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("explore", help="Log in, follow a menu path and record the screen (read-only).")
    p.add_argument("--nav", required=True, help='Menu path, for example "Settings > General > Users > Admin".')
    p.add_argument("--env", help="qa or demo (default: ENV variable, then qa).")
    p.add_argument("--role", default="superadmin", help="Role from config/<env>.yaml used to log in.")
    p.add_argument("--open-new", action="store_true", help="Also click New (+) and record the empty form.")
    p.add_argument("--tabs", help="Comma-separated tab names to visit on the form.")
    p.add_argument("--headed", action="store_true", help="Show the browser.")
    p.set_defaults(func=_explore)

    p = sub.add_parser("plan", help="Propose test scenarios from a snapshot.")
    p.add_argument("snapshot", help="Path to snapshot.json from explore.")
    p.add_argument("--id-prefix", required=True, help="Scenario id prefix, for example ADM.")
    p.add_argument("--notes", help="Your instructions: what to cover, business rules, how to verify.")
    p.set_defaults(func=_plan)

    p = sub.add_parser("approve", help="Approve or reject scenarios of a plan.")
    p.add_argument("plan_id")
    p.add_argument("--ids", help="Comma-separated scenario ids.")
    p.add_argument("--all", action="store_true", help="Apply to every scenario.")
    p.add_argument("--reject", action="store_true", help="Reject instead of approve.")
    p.set_defaults(func=_approve)

    p = sub.add_parser("generate", help="Generate code for approved scenarios (as a proposal).")
    p.add_argument("plan_id")
    p.set_defaults(func=_generate)

    p = sub.add_parser("apply", help="Apply a generate or heal proposal after confirmation.")
    p.add_argument("proposal", help="Proposal folder printed by generate or heal.")
    p.add_argument("--branch", help="Create this git branch before applying.")
    p.set_defaults(func=_apply)

    p = sub.add_parser("run", help="Run tests; re-run failed ones up to 3 times after confirmation.")
    p.add_argument("targets", nargs="*", help="Test paths or node ids (default: tests).")
    p.add_argument("-m", "--marker", help='Marker expression, for example "admin and not creates_data".')
    p.add_argument("--env", help="qa or demo.")
    p.add_argument("--browser", action="append", choices=["chromium", "firefox", "webkit"], help="Repeat for several browsers.")
    p.add_argument("--headed", action="store_true", help="Show the browser.")
    p.add_argument("--retries", type=int, default=settings.MAX_RETRIES, help="Max retries (at most 3).")
    p.add_argument("--confirm-retries", action="store_true", help="Pre-approve all retries (for CI).")
    p.set_defaults(func=_run)

    p = sub.add_parser("heal", help="Propose fixes for tests that failed on every attempt.")
    p.add_argument("run_id")
    p.add_argument("--tests", nargs="*", help="Limit to these node ids.")
    p.set_defaults(func=_heal)

    p = sub.add_parser("status", help="List plans, proposals and runs.")
    p.set_defaults(func=_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.func(args)
    return 0
