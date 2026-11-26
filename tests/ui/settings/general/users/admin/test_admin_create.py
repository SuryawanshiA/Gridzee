"""Group H: create admin (creates data on QA). ADM-070 to ADM-076.

Every test here is marked ``creates_data``. These tests never run on demo.
Run only the read-only Admin tests with: ``pytest -m "admin and not creates_data"``.

The admin created by ADM-070 is reused by the later tests in the same run and
stored in ``.auth/created_admins.json`` for later login automation.
"""

import re
from collections.abc import Callable

import pytest
from playwright.sync_api import expect

from gridzee_qa.core.config_loader import Config
from gridzee_qa.factories.admin_factory import AdminData, AdminFactory
from gridzee_qa.flows.auth_flow import AuthFlow
from gridzee_qa.flows.settings.general.users.admin_flow import AdminFlow
from gridzee_qa.pages.auth.login_page import LoginPage

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.creates_data]


@pytest.mark.smoke
def test_adm_070_create_admin_with_mandatory_fields(
    admin_flow: AdminFlow, admin_factory: AdminFactory, remember_admin: Callable[[AdminData], None]
) -> None:
    admin = admin_factory.build()

    admin_flow.create_admin(admin)
    remember_admin(admin)

    rows = admin_flow.find_by_short_name(admin.short_name)
    assert len(rows) == 1, f"Expected exactly 1 row for {admin.short_name}, found {len(rows)}"
    assert rows[0]["User Name"] == admin.username
    assert rows[0]["User Status"] == "Active"


@pytest.mark.regression
def test_adm_071_create_admin_with_all_my_account_fields(admin_flow: AdminFlow, admin_factory: AdminFactory) -> None:
    admin = admin_factory.build()

    admin_flow.create_admin(admin, include_optional=True)
    assert len(admin_flow.find_by_short_name(admin.short_name)) == 1
    admin_flow.open_edit_form(admin.short_name)

    form = admin_flow.form
    mismatches = {
        name: (expected, form.value(name))
        for name, expected in admin.optional_fields().items()
        if form.value(name) != expected
    }
    admin_flow.back_to_overview()
    assert not mismatches, f"Saved values differ (expected, shown): {mismatches}"


@pytest.mark.smoke
def test_adm_072_duplicate_user_name_is_rejected(
    admin_flow: AdminFlow, admin_factory: AdminFactory, created_admin: AdminData
) -> None:
    duplicate = admin_factory.build(username=created_admin.username)

    admin_flow.open_add_form()
    admin_flow.fill_my_account(duplicate)
    message = admin_flow.save_expecting_message()
    admin_flow.back_to_overview()

    assert message
    assert len(admin_flow.find_by_username(created_admin.username)) == 1


@pytest.mark.regression
@pytest.mark.parametrize("field", ["short_name", "admin_code"])
def test_adm_073_duplicate_short_name_or_admin_code(
    admin_flow: AdminFlow, admin_factory: AdminFactory, created_admin: AdminData, field: str
) -> None:
    """Expected behavior is to be confirmed (open question). This test expects a rejection."""
    duplicate = admin_factory.build(**{field: getattr(created_admin, field)})

    admin_flow.open_add_form()
    admin_flow.fill_my_account(duplicate)
    message = admin_flow.save_expecting_message()
    admin_flow.back_to_overview()

    assert message


@pytest.mark.regression
def test_adm_074_edit_view_shows_saved_data(admin_flow: AdminFlow, created_admin: AdminData) -> None:
    assert len(admin_flow.find_by_short_name(created_admin.short_name)) == 1

    admin_flow.open_edit_form(created_admin.short_name)
    form = admin_flow.form
    shown = {
        "mode": form.mode(),
        "short_name": form.value("short_name"),
        "username": form.value("username"),
        "admin_code": form.value("admin_code"),
        "password_value": form.value("password_value"),
        "retype_password": form.value("retype_password"),
    }
    admin_flow.back_to_overview()

    assert shown == {
        "mode": "update",
        "short_name": created_admin.short_name,
        "username": created_admin.username,
        "admin_code": created_admin.admin_code,
        "password_value": "",
        "retype_password": "",
    }


@pytest.mark.smoke
def test_adm_075_created_admin_can_log_in(created_admin: AdminData, new_context, config: Config) -> None:
    context = new_context()
    page = context.new_page()
    page.set_default_timeout(config.timeouts.default_ms)
    page.set_default_navigation_timeout(config.timeouts.navigation_ms)

    AuthFlow(LoginPage(page, config), config).login_with(created_admin.username, created_admin.password)

    expect(page).to_have_url(re.compile(r"/jsp/index\.html"))


@pytest.mark.regression
@pytest.mark.skip(reason="Pending decision (open question 5): Save does not enforce the Data Access fields marked mandatory.")
def test_adm_076_data_access_mandatory_fields() -> None:
    """Will assert the agreed behavior once it is confirmed."""
