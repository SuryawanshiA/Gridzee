# AI Workflow: explore, plan, generate, run, heal

The AI engine (`ai_engine/`) automates the repetitive parts of test creation. A person approves every step that changes code or data.

```
explore -> plan -> [approve] -> generate -> [apply] -> run -> [confirm each retry, max 3] -> heal -> [apply] -> run
```

| Stage | Command | Changes the project? | Your gate |
|---|---|---|---|
| Explore | `explore` | No. Read-only browser session | |
| Plan | `plan` | No. Writes `ai_workspace/plans/<id>/` | Review `plan.md`, then `approve` |
| Generate | `generate` | No. Writes a proposal in `ai_workspace/generated/` | Review the diff, then `apply` |
| Apply | `apply` | **Yes**, after you type `y` | Confirmation prompt, optional git branch |
| Run | `run` | No code. Tests may create data | Confirms before each retry |
| Heal | `heal` | No. Writes a proposal in `ai_workspace/heal/` | Review the diff, then `apply` |

## One-time setup
```powershell
.venv\Scripts\activate
pip install -r ai_engine/requirements.txt
```
Then add to `.env` (see `.env.example`):
```
AI_PROVIDER=anthropic          # or bedrock / bedrock-runtime
AI_MODEL=<current Claude model name>
ANTHROPIC_API_KEY=<your key>   # for anthropic; Bedrock uses your AWS credentials
```

## Worked example: a new screen
```powershell
# 1. Explore (read-only). Opens the screen, clicks New (+), visits two tabs.
python -m ai_engine explore --nav "Settings > General > Users > Admin" --open-new --tabs "My Account,Data Access"

# 2. Plan. Pass your business rules in --notes.
python -m ai_engine plan ai_workspace/exploration/settings/general/users/admin/<id>/snapshot.json --id-prefix ADM `
    --notes "To add admin click (+), fill the mandatory fields, save, and verify on the overview using the bottom search."

# 3. Review ai_workspace/plans/<plan id>/plan.md, then approve
python -m ai_engine approve <plan id> --ids ADM-001,ADM-070     # or --all; --reject to reject

# 4. Generate a proposal for the approved scenarios
python -m ai_engine generate <plan id>

# 5. Review the proposal's README.md and proposal.diff, then apply (asks y/N)
python -m ai_engine apply ai_workspace/generated/<plan id>/<gen id> --branch ai/admin

# 6. Run. Each retry of failed tests asks first. Up to 3 retries.
python -m ai_engine run tests/ui/settings/general/users/admin -m "not creates_data"

# 7. Heal the tests that failed on every attempt, review, apply, run again
python -m ai_engine heal <run id>
python -m ai_engine apply ai_workspace/heal/<run id>/<heal id>

# Overview of everything
python -m ai_engine status
```

## Run results
`ai_workspace/runs/<run id>/summary.md` labels every test:

| Label | Meaning |
|---|---|
| passed | Passed on the first attempt |
| flaky | Failed, then passed on a retry. Listed for review, not counted as a plain pass |
| failed | Failed on every attempt. Input for `heal` |
| skipped | Skipped |

The HTML and Allure reports from `pytest.ini` are still written to `reports/` on every attempt.

## Safety rules built into the engine
- **Sanitizing:** before any AI call, `.env` secrets, emails, long numbers, tokens, password inputs and grid password columns are masked (`ai_engine/sanitizer.py`).
- **Read-only exploration:** the explorer never clicks Save or Delete, and dismisses browser confirmations.
- **Write limits:** generate may write only under `pages/`, `flows/`, `components/`, `factories/`, `tests/ui/`, `data/`, `docs/test-cases/`. Heal may write only under `pages/` and `components/`. `tests/conftest.py`, `.env` and `.auth/` are never written. Paths are checked when the proposal is created and again when it is applied.
- **No weakened tests:** heal never changes tests, assertions or expected values. A suspected application bug is reported, not patched.
- **Syntax check:** proposals with Python syntax errors cannot be applied. Code is compiled, not run.
- **Retries:** at most 3, each confirmed. `--confirm-retries` pre-approves them, for CI.
- **One-way dependency:** `ai_engine` imports the framework; the framework never imports `ai_engine`.

## Files
| Location | Purpose |
|---|---|
| `ai_engine/cli.py`, `__main__.py` | Commands (`python -m ai_engine ...`) |
| `ai_engine/settings.py` | Paths, AI settings, write limits |
| `ai_engine/llm.py` | Claude client (Anthropic API or Bedrock), JSON replies |
| `ai_engine/sanitizer.py` | Masking before AI calls |
| `ai_engine/explorer.py` | Stage 1 |
| `ai_engine/planner.py` | Stage 2 and approvals |
| `ai_engine/generator.py` | Stage 3 |
| `ai_engine/applier.py` | Applies proposals after confirmation |
| `ai_engine/runner.py` | Stage 4 with retries and labels |
| `ai_engine/healer.py` | Stage 5 |
| `ai_engine/prompts/*.md` | Instructions sent to the AI for plan, generate and heal |
| `ai_workspace/plans/` | Plans (committed to git) |
| `ai_workspace/exploration/`, `generated/`, `heal/`, `runs/` | Working files (git-ignored) |
