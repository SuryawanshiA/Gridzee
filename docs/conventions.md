# Automation Conventions (binding)

These rules apply to **every person and every AI agent** (Kiro, Claude, the `ai_engine` generator and healer) that writes or changes code in this repository. They keep new features consistent with the existing ones.

The reference implementation is **Settings > General > Users > Admin**. When in doubt, copy how Admin does it.

---

## 1. Reuse first, create second

Before writing anything, search the existing code. Use it if it exists. Create something new only if it does not.

| Need | Look here first | Rule |
|---|---|---|
| Click, fill, wait, frames | `src/gridzee_qa/core/base_page.py` (`frame`, `wait_until`) | Never re-implement waiting or frame lookup |
| Sidebar navigation | `components/side_menu.py` (`navigate(...)`) | Every screen is opened through it |
| New, Save, Back, Reset, search, paging, export, counter | `components/bottom_toolbar.py` | Never write these locators in a page object |
| Validation and info messages | `components/message_box.py` | |
| Login | `flows/auth_flow.py` (`login_as`, `login_with`) | |
| Test data | `utils/data_generator.py` (`DataGenerator`, `FieldSpec`) | Never hard-code data; never write a second generator |
| Created-record credentials | `utils/credential_store.py` | |
| Fixtures (`page`, `config`, `login_page`, `auth_flow`) | `tests/conftest.py`, `tests/ui/conftest.py` | |

- If an existing class almost fits, **extend it** (new method or parameter). Do not copy it.
- If two features need the same new helper, put it in `components/` or `utils/`, not in a feature folder.
- Do not rename or move existing public methods unless asked. Other tests use them.

## 2. Folders follow the application menu

The menu path of a screen is its folder path in every layer. Lowercase, words joined with `_`.

`Settings > General > Users > Admin` becomes:

| Layer | Location |
|---|---|
| Page objects | `src/gridzee_qa/pages/settings/general/users/admin/` |
| Flow | `src/gridzee_qa/flows/settings/general/users/admin_flow.py` |
| Data factory | `src/gridzee_qa/factories/admin_factory.py` |
| Tests and feature fixtures | `tests/ui/settings/general/users/admin/` (with `conftest.py`) |
| Static data (only if truly static) | `data/settings/general/users/admin/` |
| Test-case document | `docs/test-cases/settings/general/users/admin.md` |

Every folder under `src/gridzee_qa/` has an `__init__.py`.

## 3. Page objects: one class per screen

A menu item usually opens an **overview** (grid) and a **detail** (add/edit form). Each screen gets its own class, in the same module folder:

| Screen | File | Class |
|---|---|---|
| Overview (grid) | `<module>_overview_page.py` | `<Module>OverviewPage` |
| Detail (add/edit form) | `<module>_form_page.py` | `<Module>FormPage` |

Rules:
- Extend `BasePage` (pages) or `BaseComponent` (shared parts).
- Locators are class constants (`SHORT_NAME = "short_name"`, `SHARE_ICON = "a#send_cred_link"`). Locators exist **only** in page objects and components.
- Page objects hold actions and state readers. **No test assertions.**
- Reach frame content with `self.frame("contentframe", "<url part>")`. Known frames: `divframe` (menu), `contentframe` (screen), `bottomframe` (toolbar), `titleframe` (title icons).
- Locator preference: `name`/`id` attribute, role or label, visible text, test id, then CSS. Avoid long XPath.
- Never log field values (`set_field` logs only the field name).
- Start the file with a docstring: the menu path, the frame and URL part, and anything unusual about the screen.

## 4. Flows: one per module

`<module>_flow.py` with class `<Module>Flow`. It combines menu, toolbar, message box and the module's page objects into business steps: `open_overview`, `open_add_form`, `fill_...`, `save`, `save_expecting_message`, `create_<module>`, `search`, `find_by_...`, `reset_search`.

- Flows hold **no locators** and no assertions, except safety guards (`save_expecting_message` fails if a form that must be rejected was saved).
- Copy the method names from `admin_flow.py` when the behavior is the same.

## 5. Test data: always generated at run time

- Use `DataGenerator` and `FieldSpec` from `utils/data_generator.py`. Describe each field once (name, label, input type, max length, required, prefix). The generator chooses a fitting value.
- Each module has a thin factory in `factories/<module>_factory.py`: the field list in form order, plus a `<Module>Data` dataclass and a `build(**overrides)` method. See `admin_factory.py`.
- Unique values (names, emails, codes) use a prefix that makes test records easy to find: `Auto <Module> <token>`, `auto.<module>.<token>@<domain>`, `<CODE><token>`.
- Email domain comes from `config.email_domain` (`config/base.yaml`).
- Negative data comes from the same generator: `invalid_email()`, `weak_password()`, `letters()`, `over_length(spec)`.
- Passwords are hidden from `repr` (`field(repr=False)`).
- `data/` is only for values that are truly fixed (for example a list of expected menu labels). Never put generated-style data there.

## 6. Tests

**File layout**
- 15 tests or fewer for a module: one file, `test_<module>.py`.
- More than 15: one file per group, `test_<module>_<group>.py`, for example `test_admin_search.py`, `test_admin_validation.py`, `test_admin_create.py`.
- All tests that save records go in `test_<module>_create.py` (or the single file, clearly marked).

**Each test**
- Name: `test_<id>_<behavior>`, for example `test_adm_070_create_admin_with_mandatory_fields`. The id matches the test-case document.
- Module-level `pytestmark = [pytest.mark.ui, pytest.mark.<module>]`, plus one tier marker per test: `smoke`, `sanity` or `regression`.
- Tests that save records: `@pytest.mark.creates_data` (module-level in the create file). They never run on `demo`.
- Validation tests leave at least one mandatory field blank (the last one validated) and use `save_expecting_message()`.
- Assertions live in tests. Use clear failure messages.
- Search terms and other inputs come from the generator or from the screen at run time.
- No fixed sleeps. Use Playwright auto-waiting, `expect()`, or `wait_until` with a condition that cannot be met by the previous screen state.
- Use `pytest.mark.parametrize` for the same check over several inputs, with readable `ids`.
- Use `pytest.skip` with a reason for a precondition the environment lacks, and for a decision still pending.

**Feature `conftest.py`** (copy from Admin)
- `<module>_flow_at_home`: logged in, on the landing page. Accepts and logs browser dialogs.
- `<module>_flow`: on the module overview.
- `<module>_form`: on an empty add form.
- `<module>_factory`, `remember_<module>`, `created_<module>` (reuses the record created earlier in the run).

**Markers**
- Register every new marker in `pytest.ini` (`--strict-markers` is on). Each module has its own marker.

## 7. Safety

- Never write URLs, usernames or passwords in code, tests, data or docs. They come from `config/` and `.env`.
- Never delete existing records in the application.
- Never create, edit or delete data on `demo`.
- Never commit `.env`, `.auth/`, `reports/`.
- Never print credentials in logs or reports.

## 8. Code style

- Python 3.12, type hints on public functions, `from __future__` not required.
- Module docstring at the top of every file: what it covers and where it sits in the menu.
- Short methods with one job. Names describe behavior (`find_by_short_name`, not `do_search2`).
- Constants in UPPER_CASE at class or module level.
- Standard library first. A new third-party package needs agreement first and goes in `requirements.txt` with a pinned version.

## 9. Documentation, every time

When a feature is added or changed, update in the same change:
1. `docs/test-cases/<menu path>.md`: explored behavior, test cases with ids, automation mapping, open questions.
2. `docs/BUILD_LOG.md`: a new step describing what was added, where, and why.
3. `pytest.ini`: new markers.

## 10. Checklist before a change is done

- [ ] Searched existing code and reused it (section 1).
- [ ] Folders match the menu path (section 2).
- [ ] One page object per screen; no locators outside pages and components (section 3).
- [ ] Data comes from `DataGenerator` through the module factory (section 5).
- [ ] Every test has an id, a type, a tier and a module marker; data-changing tests are `creates_data` (section 6).
- [ ] No fixed sleeps; no secrets; no hard-coded data (sections 6 and 7).
- [ ] `python -m compileall src tests` and `pytest --collect-only` pass.
- [ ] Docs updated (section 9).
- [ ] Tests are run only with the user's permission.

## Template for a new module

Replace `<menu>/<path>/<module>` and `<Module>`:

```
src/gridzee_qa/pages/<menu>/<path>/<module>/__init__.py
src/gridzee_qa/pages/<menu>/<path>/<module>/<module>_overview_page.py   class <Module>OverviewPage(BasePage)
src/gridzee_qa/pages/<menu>/<path>/<module>/<module>_form_page.py       class <Module>FormPage(BasePage)
src/gridzee_qa/flows/<menu>/<path>/<module>_flow.py                     class <Module>Flow
src/gridzee_qa/factories/<module>_factory.py                            <MODULE>_FIELDS, <Module>Data, <Module>Factory
tests/ui/<menu>/<path>/<module>/conftest.py
tests/ui/<menu>/<path>/<module>/test_<module>[_<group>].py
docs/test-cases/<menu>/<path>/<module>.md
```
