"""Groups C and D: paging and sorting (read-only). ADM-020 to ADM-025."""

import math

import pytest

from gridzee_qa.flows.settings.general.users.admin_flow import AdminFlow

pytestmark = [pytest.mark.ui, pytest.mark.admin]

PAGE_SIZES = ["10", "20", "30", "40", "50", "100", "200", "300", "400", "500", "1000"]


def set_page_size_10(admin_flow: AdminFlow) -> int:
    total = admin_flow.toolbar.counter().total
    if total <= 10:
        pytest.skip(f"Paging needs more than 10 admins; QA has {total}.")
    admin_flow.toolbar.set_page_size(10)
    admin_flow.toolbar.wait_until(lambda: admin_flow.toolbar.counter().end == 10, description="10 records per page")
    return total


@pytest.mark.regression
def test_adm_020_records_per_page_options(admin_flow: AdminFlow) -> None:
    assert admin_flow.toolbar.page_size_options() == PAGE_SIZES
    assert admin_flow.toolbar.page_size() == "1000"


@pytest.mark.regression
def test_adm_021_page_size_10(admin_flow: AdminFlow) -> None:
    total = set_page_size_10(admin_flow)

    counter = admin_flow.toolbar.counter()
    assert (counter.start, counter.end, counter.total) == (1, 10, total)
    assert len(admin_flow.toolbar.page_number_options()) == math.ceil(total / 10)


@pytest.mark.regression
def test_adm_022_go_to_page_2(admin_flow: AdminFlow) -> None:
    total = set_page_size_10(admin_flow)
    page_1 = set(admin_flow.overview.grid().column("Short Name"))

    admin_flow.toolbar.go_to_page(2)
    admin_flow.toolbar.wait_until(lambda: admin_flow.toolbar.counter().start == 11, description="page 2")

    counter = admin_flow.toolbar.counter()
    assert (counter.start, counter.end, counter.total) == (11, min(20, total), total)
    page_2 = set(admin_flow.overview.grid().column("Short Name"))
    assert page_2 and not page_1 & page_2


@pytest.mark.regression
def test_adm_023_previous_and_next_icons(admin_flow: AdminFlow) -> None:
    set_page_size_10(admin_flow)

    admin_flow.toolbar.click_next()
    admin_flow.toolbar.wait_until(lambda: admin_flow.toolbar.counter().start > 1, description="a later page")
    later_start = admin_flow.toolbar.counter().start

    admin_flow.toolbar.click_previous()
    admin_flow.toolbar.wait_until(lambda: admin_flow.toolbar.counter().start < later_start, description="an earlier page")


@pytest.mark.regression
def test_adm_025_sort_by_user_name(admin_flow: AdminFlow) -> None:
    """Header click did not respond during exploration. This test confirms the behavior."""
    overview = admin_flow.overview

    overview.click_column_header("User Name")
    ascending = overview.wait_for_grid(
        lambda g: (n := g.column("User Name")) == sorted(n, key=str.casefold), "User Name ascending"
    )
    overview.click_column_header("User Name")
    descending = overview.wait_for_grid(
        lambda g: (n := g.column("User Name")) == sorted(n, key=str.casefold, reverse=True)
        and n != ascending.column("User Name"),
        "User Name descending",
    )

    assert descending.rows
