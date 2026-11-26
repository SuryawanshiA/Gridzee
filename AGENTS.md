# Instructions for AI agents

This is a Python + Playwright + pytest test automation framework for the Trakzee web application.

Before writing or changing any code, read and follow **`docs/conventions.md`**. It is binding. In short:

1. **Reuse existing code first.** Search `src/gridzee_qa/` (core, components, flows, factories, utils) before creating anything. Extend, don't duplicate.
2. **Folders follow the application menu**, for example `Settings > General > Users > Admin` lives in `.../settings/general/users/admin/` in every layer.
3. **One page object per screen** (`<module>_overview_page.py`, `<module>_form_page.py`). Locators only in page objects and components.
4. **Test data is generated at run time** with `src/gridzee_qa/utils/data_generator.py`, through a thin module factory. Never hard-code data.
5. **Tests** follow the Admin pattern: ids in names, markers, `creates_data` for anything that saves, one file per group when a module has more than 15 tests.
6. **Never** hard-code credentials or URLs, delete records, change data on `demo`, or run tests without the user's permission.

Reference implementation: Settings > General > Users > Admin. Other docs: `README.md` (usage), `docs/BUILD_LOG.md` (how the framework was built), `docs/ai-workflow.md` (AI engine).
