"""Stage 1, explore: open a feature through the menu and record what is on screen.

Read-only. The explorer logs in, follows the menu path, and captures every frame:
form fields (label, name, mandatory, max length, default), buttons and links,
grids (headers and a few sample rows) and visible messages. With ``open_new`` it
also clicks New (+) and captures the empty form, and it can visit named tabs.
It never clicks Save, Delete or any other button that changes data.

Output: ai_workspace/exploration/<navigation slug>/<timestamp>/snapshot.json and screenshots.
"""

from pathlib import Path
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright

from ai_engine.settings import EXPLORATION_DIR
from ai_engine.workspace import new_id, slug, write_json
from gridzee_qa.components.bottom_toolbar import BottomToolbar
from gridzee_qa.components.side_menu import SideMenu
from gridzee_qa.core.config_loader import load_config, resolve_env_name
from gridzee_qa.flows.auth_flow import AuthFlow
from gridzee_qa.pages.auth.login_page import LoginPage

SETTLE_MS = 2000  # exploration tool only: lets dynamic content finish after each step

_CAPTURE_JS = r"""() => {
    const vis = e => !!(e.offsetWidth || e.offsetHeight);
    const norm = s => (s || '').replace(/\s+/g, ' ').trim();
    const labelOf = e => {
        if (e.id) { const l = document.querySelector(`label[for="${CSS.escape(e.id)}"]`); if (l) return norm(l.innerText); }
        const row = e.closest('tr') || e.closest('.form-group') || e.parentElement;
        return row ? norm((row.innerText || '').split('\n')[0]).slice(0, 80) : '';
    };
    const fields = Array.from(document.querySelectorAll('input, select, textarea'))
        .filter(e => e.type !== 'hidden' && vis(e))
        .map(e => {
            const label = labelOf(e);
            const f = {tag: e.tagName.toLowerCase(), type: e.type || null, id: e.id || null, name: e.name || null,
                label, mandatory: /\*/.test(label) || e.required, maxlength: e.maxLength > 0 ? e.maxLength : null,
                placeholder: e.placeholder || null, classes: (e.className || '').toString().slice(0, 60)};
            if (e.type === 'checkbox' || e.type === 'radio') f.checked = e.checked;
            else f.value = (e.value || '').slice(0, 60);
            if (e.tagName === 'SELECT') { f.options_count = e.options.length; f.options = Array.from(e.options).slice(0, 30).map(o => norm(o.text)); }
            return f;
        });
    const actions = Array.from(document.querySelectorAll('a, button, input[type=button], input[type=submit]'))
        .filter(vis)
        .map(e => ({tag: e.tagName.toLowerCase(), id: e.id || null, title: e.getAttribute('title'),
            text: norm(e.innerText || e.value).slice(0, 60), classes: (e.className || '').toString().slice(0, 60)}))
        .filter(a => a.title || a.text)
        .slice(0, 200);
    const tables = Array.from(document.querySelectorAll('table')).filter(vis).map(t => {
        const rows = Array.from(t.querySelectorAll(':scope > tbody > tr, :scope > thead > tr, :scope > tr')).filter(vis);
        const cells = r => Array.from(r.children).filter(c => c.tagName === 'TD' || c.tagName === 'TH').map(c => norm(c.innerText).slice(0, 80));
        if (!rows.length) return null;
        const headers = cells(rows[0]);
        return {headers, rows: rows.slice(1).map(cells).filter(r => r.length === headers.length).slice(0, 5)};
    }).filter(t => t && t.headers.length >= 3).slice(0, 5);
    const messages = Array.from(document.querySelectorAll('.jalert-parent')).filter(vis).map(e => norm(e.innerText));
    return {fields, actions, tables, messages};
}"""


def _settle(page: Page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except PlaywrightError:
        pass  # the application keeps polling; fall back to a short settle
    page.wait_for_timeout(SETTLE_MS)


def _capture(page: Page, step: str, out_dir: Path) -> dict[str, Any]:
    frames = []
    for index, frame in enumerate(page.frames):
        if frame.url in ("about:blank", "") or frame.is_detached():
            continue
        try:
            content = frame.evaluate(_CAPTURE_JS)
        except PlaywrightError as error:
            content = {"error": type(error).__name__}
        if content.get("fields") or content.get("actions") or content.get("tables") or content.get("messages"):
            frames.append({"index": index, "name": frame.name, "url": frame.url, **content})
    screenshot = out_dir / f"{step}.png"
    page.screenshot(path=str(screenshot))
    return {"step": step, "screenshot": screenshot.name, "frames": frames}


def _click_tab(page: Page, tab: str) -> bool:
    for frame in page.frames:
        try:
            target = frame.get_by_text(tab, exact=True).locator("visible=true")
            if target.count():
                target.first.click()
                return True
        except PlaywrightError:
            continue
    return False


def explore(
    navigation: list[str],
    env: str | None = None,
    role: str = "superadmin",
    open_new: bool = False,
    tabs: list[str] | None = None,
    headed: bool = False,
) -> Path:
    config = load_config(resolve_env_name(env))
    out_dir = EXPLORATION_DIR / slug(navigation) / new_id("explore")
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot: dict[str, Any] = {
        "navigation": navigation, "env": config.env, "base_url": config.base_url, "role": role,
        "steps": [], "dialogs": [], "notes": [],
    }

    with sync_playwright() as playwright:
        browser = getattr(playwright, config.browser).launch(headless=not headed)
        context = browser.new_context(viewport={"width": config.viewport.width, "height": config.viewport.height})
        page = context.new_page()
        page.set_default_timeout(config.timeouts.default_ms)
        # Read-only: dismiss any confirmation instead of accepting it.
        page.on("dialog", lambda d: (snapshot["dialogs"].append({"type": d.type, "message": d.message}), d.dismiss()))
        try:
            AuthFlow(LoginPage(page, config), config).login_as(role)
            _settle(page)
            SideMenu(page, config).navigate(navigation[0], *navigation[1:])
            _settle(page)
            snapshot["steps"].append(_capture(page, "01_screen", out_dir))

            if open_new:
                toolbar = BottomToolbar(page, config)
                if toolbar.is_new_visible():
                    toolbar.click_new()
                    _settle(page)
                    snapshot["steps"].append(_capture(page, "02_new_form", out_dir))
                else:
                    snapshot["notes"].append("No New (+) button found on this screen.")

            for number, tab in enumerate(tabs or [], start=3):
                if _click_tab(page, tab):
                    _settle(page)
                    snapshot["steps"].append(_capture(page, f"{number:02d}_tab_{slug([tab])}", out_dir))
                else:
                    snapshot["notes"].append(f"Tab '{tab}' not found.")
        finally:
            context.close()
            browser.close()

    path = out_dir / "snapshot.json"
    write_json(path, snapshot)
    return path
