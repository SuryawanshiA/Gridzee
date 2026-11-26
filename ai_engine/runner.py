"""Stage 4, run: execute tests, then re-run only the failed ones, up to 3 times.

Every re-run asks for confirmation first, unless ``confirm_retries`` is set
(for CI). Results per test:
    passed   passed on the first attempt
    flaky    failed first, passed on a retry (listed for review, not counted as a plain pass)
    failed   failed on every attempt
    skipped  skipped

Output: ai_workspace/runs/<run id>/attempt-<n>.xml, summary.json, summary.md
"""

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from ai_engine.settings import MAX_RETRIES, ROOT, RUNS_DIR
from ai_engine.workspace import confirm, new_id, write_json


def _pytest_command(options: list[str], targets: list[str], junit: Path) -> list[str]:
    return [
        sys.executable, "-m", "pytest", *targets, *options,
        "-o", "junit_family=xunit1",  # adds the file attribute, needed to rebuild node ids
        f"--junitxml={junit}",
    ]


def parse_junit(path: Path) -> dict[str, dict[str, str]]:
    """Map pytest node id to outcome and failure text."""
    results: dict[str, dict[str, str]] = {}
    if not path.is_file():
        return results
    for case in ET.parse(path).getroot().iter("testcase"):
        file = (case.get("file") or "").replace("\\", "/")
        classname = case.get("classname", "")
        last = classname.rsplit(".", 1)[-1]
        prefix = f"{file}::{last}::" if last.startswith("Test") else f"{file}::"
        node_id = prefix + case.get("name", "")
        outcome, detail = "passed", ""
        for tag in ("failure", "error", "skipped"):
            element = case.find(tag)
            if element is not None:
                outcome = "failed" if tag in ("failure", "error") else "skipped"
                detail = f"{element.get('message', '')}\n{element.text or ''}".strip()
                break
        results[node_id] = {"outcome": outcome, "detail": detail[:8000]}
    return results


def run(
    targets: list[str],
    marker: str | None = None,
    env: str | None = None,
    browsers: list[str] | None = None,
    headed: bool = False,
    max_retries: int = MAX_RETRIES,
    confirm_retries: bool = False,
) -> Path:
    max_retries = min(max_retries, MAX_RETRIES)
    run_dir = RUNS_DIR / new_id("run")
    run_dir.mkdir(parents=True, exist_ok=True)

    options: list[str] = []
    if marker:
        options += ["-m", marker]
    if env:
        options += ["--env", env]
    for browser in browsers or []:
        options += ["--browser", browser]
    if headed:
        options.append("--headed")

    history: dict[str, list[str]] = {}
    details: dict[str, str] = {}

    def attempt(number: int, selection: list[str], extra: list[str]) -> list[str]:
        junit = run_dir / f"attempt-{number}.xml"
        command = _pytest_command(extra, selection, junit)
        print(f"\n=== Attempt {number}: {' '.join(command[3:])}\n", flush=True)
        subprocess.run(command, cwd=ROOT, check=False)
        results = parse_junit(junit)
        for node_id, result in results.items():
            history.setdefault(node_id, []).append(result["outcome"])
            if result["outcome"] == "failed":
                details[node_id] = result["detail"]
        return [n for n, r in results.items() if r["outcome"] == "failed"]

    failed = attempt(0, targets or ["tests"], options)
    for number in range(1, max_retries + 1):
        if not failed:
            break
        print(f"\n{len(failed)} test(s) failed:", *[f"  - {n}" for n in failed], sep="\n")
        if not confirm_retries and not confirm(f"Re-run the failed tests (retry {number} of {max_retries})?"):
            print("Retry declined.")
            break
        # Marker filter is not needed for explicit node ids; browser and env options are.
        rerun_options = [o for i, o in enumerate(options) if o != "-m" and (i == 0 or options[i - 1] != "-m")]
        failed = attempt(number, failed, rerun_options)

    summary = _summarize(history, details)
    write_json(run_dir / "summary.json", summary)
    (run_dir / "summary.md").write_text(_markdown(run_dir.name, summary), encoding="utf-8")
    print(f"\nRun summary: {run_dir / 'summary.md'}")
    return run_dir


def _label(outcomes: list[str]) -> str:
    if outcomes[0] == "skipped":
        return "skipped"
    if outcomes[0] == "passed":
        return "passed"
    return "flaky" if "passed" in outcomes[1:] else "failed"


def _summarize(history: dict[str, list[str]], details: dict[str, str]) -> dict[str, Any]:
    tests = {n: {"label": _label(o), "attempts": o, "last_failure": details.get(n, "")} for n, o in history.items()}
    counts = {label: sum(1 for t in tests.values() if t["label"] == label) for label in ("passed", "flaky", "failed", "skipped")}
    return {"counts": counts, "tests": tests}


def _markdown(run_id: str, summary: dict[str, Any]) -> str:
    c = summary["counts"]
    lines = [
        f"# Run {run_id}", "",
        f"Passed {c['passed']} | Flaky {c['flaky']} | Failed {c['failed']} | Skipped {c['skipped']}", "",
        "Flaky tests failed at least once and then passed. Review them; they are not plain passes.", "",
        "| Test | Result | Attempts |", "|---|---|---|",
    ]
    order = {"failed": 0, "flaky": 1, "passed": 2, "skipped": 3}
    for node_id, test in sorted(summary["tests"].items(), key=lambda kv: (order[kv[1]["label"]], kv[0])):
        lines.append(f"| `{node_id}` | {test['label']} | {' > '.join(test['attempts'])} |")
    if c["failed"]:
        lines += ["", f"To propose fixes for the failed tests: `python -m ai_engine heal {run_id}`"]
    return "\n".join(lines) + "\n"
