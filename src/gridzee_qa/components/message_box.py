"""Validation and information message box (``.jalert-parent``) with a Close button.

The application shows one message at a time. The box can appear in any frame,
so every frame is checked.
"""

import re

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator

from gridzee_qa.core.base_component import BaseComponent


class MessageBox(BaseComponent):
    BOX = ".jalert-parent"
    CLOSE_TEXT = "Close"

    def _visible_boxes(self) -> list[Locator]:
        boxes = []
        for frame in self.page.frames:
            try:
                found = frame.locator(self.BOX).locator("visible=true")
                boxes.extend(found.nth(i) for i in range(found.count()))
            except PlaywrightError:
                continue  # frame is reloading
        return boxes

    def current_message(self) -> str | None:
        """Text of the visible message without the Close label, or ``None``."""
        for box in self._visible_boxes():
            try:
                return self._clean(box.inner_text())
            except PlaywrightError:
                continue
        return None

    def wait_for_message(self, timeout_ms: int | None = None) -> str:
        return self.wait_until(self.current_message, timeout_ms or self.config.timeouts.expect_ms, "a message box")

    def visible_count(self) -> int:
        return len(self._visible_boxes())

    def close(self) -> None:
        boxes = self._visible_boxes()
        if not boxes:
            return
        self.log.info("Close message box")
        boxes[0].get_by_text(self.CLOSE_TEXT, exact=True).first.click()
        self.wait_until(lambda: self.visible_count() == 0, self.config.timeouts.expect_ms, "the message box to close")

    @classmethod
    def _clean(cls, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        return re.sub(rf"\s*{cls.CLOSE_TEXT}$", "", text).strip()
