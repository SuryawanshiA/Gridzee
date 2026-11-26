"""Bottom toolbar (frame ``bottomframe``).

On overview screens it holds New, Reset, the exports, the search box and paging.
On add/edit forms it holds Back, Save and Reset.
"""

import re
from dataclasses import dataclass

from playwright.sync_api import Download, Frame, Locator

from gridzee_qa.core.base_component import BaseComponent


@dataclass(frozen=True)
class RecordCounter:
    """The ``start-end (total)`` counter, for example ``1-47 (47)``."""

    start: int
    end: int
    total: int


class BottomToolbar(BaseComponent):
    FRAME = "bottomframe"

    NEW = "a[title='New']"
    SAVE = "a[title='Save']"
    BACK = "a[title='Back']"
    RESET = "a[title='Reset']"
    EXCEL = "#bottomFrame_excelDownloadIcon"
    PDF = "#bottomFrame_pdfDownloadIcon"
    CSV = "#bottomFrame_csvDownloadIcon"
    SEARCH_FIELD = "select[name='searchfield']"
    SEARCH_TERM = "input[name='searchterm']"
    SEARCH_BUTTON = "a.bt-bottomsearch"
    PAGE_SIZE = "select#recordsperpages"
    PAGE_NUMBER = "select#pagecounter"
    PREVIOUS = "#F1"
    NEXT = "#F2"
    COUNTER_START = "#srtrec"
    COUNTER_END = "#cntrec"
    COUNTER_TOTAL = "#totrec"

    OVERVIEW_CONTROLS = {
        "New": NEW,
        "Reset": RESET,
        "Excel": EXCEL,
        "PDF": PDF,
        "CSV": CSV,
        "Search field": SEARCH_FIELD,
        "Search term": SEARCH_TERM,
        "Search button": SEARCH_BUTTON,
    }
    _DOWNLOADS = {"excel": EXCEL, "pdf": PDF, "csv": CSV}

    def _bar(self) -> Frame:
        return self.frame(self.FRAME)

    def _control(self, selector: str) -> Locator:
        return self._bar().locator(selector).locator("visible=true").first

    def _click(self, selector: str, name: str) -> None:
        self.log.info("Toolbar: %s", name)
        self._control(selector).click()

    # --- buttons ------------------------------------------------------------
    def click_new(self) -> None:
        self._click(self.NEW, "New")

    def click_save(self) -> None:
        self._click(self.SAVE, "Save")

    def click_back(self) -> None:
        self._click(self.BACK, "Back")

    def click_reset(self) -> None:
        self._click(self.RESET, "Reset")

    def is_control_visible(self, selector: str) -> bool:
        return self._bar().locator(selector).locator("visible=true").count() > 0

    def is_new_visible(self) -> bool:
        return self.is_control_visible(self.NEW)

    # --- search -------------------------------------------------------------
    def search_field_options(self) -> list[str]:
        return self._options(self._bar().locator(self.SEARCH_FIELD).first)

    def search(self, field: str, term: str) -> None:
        """Select the search field, type the term and click the search icon."""
        self.log.info("Search '%s' in %s", term, field)
        bar = self._bar()
        bar.locator(self.SEARCH_FIELD).first.select_option(label=field)
        bar.locator(self.SEARCH_TERM).first.fill(term)
        bar.locator(self.SEARCH_BUTTON).first.click()

    # --- paging -------------------------------------------------------------
    def page_size_options(self) -> list[str]:
        return self._options(self._bar().locator(self.PAGE_SIZE).first)

    def page_size(self) -> str:
        return self._bar().locator(self.PAGE_SIZE).first.evaluate("e => e.options[e.selectedIndex].text.trim()")

    def set_page_size(self, size: int) -> None:
        self.log.info("Page size %s", size)
        self._bar().locator(self.PAGE_SIZE).first.select_option(label=str(size))

    def page_number_options(self) -> list[str]:
        return self._options(self._bar().locator(self.PAGE_NUMBER).last)

    def go_to_page(self, number: int) -> None:
        self.log.info("Go to page %s", number)
        self._bar().locator(self.PAGE_NUMBER).last.select_option(label=str(number))

    def click_previous(self) -> None:
        self.log.info("Toolbar: Previous")
        self._bar().locator(self.PREVIOUS).last.click()

    def click_next(self) -> None:
        self.log.info("Toolbar: Next")
        self._bar().locator(self.NEXT).last.click()

    def counter(self) -> RecordCounter:
        return RecordCounter(
            start=self._read_int(self.COUNTER_START),
            end=self._read_int(self.COUNTER_END),
            total=self._read_int(self.COUNTER_TOTAL),
        )

    # --- export -------------------------------------------------------------
    def download(self, kind: str) -> Download:
        """Click an export icon (``excel``, ``pdf`` or ``csv``) and return the download."""
        selector = self._DOWNLOADS[kind]
        self.log.info("Download %s", kind)
        with self.page.expect_download() as info:
            self._bar().locator(selector).first.click()
        return info.value

    # --- helpers ------------------------------------------------------------
    def _read_int(self, selector: str) -> int:
        # The page holds two elements with each counter id; the last one is the visible value.
        text = self._bar().locator(selector).last.inner_text()
        digits = re.sub(r"\D", "", text)
        return int(digits) if digits else 0

    @staticmethod
    def _options(select: Locator) -> list[str]:
        return select.evaluate("e => Array.from(e.options).map(o => o.text.trim())")
