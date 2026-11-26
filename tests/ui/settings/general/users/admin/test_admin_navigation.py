"""Group A: navigation and overview (read-only). ADM-001 to ADM-006."""

import pytest

from gridzee_qa.components.bottom_toolbar import BottomToolbar
from gridzee_qa.flows.settings.general.users.admin_flow import AdminFlow
from gridzee_qa.pages.settings.general.users.admin.admin_overview_page import AdminOverviewPage

pytestmark = [pytest.mark.ui, pytest.mark.admin]

USERS_SUBMENU = ["Super Admin", "Admin", "Reseller", "Company", "Sub Users", "Branch"]


@pytest.mark.smoke
def test_adm_001_open_admin_overview_from_menu(admin_flow_at_home: AdminFlow) -> None:
    admin_flow_at_home.open_overview()

    assert admin_flow_at_home.overview.is_admin_screen()
    assert admin_flow_at_home.overview.grid().headers


@pytest.mark.regression
def test_adm_002_users_submenu_lists_all_user_types(admin_flow_at_home: AdminFlow) -> None:
    admin_flow_at_home.open_users_menu()

    entries = admin_flow_at_home.menu.visible_entries()
    missing = [item for item in USERS_SUBMENU if item not in entries]
    assert not missing, f"Missing from the Users submenu: {missing}"


@pytest.mark.regression
def test_adm_003_grid_shows_expected_columns(admin_flow: AdminFlow) -> None:
    headers = [h for h in admin_flow.overview.grid().headers if h]

    assert headers == AdminOverviewPage.EXPECTED_COLUMNS


@pytest.mark.regression
def test_adm_004_default_sort_is_short_name_ascending(admin_flow: AdminFlow) -> None:
    names = admin_flow.overview.grid().column("Short Name")

    assert names, "The grid has no rows."
    assert names == sorted(names, key=str.casefold)


@pytest.mark.sanity
def test_adm_005_record_counter_matches_grid(admin_flow: AdminFlow) -> None:
    counter = admin_flow.toolbar.counter()
    rows = admin_flow.overview.grid().rows

    assert counter.start == 1
    assert len(rows) == counter.end - counter.start + 1
    assert counter.end <= counter.total


@pytest.mark.regression
def test_adm_006_bottom_toolbar_icons_are_present(admin_flow: AdminFlow) -> None:
    missing = [
        name for name, selector in BottomToolbar.OVERVIEW_CONTROLS.items()
        if not admin_flow.toolbar.is_control_visible(selector)
    ]

    assert not missing, f"Missing toolbar controls: {missing}"
