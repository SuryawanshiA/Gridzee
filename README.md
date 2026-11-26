# Gridzee QA Automation Framework

A test automation framework for the Gridzee (Trakzee) web application, built with **Python**, **Playwright** and **pytest**.

> **Status:** The folder structure, environment config and `.venv` are in place. The framework code is built in phases (see [Roadmap](#roadmap)). Code snippets in this file show the **pattern every file must follow**. Selectors in snippets are placeholders until the real pages are inspected.

---

## Table of contents
1. [What this framework does](#what-this-framework-does)
2. [Tech stack](#tech-stack)
3. [Design approach (hybrid)](#design-approach-hybrid)
4. [Folder structure](#folder-structure)
5. [How a test flows through the layers](#how-a-test-flows-through-the-layers)
6. [Where does my code go? (quick lookup)](#where-does-my-code-go-quick-lookup)
7. [Worked example: the login test, layer by layer](#worked-example-the-login-test-layer-by-layer)
8. [Setup](#setup)
9. [Running tests](#running-tests)
10. [Reports](#reports)
11. [Configuration and secrets](#configuration-and-secrets)
12. [AI-assisted test generation](#ai-assisted-test-generation)
13. [Rules for AI agents and contributors](#rules-for-ai-agents-and-contributors)
14. [Roadmap](#roadmap)

---

## What this framework does
- Runs automated **UI tests** and **API tests**.
- Runs on **Chromium, Firefox and WebKit** (cross-browser).
- Runs **headless by default**, with a switch to **headed**.
- Produces **HTML** and **Allure** reports on every run.
- Later phases add mobile, performance and load testing, and a CLI AI agent that explores the application and proposes tests for human approval.

**Environments**
| Name | Base URL | Login page |
|---|---|---|
| `qa` | https://qa.uffizio.com | `/jsp/trakzee_login.jsp` |
| `demo` | https://demo.uffizio.com | `/jsp/trakzee_login.jsp` |

`demo` is a shared site. Run only read-only checks and smoke tests there.

## Tech stack
| Purpose | Tool |
|---|---|
| Language | Python 3.12 |
| Browser automation | Playwright |
| Test runner | pytest, `pytest-playwright` |
| Parallel runs | `pytest-xdist` |
| Retries | `pytest-rerunfailures` |
| Reports | `pytest-html`, Allure |
| Config and data | YAML, JSON, `.env` |
| Code quality | ruff, black, mypy, pre-commit |
| Containers | Docker |
| Load testing (future) | Locust |
| Native mobile (future) | Appium |

## Design approach (hybrid)
| Approach | What it means | Where it lives |
|---|---|---|
| **Page Object Model (POM)** | Each page or UI part is a class that holds its locators and actions. A UI change is fixed in one place. | `src/gridzee_qa/pages`, `components` |
| **Data-driven** | Test data sits in files outside the code. One test runs against many data sets. | `data/` |
| **Keyword-driven** | Business actions such as `login_as("superadmin")` are reusable steps. Tests read like a list of steps. | `src/gridzee_qa/flows` |
| **API testing** | API clients are used for API tests and to create test data quickly. | `src/gridzee_qa/api`, `factories` |

## Folder structure
```
Gridzee/
├── .github/workflows/        CI pipelines (PR smoke run, nightly regression, lint)
├── config/                   Settings per environment
│   ├── base.yaml             Defaults for all environments
│   ├── qa.yaml               QA URL, login path, credential variable names
│   └── demo.yaml             Demo URL, login path, credential variable names
├── data/                     Static test data (JSON/YAML)
├── src/gridzee_qa/           The framework package
│   ├── core/                 Base classes, config loader, logger, exceptions
│   ├── pages/                Page objects (locators and page actions)
│   ├── components/           Reusable UI parts (header, modal, table)
│   ├── flows/                Business workflows built from pages (keyword layer)
│   ├── api/                  API clients, one per service area
│   ├── models/               Typed data models for payloads and users
│   ├── factories/            Create and clean up test data through the API
│   ├── mobile/               (future) Appium screens and drivers
│   └── utils/                Data reader, helpers, custom assertions
├── tests/
│   ├── conftest.py           Shared fixtures (browser, page, config, API clients)
│   ├── ui/                   UI tests
│   ├── api/                  API tests
│   ├── mobile/               (future)
│   └── performance/          (future)
├── load/                     (future) Locust load tests
├── ai_engine/                CLI AI agent: explore, plan, generate, run, retry
├── ai_workspace/             AI working files: exploration data, plans, run history
├── .auth/                    Saved login sessions (git-ignored)
├── reports/                  HTML and Allure output, screenshots, traces (git-ignored)
├── docs/                     Detailed documentation
├── .env                      Real credentials (git-ignored, local only)
├── .env.example              Template listing every required variable
├── Dockerfile                Same runtime locally and in CI
├── pytest.ini                Test paths, markers, default options
├── pyproject.toml            Dependencies and tool settings
└── requirements.txt          Pinned dependencies
```

## How a test flows through the layers
```
tests/ui/test_*.py   ->   flows/   ->   pages/ + components/   ->   core/base_page.py   ->   Playwright
                              |                  |
                       data from data/     settings from config/ and .env
```
**Rule:** a layer calls only the layer directly below it. A test never touches a locator. A page object never contains `assert` for test outcomes.

## Where does my code go? (quick lookup)
| I want to... | Put it in | Example file |
|---|---|---|
| Add a click, fill or wait helper used by all pages | `core/base_page.py` | `BasePage.click_and_wait()` |
| Describe a page's elements and actions | `pages/<page>_page.py` | `pages/login_page.py` |
| Describe a UI part used on many pages | `components/<part>.py` | `components/header.py` |
| Combine page actions into a business step | `flows/<area>_flow.py` | `flows/auth_flow.py` |
| Call a backend endpoint | `api/<area>_api.py` | `api/auth_api.py` |
| Define the shape of a payload or user | `models/<name>.py` | `models/user.py` |
| Create and delete data for a test | `factories/<name>_factory.py` | `factories/vehicle_factory.py` |
| Store inputs for a data-driven test | `data/<feature>/<name>.json` | `data/login/invalid_users.json` |
| Add a URL or timeout | `config/<env>.yaml` or `base.yaml` | `config/qa.yaml` |
| Add a password or API key | `.env` and the name in `.env.example` | `QA_SUPERADMIN_PASSWORD` |
| Write a test | `tests/ui/` or `tests/api/` | `tests/ui/test_login.py` |
| Share a fixture across tests | `tests/conftest.py` (or a folder-level `conftest.py`) | `page`, `config` |

## Worked example: the login test, layer by layer
This example shows how one scenario ("super admin can log in") touches each folder. Copy this pattern for new features. Selectors are placeholders.

**1. Config** (`config/qa.yaml`) holds the URL and the *names* of credential variables:
```yaml
name: qa
base_url: https://qa.uffizio.com
login_path: /jsp/trakzee_login.jsp
credentials:
  superadmin:
    username_env: QA_SUPERADMIN_USERNAME
    password_env: QA_SUPERADMIN_PASSWORD
```

**2. Secrets** (`.env`, never committed) hold the real values:
```
QA_SUPERADMIN_USERNAME=<your-qa-username>
QA_SUPERADMIN_PASSWORD='<your-qa-password>'
```

**3. Page object** (`src/gridzee_qa/pages/login_page.py`) knows the page, and nothing about test goals:
```python
from gridzee_qa.core.base_page import BasePage

class LoginPage(BasePage):
    USERNAME = "#username"        # placeholder selector
    PASSWORD = "#password"        # placeholder selector
    SUBMIT = "button[type=submit]"

    def open(self) -> None:
        self.goto(self.config.login_url)

    def login(self, username: str, password: str) -> None:
        self.fill(self.USERNAME, username)
        self.fill(self.PASSWORD, password)
        self.click(self.SUBMIT)
```

**4. Flow** (`src/gridzee_qa/flows/auth_flow.py`) is the keyword layer, a business step made from page actions:
```python
class AuthFlow:
    def __init__(self, login_page, config):
        self.login_page = login_page
        self.config = config

    def login_as(self, role: str) -> None:
        creds = self.config.credentials(role)   # reads the .env values
        self.login_page.open()
        self.login_page.login(creds.username, creds.password)
```

**5. Test** (`tests/ui/test_login.py`) reads like steps and holds the assertions:
```python
import pytest

@pytest.mark.ui
@pytest.mark.smoke
def test_superadmin_can_log_in(auth_flow, page):
    auth_flow.login_as("superadmin")
    assert "login" not in page.url
```

**6. Data-driven version** (`data/login/invalid_users.json` plus `parametrize`) runs one test against many inputs:
```python
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("case", load_data("login/invalid_users.json"))
def test_invalid_login_is_rejected(login_page, case):
    login_page.open()
    login_page.login(case["username"], case["password"])
    assert login_page.error_message() == case["expected_error"]
```

**What the example shows**
- The selector `#username` exists in one file. If it changes, only `login_page.py` changes.
- The test does not know about selectors, URLs or passwords.
- Adding a new role means a new entry in the config and `.env`. No page or test code changes.

## Setup
Requires Python 3.12 and Git.

```powershell
# 1. Create the virtual environment (already done in this repo)
python -m venv .venv

# 2. Activate it in every new terminal. You should see (.venv) in the prompt.
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install the Playwright browsers
playwright install

# 5. Create your local secrets file and fill in the values
copy .env.example .env
```
macOS or Linux: use `source .venv/bin/activate` and `cp .env.example .env`.

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

## Running tests
Headless is the default. Always activate `.venv` first.

| Goal | Command |
|---|---|
| Run all tests (headless) | `pytest` |
| Run with a visible browser | `pytest --headed` |
| Pick the environment (`qa` or `demo`) | `pytest --env qa` |
| Smoke tests only | `pytest -m smoke` |
| Regression tests only | `pytest -m regression` |
| UI tests only | `pytest -m ui` |
| API tests only | `pytest -m api` |
| One browser | `pytest --browser firefox` |
| All three browsers | `pytest --browser chromium --browser firefox --browser webkit` |
| Run in parallel | `pytest -n auto` |
| One file | `pytest tests/ui/test_login.py` |
| Retry failed tests up to 3 times | `pytest --reruns 3` |
| Slow motion for debugging | `pytest --headed --slowmo 500` |

### Headed or headless
Highest priority first:
1. Command line: `--headed` for one run.
2. Environment file, for example `config/qa.yaml`: `headless: false`.
3. Default in `config/base.yaml`: `headless: true`.

### Test markers
| Marker | Meaning |
|---|---|
| `smoke` | Fast checks of critical paths. Run on every pull request. |
| `sanity` | Quick check after a change or deployment. |
| `regression` | The full suite. Runs nightly. |
| `ui` / `api` | Type of test. |
| `flaky` | Known unstable test, under review. |
| `auth`, `admin` | Module markers (`pytest -m admin` runs Settings > General > Users > Admin). |
| `creates_data` | Test adds records to the application. Never runs on `demo`. Exclude with `-m "not creates_data"`. |

Every test needs one type marker and one tier marker.

## Reports
Both reports are produced on every run.

| Report | Output | How to open |
|---|---|---|
| HTML | `reports/report.html` | Open the file in a browser |
| Allure | `reports/allure-results` | `allure serve reports/allure-results` |

On failure the framework also saves a screenshot, a video and a Playwright trace. View a trace with `playwright show-trace <trace-file>.zip`. Allure needs its command-line tool installed separately: https://allurereport.org/docs/install/

## Configuration and secrets
| Item | File | Committed? |
|---|---|---|
| URLs, login path, timeouts | `config/*.yaml` | Yes |
| Usernames, passwords, API keys | `.env` | **No** |
| List of required variable names | `.env.example` | Yes |
| Passwords in CI | CI secret store | **No** |

The loader merges settings in this order, where later wins: `config/base.yaml`, then `config/<env>.yaml`, then environment variables.

Select an environment with `--env <name>` or the `ENV` variable. A password that contains `$` must be wrapped in single quotes in `.env`.

## AI-assisted test generation
The CLI agent in `ai_engine/` explores the application and drafts tests. A person approves every stage.

```
explore -> plan -> [approve] -> generate -> [apply] -> run -> [confirm each retry, max 3] -> heal -> [apply]
```
1. **Explore** (`python -m ai_engine explore --nav "Settings > General > Users > Admin" --open-new`): read-only capture of a screen through its menu path.
2. **Plan** (`plan <snapshot> --id-prefix ADM --notes "..."`): proposed scenarios in `ai_workspace/plans/`.
3. **Approve** (`approve <plan id> --ids ... | --all`): nothing is generated before this.
4. **Generate** (`generate <plan id>`): code for approved scenarios, as a proposal with a diff.
5. **Apply** (`apply <proposal> [--branch ai/name]`): writes the code after you confirm.
6. **Run** (`run [paths] -m ...`): failed tests re-run up to 3 times, each after confirmation. Tests that fail and then pass are labelled **flaky**.
7. **Heal** (`heal <run id>`): diagnoses tests that failed every attempt and proposes locator or timing fixes only. Tests are never weakened.

Page content is sanitized before it goes to the AI service. Full guide: `docs/ai-workflow.md`.

## Rules for AI agents and contributors
These rules apply equally to people and to AI agents that read or generate code in this repository.

**The full, binding rule set is [`docs/conventions.md`](docs/conventions.md).** It covers reuse-first, menu-based folders, one page object per screen, run-time data through `utils/data_generator.py`, the test pattern and a checklist. AI agents find it through `AGENTS.md`, `CLAUDE.md` and `.kiro/steering/automation-conventions.md`. The summary below is for quick reading.

**Read first**
1. Read this README, `config/`, `pytest.ini` and an existing page object and test before writing code.
2. Reuse an existing page object, flow or helper before creating a new one.

**Structure**
3. Locators live only in `pages/` and `components/`. Tests never contain locators.
4. Flows are thin. They combine page actions and hold no locators and no assertions about test outcomes.
5. Assertions live in tests (or in `utils/assertions.py` helpers called from tests).
6. Dependencies point downward only: `tests -> flows -> pages/components -> core`. `src/` never imports from `ai_engine/`.

**Tests**
7. Each test is independent. It creates its own data (through `factories/`) and cleans it up.
8. Each test has one type marker (`ui` or `api`) and one tier marker (`smoke`, `sanity` or `regression`).
9. Test names describe behavior: `test_superadmin_can_log_in`.
10. Do not use fixed `sleep`. Use Playwright auto-waiting and `expect`.
11. Prefer stable locators in this order: role, label or text, test id, then CSS. Avoid long XPath chains.
12. Do not run create, edit or delete tests on `demo`.

**Security**
13. Never write a URL, username or password in code, tests or data files. Read them from config and `.env`.
14. Never commit `.env`, `.auth/` or `reports/`.
15. Never print credentials in logs or reports.

**Navigation-based folders**
18. Page objects, flows, tests and data follow the application's menu path. `Settings > General > Users > Admin` lives under `settings/general/users/admin/` in `pages/`, `tests/ui/` and `data/`, and the flow is `flows/settings/general/users/admin_flow.py`. Folder names are lowercase with underscores.

**Process**
16. AI-generated code goes through a pull request and human review like any other code.
17. Run `pre-commit` before pushing. Lint and type checks must pass.

More detail will live in `docs/test-strategy.md`, `docs/conventions.md` and `docs/ai-workflow.md`.

## Roadmap
| Phase | Scope | Status |
|---|---|---|
| 0 | Folder structure, environment config, `.gitignore`, `.venv` | Done |
| 1 | Dependencies, core framework, `conftest.py`, markers, first login test, HTML and Allure reports | Next |
| 2 | API layer, data factories, login session reuse | Planned |
| 3 | Quality gates, Docker, CI pipelines | Planned |
| 4 | AI engine (CLI): explore, plan, generate, run with retries, heal | Written, not executed |
| 5 | Mobile, performance and load testing | Planned |
