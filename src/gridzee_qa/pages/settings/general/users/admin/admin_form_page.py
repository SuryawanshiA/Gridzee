"""Admin add/edit form: Settings > General > Users > Admin > New (+) or a row double-click.

The form is in frame ``contentframe`` (``DetailScreen.jsp``), with ``mode=insert``
for a new admin and ``mode=update`` for an existing one. Back, Save and Reset are
in the bottom toolbar.

Text fields are read-only until clicked, so ``set_field`` clicks before typing.
Dropdowns are "chosen" widgets: a text input that opens a list of ``li`` items.
"""

import re

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Frame, Locator

from gridzee_qa.core.base_page import BasePage

# Marks the first visible element matching ``target`` that follows a label whose
# text matches ``pattern``. Used for dropdowns that have no name attribute.
_MARK_AFTER_LABEL_JS = r"""(arg) => {
    const norm = s => (s || '').replace(/\s+/g, ' ').trim();
    const vis = e => !!(e.offsetWidth || e.offsetHeight);
    const re = new RegExp(arg.pattern, 'i');
    const labels = Array.from(document.querySelectorAll('td, th, label, span, div, b'))
        .filter(e => e.children.length <= 2 && vis(e) && norm(e.innerText).length < 60 && re.test(norm(e.innerText)));
    if (!labels.length) return false;
    const label = labels[labels.length - 1];
    const next = Array.from(document.querySelectorAll(arg.target)).filter(vis)
        .find(t => label.compareDocumentPosition(t) & Node.DOCUMENT_POSITION_FOLLOWING);
    if (!next) return false;
    document.querySelectorAll('[data-qa-target]').forEach(e => e.removeAttribute('data-qa-target'));
    next.setAttribute('data-qa-target', '1');
    return true;
}"""

_LABEL_OF_FIELD_JS = r"""(name) => {
    const e = document.querySelector(`[name="${name}"]`);
    const row = e && (e.closest('tr') || e.parentElement);
    return row ? (row.innerText || '').split('\n')[0].replace(/\s+/g, ' ').trim() : null;
}"""

_TOOLTIP_JS = r"""() => Array.from(document.querySelectorAll("[role='tooltip'], .tooltip, .popover, [class*='tooltip' i]"))
    .filter(e => e.offsetWidth || e.offsetHeight)
    .map(e => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter(Boolean)[0] || null"""


class AdminFormPage(BasePage):
    CONTENT_FRAME = "contentframe"
    URL_PART = "DetailScreen.jsp"
    TARGET = "[data-qa-target='1']"

    TABS = [
        "My Account", "Rule", "User Setting", "Screen Access", "Data Access", "Map", "Email", "SMS",
        "Payment Gateway", "Rename Label", "IVR", "White Label", "ChatBot", "Social Media API",
        "Document", "Authentication", "SSO (Single Sign On)",
    ]

    # Field names on the My Account tab
    SHORT_NAME = "short_name"
    USERNAME = "username"
    CONFIRM_USERNAME = "confirm_username"
    PASSWORD = "password_value"
    RETYPE_PASSWORD = "retype_password"
    DATA_STORAGE = "data_storage"
    ADMIN_CODE = "admin_code"

    MANDATORY_FIELDS = [SHORT_NAME, USERNAME, CONFIRM_USERNAME, PASSWORD, RETYPE_PASSWORD, DATA_STORAGE, ADMIN_CODE]

    # Max lengths observed on the form (maxlength attribute)
    MAX_LENGTHS = {
        "short_name": 50, "username": 70, "password_value": 50, "retype_password": 50, "city": 30,
        "zipcode": 10, "street1": 50, "street2": 50, "internet_address": 50, "contact_person": 50,
        "tel_no": 20, "mob_no": 20, "whatsapp_contact_number": 20, "fax_no": 20, "welcome_msg": 200,
        "data_storage": 3,
    }

    # Checkbox and radio ids, with their default state
    CHECKBOX_DEFAULTS = {
        "license_type_1": True,  # License Type: Tariff
        "auto_suggest_imei_1": True,
        "is_disable_1": False,
        "inventory_1": False,
        "kyc_1": False,
        "enable_security_pin_1": False,
        "email_login_details_1": False,  # Share Credentials Via: Email
        "email_login_details_2": False,  # Share Credentials Via: SMS
    }
    CALLING_CODE = "select#calling_code"

    EYE_ICON = "[class*='eye' i]:not(input), [onclick*='assword' i]:not(input), img[src*='eye' i]"
    INFO_ICON = "[class*='info' i]:not(input), img[src*='info' i], [data-toggle='tooltip']"

    def _form(self) -> Frame:
        return self.frame(self.CONTENT_FRAME, self.URL_PART)

    # --- state --------------------------------------------------------------
    def wait_loaded(self, mode: str = "insert") -> None:
        frame = self.frame(self.CONTENT_FRAME, f"mode={mode}")
        frame.locator(f"input[name='{self.SHORT_NAME}']").wait_for(state="attached")

    def mode(self) -> str | None:
        match = re.search(r"mode=(\w+)", self._form().url)
        return match.group(1) if match else None

    # --- tabs ---------------------------------------------------------------
    def open_tab(self, name: str) -> None:
        self.log.info("Open tab %s", name)
        self._form().get_by_text(name, exact=True).first.click()

    def is_tab_visible(self, name: str) -> bool:
        return self._form().get_by_text(name, exact=True).first.is_visible()

    # --- fields -------------------------------------------------------------
    def field(self, name: str) -> Locator:
        return self._form().locator(f"[name='{name}']").first

    def set_field(self, name: str, value: str) -> None:
        # Values are not logged: the field may hold a password.
        self.log.info("Set field %s", name)
        locator = self.field(name)
        locator.click()
        locator.fill(value)

    def set_fields(self, values: dict[str, str]) -> None:
        for name, value in values.items():
            self.set_field(name, value)

    def value(self, name: str) -> str:
        return self.field(name).input_value()

    def placeholder(self, name: str) -> str | None:
        return self.field(name).get_attribute("placeholder")

    def label(self, name: str) -> str | None:
        """Label text of a field, for example ``Short Name* :``."""
        return self._form().evaluate(_LABEL_OF_FIELD_JS, name)

    def is_checked(self, element_id: str) -> bool:
        return self._form().locator(f"#{element_id}").is_checked()

    def calling_code(self) -> str:
        return self._form().locator(self.CALLING_CODE).input_value()

    # --- dropdowns (chosen widgets) -----------------------------------------
    def _mark_after_label(self, label: str, target: str) -> Locator:
        pattern = rf"^{re.escape(label)}\s*\*?\s*:?\s*$"
        found = self._form().evaluate(_MARK_AFTER_LABEL_JS, {"pattern": pattern, "target": target})
        if not found:
            raise LookupError(f"No '{target}' found after the label '{label}'.")
        return self._form().locator(self.TARGET)

    def choose(self, label: str, option: str) -> None:
        """Open the dropdown next to ``label`` and pick ``option``."""
        self.log.info("Choose %s = %s", label, option)
        self._mark_after_label(label, "input.chosen-focus-input, input.chosen-search-input").click()
        items = self._form().locator("li").filter(has_text=re.compile(rf"^\s*{re.escape(option)}\s*$"))
        items.locator("visible=true").first.click()

    def dropdown_text(self, label: str) -> str:
        """Text currently shown in the dropdown next to ``label``."""
        text = self._mark_after_label(label, ".chosen-container").inner_text()
        return text.strip().split("\n")[0].strip()

    # --- password helpers ---------------------------------------------------
    def _password_row(self) -> Locator:
        form = self._form()
        return form.locator("tr").filter(has=form.locator(f"input[name='{self.PASSWORD}']")).last

    def password_input_type(self) -> str | None:
        return self.field(self.PASSWORD).get_attribute("type")

    def toggle_password_visibility(self) -> None:
        self.log.info("Toggle password visibility")
        self._password_row().locator(self.EYE_ICON).first.click()

    def password_info_text(self) -> str:
        """Hover the info icon next to Password and return the help text."""
        icon = self._password_row().locator(self.INFO_ICON).first
        icon.hover()
        for attribute in ("title", "data-original-title", "data-content", "data-title"):
            value = icon.get_attribute(attribute)
            if value and value.strip():
                return value.strip()

        def tooltip() -> str | None:
            for frame in self.page.frames:
                try:
                    text = frame.evaluate(_TOOLTIP_JS)
                except PlaywrightError:
                    continue
                if text:
                    return text
            return None

        return self.wait_until(tooltip, self.config.timeouts.expect_ms, "the password info tooltip")
