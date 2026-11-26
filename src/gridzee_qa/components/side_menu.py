"""Left sidebar menu (frame ``divframe``).

Main entries (Dashboard, Reports, Charts, Settings) are buttons. Clicking one
opens a flyout; each further level opens on click.

Example: ``SideMenu(page, config).navigate("Settings", "General", "Users", "Admin")``
"""

from gridzee_qa.core.base_component import BaseComponent

_VISIBLE_ENTRIES_JS = r"""() => Array.from(document.querySelectorAll('a, span, li'))
    .filter(e => e.children.length === 0 && (e.offsetWidth || e.offsetHeight))
    .map(e => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter(t => t && t.length < 60)"""


class SideMenu(BaseComponent):
    FRAME = "divframe"

    def navigate(self, main: str, *items: str) -> None:
        """Click a main entry, then each submenu entry in order."""
        menu = self.frame(self.FRAME)
        self.log.info("Menu: %s", " > ".join((main, *items)))
        menu.locator(f"button:has-text('{main}')").first.click()
        for item in items:
            menu.get_by_text(item, exact=True).locator("visible=true").first.click()

    def visible_entries(self) -> list[str]:
        """Texts of the menu entries currently shown."""
        return list(dict.fromkeys(self.frame(self.FRAME).evaluate(_VISIBLE_ENTRIES_JS)))
