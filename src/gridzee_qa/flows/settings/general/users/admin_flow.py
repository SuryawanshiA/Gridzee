"""Business steps for Settings > General > Users > Admin.

Combines the side menu, the Admin overview, the Admin form, the bottom toolbar
and the message box. Holds no locators.
"""

from collections.abc import Callable

from playwright.sync_api import Page

from gridzee_qa.components.bottom_toolbar import BottomToolbar
from gridzee_qa.components.message_box import MessageBox
from gridzee_qa.components.side_menu import SideMenu
from gridzee_qa.core.config_loader import Config
from gridzee_qa.factories.admin_factory import AdminData
from gridzee_qa.pages.settings.general.users.admin.admin_form_page import AdminFormPage
from gridzee_qa.pages.settings.general.users.admin.admin_overview_page import AdminOverviewPage, GridState

MENU_PATH = ("Settings", "General", "Users", "Admin")
USERS_MENU_PATH = ("Settings", "General", "Users")


class AdminFlow:
    def __init__(self, page: Page, config: Config) -> None:
        self.page = page
        self.config = config
        self.menu = SideMenu(page, config)
        self.toolbar = BottomToolbar(page, config)
        self.messages = MessageBox(page, config)
        self.overview = AdminOverviewPage(page, config)
        self.form = AdminFormPage(page, config)

    # --- navigation ---------------------------------------------------------
    def open_overview(self) -> None:
        self.menu.navigate(*MENU_PATH)
        self.overview.wait_loaded()

    def open_users_menu(self) -> None:
        self.menu.navigate(*USERS_MENU_PATH)

    def open_add_form(self) -> None:
        self.toolbar.click_new()
        self.form.wait_loaded("insert")

    def open_edit_form(self, short_name: str) -> None:
        self.overview.open_row(short_name)
        self.form.wait_loaded("update")

    def back_to_overview(self) -> None:
        self.toolbar.click_back()
        self.overview.wait_loaded()

    # --- form ---------------------------------------------------------------
    def fill_my_account(self, admin: AdminData, include_optional: bool = False, skip: tuple[str, ...] = ()) -> None:
        values = dict(admin.mandatory_fields())
        if include_optional:
            values.update({k: v for k, v in admin.optional_fields().items() if v})
        self.form.set_fields({k: v for k, v in values.items() if k not in skip})

    def save(self) -> str | None:
        """Click Save. Return the validation message, or ``None`` if the form was saved."""
        self.toolbar.click_save()

        def outcome() -> tuple[str, str | None] | None:
            message = self.messages.current_message()
            if message:
                return ("message", message)
            if self.overview.is_loaded():
                return ("saved", None)
            return None

        _, message = self.form.wait_until(outcome, description="a validation message or the Admin overview")
        return message

    def save_expecting_message(self) -> str:
        """Save on a form that must not be accepted. Fails loudly if it was saved."""
        message = self.save()
        if message is None:
            raise AssertionError("The form was saved, but a validation message was expected. A record may have been created.")
        return message

    def create_admin(self, admin: AdminData, include_optional: bool = False) -> AdminData:
        """Open the add form, fill My Account, save and return to the overview."""
        self.open_add_form()
        self.fill_my_account(admin, include_optional=include_optional)
        message = self.save()
        if message:
            raise AssertionError(f"Admin '{admin.short_name}' was not created: {message}")
        self.overview.wait_loaded()
        return admin

    # --- search -------------------------------------------------------------
    def search(
        self,
        field: str,
        term: str,
        row_matches: Callable[[dict[str, str]], bool],
        allow_empty: bool = False,
    ) -> GridState:
        """Search and wait until every row matches, or until "No Records Found" if allowed."""
        self.toolbar.search(field, term)

        def done(grid: GridState) -> bool:
            if grid.no_records:
                return allow_empty
            return bool(grid.rows) and all(row_matches(row) for row in grid.rows)

        return self.overview.wait_for_grid(done, f"search results for '{term}' in {field}")

    def find_by_short_name(self, short_name: str) -> list[dict[str, str]]:
        grid = self.search("Short Name", short_name, lambda row: row.get("Short Name") == short_name, allow_empty=True)
        return grid.rows

    def find_by_username(self, username: str) -> list[dict[str, str]]:
        target = username.casefold()
        grid = self.search("User Name", username, lambda row: row.get("User Name", "").casefold() == target, allow_empty=True)
        return grid.rows

    def search_without_results(self, field: str, term: str) -> GridState:
        return self.search(field, term, lambda row: False, allow_empty=True)

    def reset_search(self, expected_total: int) -> None:
        self.toolbar.click_reset()
        self.toolbar.wait_until(
            lambda: self.toolbar.counter().total == expected_total,
            self.config.timeouts.expect_ms,
            f"the full list of {expected_total} records",
        )
