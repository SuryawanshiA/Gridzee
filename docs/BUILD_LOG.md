# Framework Build Log

This file records **what was built, where it lives, why it exists and how it is used**, in the order it was built. It is updated at every build step. `README.md` explains how to *use* the framework. This file explains how it was *put together*.

All paths are relative to the project root `Gridzee/`.

**Contents**
- [Step 1: Folder structure](#step-1-folder-structure)
- [Step 2: Environment config and secrets](#step-2-environment-config-and-secrets)
- [Step 3: Virtual environment](#step-3-virtual-environment)
- [Step 4: Dependencies and test runner settings](#step-4-dependencies-and-test-runner-settings)
- [Step 5: Core code](#step-5-core-code)
- [Step 6: Verification](#step-6-verification)
- [Step 7: Auth module (login)](#step-7-auth-module-login)
- [Current state of every folder](#current-state-of-every-folder)
- [How to add to the framework](#how-to-add-to-the-framework)

---

## Step 1: Folder structure

**What:** Created the full folder layout and empty placeholder files. Python package folders got an empty `__init__.py` so they can be imported. Empty folders got a `.gitkeep` file so git keeps them.

**Where and why**

| Location | Why it exists |
|---|---|
| `src/gridzee_qa/` | The framework package. All reusable code lives here. |
| `src/gridzee_qa/core/` | Foundation code every other layer uses (config, logging, base classes). |
| `src/gridzee_qa/pages/` | Page objects: one class per page, holding locators and page actions. |
| `src/gridzee_qa/components/` | UI parts shared across pages (header, modal, table). |
| `src/gridzee_qa/flows/` | Business steps built from page actions (keyword-driven layer). |
| `src/gridzee_qa/api/` | API clients, one per service area. |
| `src/gridzee_qa/models/` | Typed data models for payloads and users. |
| `src/gridzee_qa/factories/` | Create and clean up test data through the API. |
| `src/gridzee_qa/utils/` | Small helpers: data reader, assertions. |
| `src/gridzee_qa/mobile/` | Reserved for future mobile testing. |
| `tests/ui/`, `tests/api/` | Test files. They call flows, pages and API clients, and hold the assertions. |
| `tests/mobile/`, `tests/performance/`, `load/` | Reserved for future phases. |
| `config/` | Per-environment settings. |
| `data/` | Static test data (JSON/YAML) for data-driven tests. |
| `ai_engine/` | Future CLI AI agent. Kept outside `src/` so the framework runs without it. |
| `ai_workspace/` | Future working files of the AI agent. |
| `reports/` | Output of every run: HTML report, Allure results, screenshots, videos, traces, logs. Git-ignored. |
| `.auth/` | Future saved login sessions. Git-ignored. |
| `docs/` | Documentation, including this file. |
| `.github/workflows/` | Future CI pipelines. |

Root files created empty at this step and filled in later: `Dockerfile`, `docker-compose.yml`, `.pre-commit-config.yaml`, `pyproject.toml`.

## Step 2: Environment config and secrets

**What:** Stored the application URLs, the login path and the credential variable names. Stored the real credentials in a local, git-ignored file.

| File | Content | Committed to git? |
|---|---|---|
| `.gitignore` | Rules that keep `.env`, `.auth/`, `reports/`, `.venv/` and Python caches out of git. Written **before** `.env` was created. | Yes |
| `.env` | Real usernames and passwords for QA and demo. A password containing `$` is wrapped in single quotes so `$` is not interpreted. | **No** |
| `.env.example` | The same variable names with empty values. A new team member copies it to `.env` and fills it in. | Yes |
| `config/base.yaml` | Defaults for all environments: browser `chromium`, `headless: true`, viewport 1920x1080, timeouts. | Yes |
| `config/qa.yaml` | QA `base_url`, `login_path`, and the *names* of the credential variables. | Yes |
| `config/demo.yaml` | Demo `base_url`, `login_path`, and the *names* of the credential variables. | Yes |
| `data/users.json` | Describes the `superadmin` role. Holds no URL or password. | Yes |

**Variables in `.env`**
```
ENV                        selects the environment when --env is not given
QA_SUPERADMIN_USERNAME     QA_SUPERADMIN_PASSWORD
DEMO_SUPERADMIN_USERNAME   DEMO_SUPERADMIN_PASSWORD
```

**Why this split:** URLs are not secret, so they are versioned in `config/`. Passwords are secret, so YAML holds only the variable *name* and the value comes from `.env` (locally) or the CI secret store (in pipelines).

**Removed:** the empty `config/dev.yaml` and `config/staging.yaml`, because the real environments are `qa` and `demo`.

## Step 3: Virtual environment

**What:** Created `.venv/` with Python 3.12.6.

**Why:** It keeps this project's packages separate from other Python projects and from the system Python. Anyone can delete `.venv/` and rebuild it from `requirements.txt`.

**Use**
```powershell
.venv\Scripts\activate        # run in each new terminal; the prompt shows (.venv)
```

## Step 4: Dependencies and test runner settings

### `requirements.txt` (project root)
Exact versions that were installed and verified together:

| Package | Version | Purpose |
|---|---|---|
| `pytest` | 9.2.0 | Test runner |
| `playwright` | 1.65.2 | Browser automation |
| `pytest-playwright` | 0.10.0 | Playwright fixtures for pytest (`page`, `browser`, `--headed`, `--browser`) |
| `pytest-xdist` | 3.8.0 | Parallel runs (`-n auto`) |
| `pytest-rerunfailures` | 16.7 | Re-run failed tests (`--reruns 3`) |
| `pytest-html` | 4.2.0 | HTML report |
| `allure-pytest` | 2.16.2 | Allure results |
| `PyYAML` | 6.0.4 | Reads `config/*.yaml` |
| `python-dotenv` | 1.2.4 | Reads `.env` |

### Browsers and tools installed on this machine
- Playwright browsers: Chromium 159, Firefox 159, WebKit 27.2 (`python -m playwright install chromium firefox webkit`). Stored outside the project in `%LOCALAPPDATA%\ms-playwright`.
- Allure command-line tool 2.46.2, installed globally with `npm install -g allure-commandline`. It needs Java, which was already present.

### `pytest.ini` (project root)
| Setting | Why |
|---|---|
| `pythonpath = src` | Tests can write `from gridzee_qa... import ...` without installing the package. |
| `testpaths = tests` | `pytest` finds tests in `tests/` by default. |
| `--strict-markers` | A mistyped marker fails instead of being ignored. |
| `--html=reports/report.html --self-contained-html` | HTML report on every run, in a single file. |
| `--alluredir=reports/allure-results` | Allure data on every run. |
| `--output=reports/artifacts` | Folder for failure screenshots, videos and traces. |
| `--screenshot=only-on-failure --video=retain-on-failure --tracing=retain-on-failure` | Evidence is kept only for failed tests. |
| `markers` | Registers `smoke`, `sanity`, `regression`, `ui`, `api`, `flaky`. |

**Decision:** screenshot, video and trace settings are in `pytest.ini` because pytest-playwright reads them from command-line options. An `artifacts` block that was first placed in `config/base.yaml` would have had no effect, so it was removed.

## Step 5: Core code

Five files in the foundation layer. Dependency order: `exceptions` and `logger` first, then `config_loader`, then `base_page` and `conftest`.

### 5.1 `src/gridzee_qa/core/exceptions.py`
**Purpose:** Custom error types, so framework problems are easy to tell apart from test failures.
- `FrameworkError`: base class.
- `ConfigError`: raised when configuration is missing or wrong (unknown environment, missing variable, unsupported browser).

### 5.2 `src/gridzee_qa/core/logger.py`
**Purpose:** One consistent logging setup.
- `get_logger(name)` returns a logger named `gridzee.<name>`.
- Writes to the console and to `reports/framework.log`.
- Log level comes from the `LOG_LEVEL` variable (default `INFO`).
- **Rule:** never log passwords or tokens.

**Use**
```python
from gridzee_qa.core.logger import get_logger
log = get_logger("MyClass")
log.info("Something happened")
```

### 5.3 `src/gridzee_qa/core/config_loader.py`
**Purpose:** Builds one `Config` object for the selected environment.

**Merge order (later wins):** `config/base.yaml`, then `config/<env>.yaml`, then process environment variables loaded from `.env`.

**What `Config` offers**
| Member | Meaning |
|---|---|
| `config.env` | `qa` or `demo` |
| `config.base_url` | For example `https://qa.uffizio.com` |
| `config.login_url` | `base_url` plus `login_path` |
| `config.browser`, `config.headless`, `config.slow_mo_ms` | Browser settings |
| `config.viewport`, `config.timeouts` | Window size and wait limits |
| `config.credentials("superadmin")` | Returns a `Credentials(username, password)` read from `.env` |

**Safety details**
- `Credentials.password` is excluded from `repr()`, so it does not appear in logs or tracebacks.
- `credentials()` raises a `ConfigError` that names the missing variable, never its value.
- An unknown environment fails with the list of available ones.

**Functions:** `load_config(env)`, `resolve_env_name(cli_value)` (order: `--env`, then `ENV` variable, then `qa`), `available_envs()`.

### 5.4 `src/gridzee_qa/core/base_page.py`
**Purpose:** Parent class of every page object. It wraps common Playwright actions and logs each one.

| Method | Does |
|---|---|
| `goto(url_or_path)` | Opens a full URL, or a path relative to `base_url` |
| `wait_for_url(pattern)` | Waits for the URL to match |
| `locator(selector)` | Returns a Playwright locator |
| `click`, `fill`, `press` | Element actions. `fill` does **not** log the value, because it may be a password |
| `get_text`, `is_visible` | Read element state |
| `wait_for_visible`, `wait_for_hidden` | Wait for an element |
| `screenshot(name)` | Saves `reports/screenshots/<name>.png` |

**Rules**
- A page object extends `BasePage` and holds locators and actions only.
- Assertions about test outcomes go in the tests.
- No fixed sleeps. Playwright waits for elements automatically.

**Use**
```python
from gridzee_qa.core.base_page import BasePage

class SomePage(BasePage):
    BUTTON = "button#save"          # real selectors are added with the real pages

    def save(self) -> None:
        self.click(self.BUTTON)
```

### 5.5 `tests/conftest.py`
**Purpose:** Connects the config to pytest and pytest-playwright. Applies to every test under `tests/`.

| Item | What it does |
|---|---|
| `--env` option | Chooses the environment. If omitted, uses the `ENV` variable, then `qa`. |
| `pytest_configure` | Loads the config once. If `--browser` is not given, uses the browser from config. A config error stops the run with a clear message. |
| `pytest_report_header` | Prints `gridzee: env=... base_url=... mode=headless` at the top of every run. |
| `config` fixture | Gives tests the `Config` object. |
| `base_url` fixture | Lets `page.goto("/path")` resolve against the environment URL. |
| `browser_type_launch_args` | Applies `headless` and `slow_mo` from config. `--headed` on the command line wins. |
| `browser_context_args` | Applies the viewport from config. |
| `_expect_timeout` (automatic) | Applies `expect_ms` to every `expect()` assertion. |
| `page` fixture | Applies the default and navigation timeouts from config. |

**Headless or headed, highest priority first:** `--headed`, then `headless: false` in `config/<env>.yaml`, then `headless: true` in `config/base.yaml`.

## Step 6: Verification
A temporary test opened the real login page without logging in, then was deleted. Results:

| Check | Result |
|---|---|
| QA login page, Chromium, headless | Passed. Page title `Login` |
| QA login page, Chromium, Firefox and WebKit in one run | 3 passed |
| Demo login page, Firefox (`--env demo`) | Passed |
| Environment taken from the `ENV` variable, no flag | Selected `demo` |
| Unknown environment (`--env nope`) | Stopped with `Unknown environment 'nope'. Available: demo, qa.` |
| `--headed` | Header showed `mode=headed`. Launch option `headless` was `False` |
| Credentials resolved from `.env`, password hidden in `repr()` | Passed |
| Viewport 1920x1080 applied | Passed |
| Secret scan of `src/` and `reports/` for the real passwords | None found |
| `pip check` | No broken requirements |

Not yet verified: a login with real credentials, API tests, parallel runs (`-n auto`), Allure report opening, and the retry flow.

## Step 7: Auth module (login)

**What:** The first application module. Login is the only module whose behavior is known, so it was built first and sets the pattern for later modules. Every layer has an `auth` location.

### What was observed on the real login page
The QA login page was inspected with Playwright, without logging in, and then one successful login was made to see the landing page.

| Finding | Value |
|---|---|
| Login form | `<form id="login_form">` posting to `/UserLogin` |
| Fields | `#username`, `#password`, checkbox `#rememberMe` |
| Submit button | `button[type=submit]` inside `#login_form` |
| Extra fields or captcha | None |
| Page title | `Login` |
| After a successful login | URL `/jsp/index.html`, title starts with `Trakzee` |
| Main menu after login | Left sidebar: Dashboard, Reports, Charts, Settings |
| Page structure | Many nested frames (`Tree.jsp`, `TitleFrame.jsp`, `oldindex.jsp` and others). Later page objects must use `page.frame_locator(...)` for content inside frames. |

The forgot-password link, the language list and the app-store links also exist on the page. They are not used yet.

### Files created
| Location | Purpose |
|---|---|
| `src/gridzee_qa/pages/auth/login_page.py` | `LoginPage(BasePage)`. Holds the locators `USERNAME`, `PASSWORD`, `REMEMBER_ME`, `SUBMIT`, and the actions `open()`, `login(username, password)` and `wait_until_logged_in()`. |
| `src/gridzee_qa/pages/auth/__init__.py` | Makes `auth` an importable package. |
| `src/gridzee_qa/flows/auth_flow.py` | `AuthFlow.login_as(role)`. Reads the role's credentials from config, opens the login page, signs in and waits for the landing page. |
| `tests/ui/conftest.py` | UI fixtures `login_page` and `auth_flow`. |
| `tests/ui/auth/test_login.py` | Two smoke tests, marked `ui`, `smoke` and `auth`. |

### Changes to existing files
| File | Change | Reason |
|---|---|---|
| `pytest.ini` | Added the `auth` marker | Each module is a marker, so `pytest -m auth` runs one module. |
| `pytest.ini` | Added `--import-mode=importlib` | Lets two modules have test files with the same name without a conflict. |

### The tests
| Test | Checks |
|---|---|
| `test_login_page_shows_the_login_form` | Title is `Login`. The username field, password field and submit button are visible. |
| `test_superadmin_can_log_in` | After `login_as("superadmin")`, the URL contains `/jsp/index.html` and the title starts with `Trakzee`. |

**Use**
```powershell
pytest -m auth                                   # auth module, QA, headless
pytest -m auth --env demo                        # same on demo
pytest -m auth --browser firefox                 # one other browser
pytest tests/ui/auth/test_login.py --headed      # watch it run
```

### Results
| Run | Result |
|---|---|
| QA, Chromium + Firefox + WebKit | 6 passed |
| Demo, Chromium | 2 passed |

### Not tested yet
An invalid-login test (wrong password, expected error message). It was left out on purpose, because repeated failed logins on the shared super admin account could lock it. Add it after confirming that lockout is not a risk, or with a dedicated test user.

## Step 8: Navigation-based folders for Settings > General > Users > Admin

**Rule:** page objects, flows, tests and data follow the application's menu path. A screen reached by `Settings > General > Users > Admin` lives under `settings/general/users/admin/` in every layer. Folder names are lowercase with underscores.

| Location | Purpose |
|---|---|
| `src/gridzee_qa/pages/settings/general/users/admin/` | Page objects for the Admin overview and add/edit form (to be written) |
| `src/gridzee_qa/flows/settings/general/users/` | `admin_flow.py` (to be written) |
| `tests/ui/settings/general/users/admin/` | Admin UI tests (to be written) |
| `data/settings/general/users/admin/` | Static data for Admin tests, if any |
| `docs/test-cases/settings/general/users/admin.md` | Explored behavior and test cases, awaiting review |

Each `src/` folder has an empty `__init__.py` so it can be imported. Test and data folders have a `.gitkeep`.

## Step 9: Admin automation (Settings > General > Users > Admin)

**What:** All Admin test cases from `docs/test-cases/settings/general/users/admin.md` were automated. **They have not been executed yet.** Only static checks were run (see the end of this step).

### Core additions
| Location | Change | Why |
|---|---|---|
| `src/gridzee_qa/core/base_page.py` | `frame(name, url_part)` and `wait_until(condition)` | The application is built from named frames. `wait_until` polls a condition instead of sleeping. |
| `src/gridzee_qa/core/base_component.py` | `BaseComponent` | Parent of shared UI parts. |
| `src/gridzee_qa/core/exceptions.py` | `WaitTimeoutError` | Clear error when a wait runs out. |
| `src/gridzee_qa/core/config_loader.py`, `config/base.yaml` | `email_domain` (`test_data.email_domain`, default `yopmail.com`) | Domain for generated emails, changeable without code. |
| `src/gridzee_qa/flows/auth_flow.py` | `login_with(username, password)` | Lets tests log in as a created admin. `login_as(role)` now uses it. |

### Shared components (`src/gridzee_qa/components/`)
| File | Covers |
|---|---|
| `side_menu.py` | Sidebar in frame `divframe`. `navigate("Settings", "General", "Users", "Admin")` |
| `bottom_toolbar.py` | Frame `bottomframe`: New, Save, Back, Reset, exports, search, paging, record counter |
| `message_box.py` | Validation box `.jalert-parent` in any frame: read text, close |

### Admin page objects (`src/gridzee_qa/pages/settings/general/users/admin/`)
| File | Covers |
|---|---|
| `admin_overview_page.py` | Grid in `contentframe` (`Overview.jsp`): columns, rows, "No Records Found", open row, share popup, column headers, title icons |
| `admin_form_page.py` | Form in `contentframe` (`DetailScreen.jsp`): 17 tabs, field names, max lengths, defaults, chosen dropdowns, password eye and info icon |

### Flow (`src/gridzee_qa/flows/settings/general/users/admin_flow.py`)
`AdminFlow` combines the above: `open_overview`, `open_add_form`, `fill_my_account`, `save`, `save_expecting_message` (fails if a form that should be rejected is saved), `create_admin`, `search`, `find_by_short_name`, `find_by_username`, `reset_search`.

### Run-time data (`src/gridzee_qa/factories/admin_factory.py`)
`AdminFactory.build()` returns a new `AdminData` with unique values for every My Account text field, within each field's max length. Unique part: timestamp + per-process counter + random suffix. Negative values (invalid email, weak password, letters, over-length text) come from the same class. Standard library only, no new package.

### Created-admin credentials (`src/gridzee_qa/utils/credential_store.py`)
`save_admin(env, admin)` appends to `.auth/created_admins.json` (git-ignored). `latest_admin(env)` reads the newest one, for later login automation.

### Tests (`tests/ui/settings/general/users/admin/`)
| File | IDs |
|---|---|
| `conftest.py` | Fixtures: `admin_flow_at_home`, `admin_flow`, `admin_form`, `admin_factory`, `remember_admin`, `created_admin`. Browser dialogs are accepted and logged. |
| `test_admin_navigation.py` | ADM-001 to 006 |
| `test_admin_search.py` | ADM-010 to 018 |
| `test_admin_paging_sorting.py` | ADM-020 to 025 |
| `test_admin_export_share.py` | ADM-030 to 034 |
| `test_admin_form_display.py` | ADM-040 to 048 |
| `test_admin_validation.py` | ADM-050 to 064 |
| `test_admin_create.py` | ADM-070 to 076 (`creates_data`) |

### Safety rules in the code
- Tests that add records carry the `creates_data` marker. `tests/conftest.py` skips them on `demo`.
- Validation tests always leave Admin Code (the last field checked) blank, and `save_expecting_message` fails if a save goes through anyway.
- Passwords are never logged (`set_field` logs only the field name; `AdminData` hides the password from `repr`).

### Markers added to `pytest.ini`
`admin`, `creates_data`.

### Static checks (no browser, no application access)
| Check | Result |
|---|---|
| `python -m compileall src tests` | No errors |
| `pytest --collect-only` for Admin | 66 tests collected (58 read-only, 8 `creates_data`) |
| Data generator, 500 records offline | No duplicates, all within max lengths, all passwords meet the rule. A duplicate-token bug was found and fixed during this check. |

### Not verified (needs the first run)
Selectors that were never exercised during exploration: the password eye icon, the info tooltip, column-header sorting, previous/next icons and the Country/State dropdown text. They may need adjustment after the first run.

## Step 10: AI engine (`ai_engine/`)

**What:** The CLI agent that explores a screen, plans scenarios, generates code, runs tests with up to 3 confirmed retries, and heals failures. **Written, not executed.** Only a compile check was run. Full usage: `docs/ai-workflow.md`.

**Decisions**
| Decision | Choice | Why |
|---|---|---|
| Location | `ai_engine/` outside `src/` | The framework runs without it; `src/` never imports it |
| AI | Claude via the `anthropic` SDK 2.14 (`ai_engine/requirements.txt`, not installed yet) | Requested provider. Bedrock selectable with `AI_PROVIDER` |
| Model | `AI_MODEL` setting, no default | Avoids silently using an outdated model name |
| Approval | Plan approval, apply confirmation, retry confirmation | Matches the agreed human gates |
| Healing | Locator and timing fixes in `pages/` and `components/` only | A test is never made to pass by weakening it |

**Files**
| Location | Purpose |
|---|---|
| `ai_engine/__init__.py`, `__main__.py`, `cli.py` | `python -m ai_engine <command>` |
| `ai_engine/settings.py` | Paths, AI settings, allowed write folders |
| `ai_engine/workspace.py` | Ids, JSON, navigation slugs, path checks, proposals, diffs, confirmation prompt |
| `ai_engine/sanitizer.py` | Masks secrets and personal data before AI calls |
| `ai_engine/llm.py` | Claude client and JSON parsing |
| `ai_engine/explorer.py` | Read-only capture of a screen, its form and tabs |
| `ai_engine/planner.py` | Scenario plan (JSON + Markdown) and approve/reject |
| `ai_engine/generator.py` | Code proposal for approved scenarios |
| `ai_engine/applier.py` | Applies a proposal after confirmation; optional git branch; adds markers to `pytest.ini` |
| `ai_engine/runner.py` | pytest run, confirmed retries of failed node ids, passed/flaky/failed labels |
| `ai_engine/healer.py` | Diagnosis and fix proposal for tests that failed every attempt |
| `ai_engine/prompts/planner.md`, `generator.md`, `healer.md` | AI instructions |

**Other changes:** `.env.example` (AI settings), `.gitignore` (`ai_workspace/generated`, `heal`, `runs` ignored; `plans` committed), `docs/ai-workflow.md` (written).

**Checks:** `python -m compileall ai_engine` passed. Nothing else was run: no AI call, no browser, no pytest run.

**Before first use:** `pip install -r ai_engine/requirements.txt`, and set `AI_MODEL` plus the API key in `.env`.

## Step 11: Binding conventions and a generic data generator

**Decisions confirmed by the user:** keep one page object per screen (overview and form) inside the menu folder, keep tests split by group for large modules, reuse existing code before creating new code, and make the data generator a reusable utility.

### Conventions
| Location | Purpose |
|---|---|
| `docs/conventions.md` | **Single source of the rules**, with a checklist and a new-module template |
| `AGENTS.md` | Short pointer read by most AI coding agents |
| `CLAUDE.md` | Pointer for Claude Code (imports `AGENTS.md` and `docs/conventions.md`) |
| `.kiro/steering/automation-conventions.md` | Always-included Kiro steering file that pulls in `docs/conventions.md` |
| `ai_engine/generator.py`, `ai_engine/healer.py`, `ai_engine/prompts/generator.md` | The AI engine now sends `docs/conventions.md` (and the data generator) with every generate and heal request, and the prompt calls it binding |
| `README.md` | Points to `docs/conventions.md` |

### Generic data generator (`src/gridzee_qa/utils/data_generator.py`)
- **Standalone:** standard library only, no project imports. It can be copied into any project.
- `FieldSpec` describes a field (name, label, input type, max length, required, options, placeholder, prefix). `FieldSpec.from_dict()` accepts the field dicts captured by the explorer.
- `DataGenerator.value(spec)` infers the kind from the name, label and placeholder: email, password, phone, zip code, city, street, URL, person name, code, integer, sentence, date, unique label, dropdown choice, text. The value always fits the max length.
- `DataGenerator.record(specs)` fills a whole form with one shared token; `confirm_*` and `retype_*` fields copy their partner field.
- Negative data: `invalid_email()`, `weak_password()`, `letters()`, `over_length(spec)`.

### Admin factory refactored (`src/gridzee_qa/factories/admin_factory.py`)
Now a thin layer: `MY_ACCOUNT_FIELDS` (field specs in form order) plus `AdminData` and `AdminFactory`. All value rules moved to the generator. The public methods used by the tests are unchanged.

### Checks (offline, no browser, no application)
| Check | Result |
|---|---|
| Kind inference for all 18 Admin fields | Correct after one fix: "message" matched the keyword "age"; matching now uses whole words (plural allowed) |
| 500 Admin records | No duplicates, within max lengths, correct prefixes, numeric fields are digits, strong passwords, password hidden from `repr` |
| Generic captured fields (driver name, email + confirm, date, dropdown, remarks) | Correct kinds; confirm copied; placeholder option never chosen; max length respected |
| `compileall`, `pytest --collect-only` | Passed; 68 tests collected |

## Current state of every folder

| Location | State |
|---|---|
| `src/gridzee_qa/core/` | **Done:** `exceptions.py`, `logger.py`, `config_loader.py`, `base_page.py`. **Empty:** `base_component.py`, `base_api.py` |
| `src/gridzee_qa/pages/auth/` | **Done:** `login_page.py` |
| `src/gridzee_qa/flows/` | **Done:** `auth_flow.py` |
| `src/gridzee_qa/components/`, `api/`, `models/`, `factories/` | Empty. Filled once the application modules are defined. |
| `src/gridzee_qa/utils/` | Empty files: `data_reader.py`, `helpers.py`, `assertions.py` |
| `tests/conftest.py` | **Done** |
| `tests/ui/conftest.py` | **Done:** `login_page`, `auth_flow` fixtures |
| `tests/ui/auth/` | **Done:** `test_login.py` (2 tests) |
| `tests/api/` | No tests yet |
| `config/`, `data/users.json`, `.env`, `.env.example`, `.gitignore` | **Done** |
| `pytest.ini`, `requirements.txt` | **Done** |
| `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.pre-commit-config.yaml` | Empty (phase 3) |
| `.github/workflows/` | Empty (phase 3) |
| `ai_engine/`, `ai_workspace/` | Empty (phase 4) |
| `mobile/`, `performance/`, `load/` | Empty (phase 5) |
| `docs/test-strategy.md`, `conventions.md`, `ai-workflow.md` | Empty |

## How to add to the framework
Each new page, flow or test follows the same path. Replace `<module>` with the application module name once modules are defined.

| To add | Create | In |
|---|---|---|
| A page | `<page>_page.py`, a class that extends `BasePage` | `src/gridzee_qa/pages/` |
| A shared UI part | `<part>.py` | `src/gridzee_qa/components/` |
| A business step | `<module>_flow.py` | `src/gridzee_qa/flows/` |
| A test | `test_<behavior>.py` with a type marker and a tier marker | `tests/ui/` or `tests/api/` |
| Test data | `<name>.json` | `data/` |
| A new environment | `<env>.yaml` plus its variables in `.env` and `.env.example` | `config/` |

---

## Change history
| Step | Summary |
|---|---|
| 1 | Folder structure created |
| 2 | Environment config, `.gitignore`, `.env`, `.env.example` |
| 3 | Virtual environment `.venv` |
| 4 | Dependencies, browsers, Allure CLI, `pytest.ini` |
| 5 | Core code: `exceptions`, `logger`, `config_loader`, `base_page`, `conftest` |
| 6 | Core code verified against QA and demo on three browsers |
| 7 | Auth module: `LoginPage`, `AuthFlow`, UI fixtures, 2 smoke tests, all passing |
| 8 | Navigation-based folders for Admin; Admin test cases drafted for review |
| 9 | Admin automation: components, page objects, flow, data generator, 66 tests. Not executed yet |
| 10 | AI engine: explore, plan, generate, apply, run with retries, heal. Not executed yet |
| 11 | Binding conventions for people and AI agents; generic data generator; Admin factory on top of it |
