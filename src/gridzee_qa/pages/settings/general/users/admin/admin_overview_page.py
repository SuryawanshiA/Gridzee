"""Admin overview: Settings > General > Users > Admin.

The grid is in frame ``contentframe`` (``Overview.jsp``). Search, paging and
exports are in the bottom toolbar (see ``components/bottom_toolbar.py``).
"""

import re
from dataclasses import dataclass, field

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Frame

from gridzee_qa.core.base_page import BasePage

# Reads the grid. Header text is reduced to letters, digits and spaces, so the
# sort arrow next to "Short Name" is dropped. Data rows are rows with the same
# number of cells as the header.
_GRID_JS = r"""() => {
    const vis = e => !!(e.offsetWidth || e.offsetHeight);
    const cells = tr => Array.from(tr.children).filter(c => c.tagName === 'TD' || c.tagName === 'TH');
    const headerText = c => (c.innerText || '').replace(/[^A-Za-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
    const text = c => (c.innerText || '').replace(/\s+/g, ' ').trim();
    const trs = Array.from(document.querySelectorAll('tr')).filter(vis);
    const headerRows = trs.filter(tr => {
        const t = cells(tr).map(headerText);
        return t.includes('Short Name') && t.includes('User Name');
    });
    const noRecords = trs.some(tr => /No Records Found/i.test(tr.innerText || ''));
    if (!headerRows.length) return {headers: [], rows: [], noRecords};
    const headers = cells(headerRows[headerRows.length - 1]).map(headerText);
    const rows = trs.filter(tr => !headerRows.includes(tr))
        .map(tr => cells(tr).map(text))
        .filter(r => r.length === headers.length);
    return {headers, rows, noRecords};
}"""

_POPUP_JS = r"""(marker) => Array.from(document.querySelectorAll('div, table, section'))
    .filter(e => (e.offsetWidth || e.offsetHeight) && (e.innerText || '').includes(marker))
    .map(e => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .sort((a, b) => a.length - b.length)[0] || null"""


@dataclass(frozen=True)
class GridState:
    headers: list[str]
    rows: list[dict[str, str]] = field(default_factory=list)
    no_records: bool = False

    def column(self, name: str) -> list[str]:
        return [row.get(name, "") for row in self.rows]


class AdminOverviewPage(BasePage):
    CONTENT_FRAME = "contentframe"
    TITLE_FRAME = "titleframe"
    URL_PART = "Overview.jsp"
    SCREEN_MARKER = "nodename=Admin"

    EXPECTED_COLUMNS = [
        "Short Name", "User Name", "Password", "Share", "Application", "User Group", "Mobile No",
        "Last Login Time", "User Time Zone", "Payment Status", "User Status", "Document",
        "Expiry Date", "Extended Date",
    ]
    SHARE_ICON = "a#send_cred_link"
    SHARE_POPUP_MARKER = "Share Credentials"
    TITLE_ICONS = {"Help": "a[title='Help']", "Settings": "a[title='Settings']", "Favorite Report": "a[title='Favorite Report']"}

    def _content(self) -> Frame:
        return self.frame(self.CONTENT_FRAME, self.URL_PART)

    # --- state --------------------------------------------------------------
    def is_loaded(self) -> bool:
        frame = self.page.frame(name=self.CONTENT_FRAME)
        return bool(frame and not frame.is_detached() and self.URL_PART in frame.url)

    def is_admin_screen(self) -> bool:
        return self.SCREEN_MARKER in self._content().url

    def wait_loaded(self) -> None:
        self._content()
        self.wait_until(lambda: self.grid().headers or None, description="the Admin grid")

    def grid(self) -> GridState:
        data = self._content().evaluate(_GRID_JS)
        headers = data["headers"]
        rows = [dict(zip(headers, cells)) for cells in data["rows"]]
        return GridState(headers=headers, rows=rows, no_records=data["noRecords"])

    def wait_for_grid(self, condition, description: str, timeout_ms: int | None = None) -> GridState:
        """Wait until ``condition(grid)`` is true and return that grid."""

        def check() -> GridState | None:
            grid = self.grid()
            return grid if condition(grid) else None

        return self.wait_until(check, timeout_ms or self.config.timeouts.expect_ms, description)

    # --- row actions --------------------------------------------------------
    def open_row(self, text: str) -> None:
        """Double-click the row that contains ``text`` to open it in edit mode."""
        self.log.info("Open row %s", text)
        self._content().locator("tr").filter(has_text=text).last.dblclick()

    def click_share(self, row_index: int = 0) -> None:
        self.log.info("Click share icon of row %s", row_index)
        self._content().locator(self.SHARE_ICON).nth(row_index).click()

    def share_popup_text(self) -> str:
        def find() -> str | None:
            for frame in self.page.frames:
                try:
                    text = frame.evaluate(_POPUP_JS, self.SHARE_POPUP_MARKER)
                except PlaywrightError:
                    continue
                if text:
                    return text
            return None

        return self.wait_until(find, self.config.timeouts.expect_ms, "the Share Credentials popup")

    def close_popup(self) -> None:
        self.page.keyboard.press("Escape")

    def click_column_header(self, name: str) -> None:
        self.log.info("Click column header %s", name)
        header = self._content().locator("th, td").filter(has_text=re.compile(rf"^\s*{re.escape(name)}\W*$"))
        header.locator("visible=true").first.click()

    def is_title_icon_visible(self, name: str) -> bool:
        frame = self.frame(self.TITLE_FRAME)
        return frame.locator(self.TITLE_ICONS[name]).locator("visible=true").count() > 0
