"""Base class for every page object.

It wraps common Playwright actions so page objects stay short and every action
is logged the same way. Page objects hold locators and actions only. Test
assertions belong in the tests.

Playwright waits for elements automatically. Do not add fixed sleeps. When a
screen gives no element to wait for, use ``wait_until`` with a condition.

The application is built from named frames (``divframe``, ``contentframe``,
``bottomframe`` and others). Use ``frame(name)`` to reach content inside them.
"""

import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Frame, Locator, Page

from gridzee_qa.core.config_loader import PROJECT_ROOT, Config
from gridzee_qa.core.exceptions import WaitTimeoutError
from gridzee_qa.core.logger import get_logger

SCREENSHOT_DIR = PROJECT_ROOT / "reports" / "screenshots"

T = TypeVar("T")


class BasePage:
    def __init__(self, page: Page, config: Config) -> None:
        self.page = page
        self.config = config
        self.log = get_logger(type(self).__name__)

    # --- navigation -------------------------------------------------------
    def goto(self, url_or_path: str) -> None:
        """Open a full URL, or a path relative to the environment's base URL."""
        if url_or_path.startswith(("http://", "https://")):
            url = url_or_path
        else:
            url = f"{self.config.base_url.rstrip('/')}/{url_or_path.lstrip('/')}"
        self.log.info("Open %s", url)
        self.page.goto(url)

    def wait_for_url(self, pattern: str | re.Pattern[str]) -> None:
        self.log.info("Wait for URL %s", pattern)
        self.page.wait_for_url(pattern)

    # --- frames and waiting -----------------------------------------------
    def frame(self, name: str, url_part: str | None = None, timeout_ms: int | None = None) -> Frame:
        """Return the frame called ``name``, optionally only once its URL contains ``url_part``."""

        def find() -> Frame | None:
            frame = self.page.frame(name=name)
            if frame is None or frame.is_detached():
                return None
            if url_part and url_part not in frame.url:
                return None
            return frame

        detail = f" with URL containing '{url_part}'" if url_part else ""
        return self.wait_until(find, timeout_ms, f"frame '{name}'{detail}")

    def wait_until(
        self,
        condition: Callable[[], T | None],
        timeout_ms: int | None = None,
        description: str = "condition",
        interval_ms: int = 250,
    ) -> T:
        """Poll ``condition`` until it returns something other than ``None`` or ``False``.

        Errors from frames that reload while polling are ignored until the time limit.
        """
        timeout = timeout_ms or self.config.timeouts.default_ms
        deadline = time.monotonic() + timeout / 1000
        last_error: Exception | None = None
        while True:
            try:
                result = condition()
                if result is not None and result is not False:
                    return result
            except PlaywrightError as error:
                last_error = error
            if time.monotonic() >= deadline:
                raise WaitTimeoutError(f"Timed out after {timeout} ms waiting for {description}.") from last_error
            self.page.wait_for_timeout(interval_ms)

    # --- elements ---------------------------------------------------------
    def locator(self, selector: str) -> Locator:
        return self.page.locator(selector)

    def click(self, selector: str) -> None:
        self.log.info("Click %s", selector)
        self.locator(selector).click()

    def fill(self, selector: str, value: str) -> None:
        # The value is not logged on purpose: it may be a password.
        self.log.info("Fill %s", selector)
        self.locator(selector).fill(value)

    def press(self, selector: str, key: str) -> None:
        self.log.info("Press %s on %s", key, selector)
        self.locator(selector).press(key)

    def get_text(self, selector: str) -> str:
        return self.locator(selector).inner_text()

    def is_visible(self, selector: str) -> bool:
        return self.locator(selector).is_visible()

    def wait_for_visible(self, selector: str) -> None:
        self.log.info("Wait for visible %s", selector)
        self.locator(selector).wait_for(state="visible")

    def wait_for_hidden(self, selector: str) -> None:
        self.log.info("Wait for hidden %s", selector)
        self.locator(selector).wait_for(state="hidden")

    # --- evidence ---------------------------------------------------------
    def screenshot(self, name: str) -> Path:
        """Save a screenshot to reports/screenshots/<name>.png and return its path."""
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name)
        path = SCREENSHOT_DIR / f"{safe_name}.png"
        self.page.screenshot(path=str(path))
        self.log.info("Screenshot saved to %s", path)
        return path
