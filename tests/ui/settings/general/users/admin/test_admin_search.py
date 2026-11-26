"""Group B: search (read-only). ADM-010 to ADM-018.

Search terms are taken from the rows currently in the grid, so no data is hard-coded.
"""

import pytest

from gridzee_qa.factories.admin_factory import AdminFactory
from gridzee_qa.flows.settings.general.users.admin_flow import AdminFlow

pytestmark = [pytest.mark.ui, pytest.mark.admin]

SEARCH_FIELDS = ["All", "Short Name", "User Name", "Application", "User Group", "Email", "Mobile"]
EMPTY_VALUES = {"", "--"}


def first_row_with(admin_flow: AdminFlow, column: str) -> dict[str, str]:
    for row in admin_flow.overview.grid().rows:
        if row.get(column, "").strip() not in EMPTY_VALUES:
            return row
    pytest.skip(f"No admin in the grid has a value in '{column}'.")


def contains(row: dict[str, str], column: str, term: str) -> bool:
    return term.casefold() in row.get(column, "").casefold()


@pytest.mark.regression
def test_adm_010_search_field_list_has_all_options(admin_flow: AdminFlow) -> None:
    assert admin_flow.toolbar.search_field_options() == SEARCH_FIELDS


@pytest.mark.smoke
def test_adm_011_search_by_short_name(admin_flow: AdminFlow) -> None:
    term = first_row_with(admin_flow, "Short Name")["Short Name"]

    grid = admin_flow.search("Short Name", term, lambda row: contains(row, "Short Name", term))

    assert admin_flow.toolbar.counter().total == len(grid.rows)


@pytest.mark.smoke
def test_adm_012_search_by_user_name(admin_flow: AdminFlow) -> None:
    term = first_row_with(admin_flow, "User Name")["User Name"]

    grid = admin_flow.search("User Name", term, lambda row: contains(row, "User Name", term))

    assert admin_flow.toolbar.counter().total == len(grid.rows)


@pytest.mark.regression
def test_adm_013_search_with_all(admin_flow: AdminFlow) -> None:
    term = first_row_with(admin_flow, "Short Name")["Short Name"]

    grid = admin_flow.search("All", term, lambda row: any(term.casefold() in v.casefold() for v in row.values()))

    assert grid.rows


@pytest.mark.regression
def test_adm_014_partial_text_matches(admin_flow: AdminFlow) -> None:
    username = first_row_with(admin_flow, "User Name")["User Name"]
    local_part = username.split("@")[0]
    term = local_part[:4] if len(local_part) >= 4 else local_part

    grid = admin_flow.search("User Name", term, lambda row: contains(row, "User Name", term))

    assert any(row["User Name"].casefold() == username.casefold() for row in grid.rows)


@pytest.mark.regression
def test_adm_015_search_is_case_insensitive(admin_flow: AdminFlow) -> None:
    total = admin_flow.toolbar.counter().total
    term = first_row_with(admin_flow, "Short Name")["Short Name"]
    original = admin_flow.search("Short Name", term, lambda row: contains(row, "Short Name", term))
    # Back to the full list, so the next result cannot be the previous search's grid.
    admin_flow.reset_search(total)

    result = admin_flow.search("Short Name", term.swapcase(), lambda row: contains(row, "Short Name", term))

    assert len(result.rows) == len(original.rows)


@pytest.mark.regression
@pytest.mark.parametrize(
    ("field", "column"),
    [("User Group", "User Group"), ("Mobile", "Mobile No"), ("Application", "Application"), ("Email", "User Name")],
)
def test_adm_016_search_by_other_fields(admin_flow: AdminFlow, field: str, column: str) -> None:
    value = first_row_with(admin_flow, column)[column]
    term = value.split(",")[0].strip() if column == "Application" else value

    grid = admin_flow.search(field, term, lambda row: contains(row, column, term))

    assert grid.rows


@pytest.mark.regression
def test_adm_017_no_match_shows_no_records(admin_flow: AdminFlow, admin_factory: AdminFactory) -> None:
    term = f"no_such_admin_{admin_factory.token()}"

    grid = admin_flow.search_without_results("All", term)

    assert grid.no_records
    counter = admin_flow.toolbar.counter()
    assert (counter.start, counter.end, counter.total) == (0, 0, 0)


@pytest.mark.regression
def test_adm_018_reset_clears_the_search(admin_flow: AdminFlow) -> None:
    total = admin_flow.toolbar.counter().total
    term = first_row_with(admin_flow, "Short Name")["Short Name"]
    admin_flow.search("Short Name", term, lambda row: contains(row, "Short Name", term))

    admin_flow.reset_search(total)

    assert admin_flow.toolbar.counter().total == total
