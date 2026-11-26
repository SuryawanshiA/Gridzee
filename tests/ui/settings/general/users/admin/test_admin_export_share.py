"""Group E: export and share (read-only). ADM-030 to ADM-034."""

import re
from pathlib import Path

import pytest

from gridzee_qa.flows.settings.general.users.admin_flow import AdminFlow

pytestmark = [pytest.mark.ui, pytest.mark.admin]

EXPORT_NAME = r"^Admin_\d{2}-\d{2}-\d{4}_\d{2}-\d{2}-\d{2}_(AM|PM)\.{ext}$"


@pytest.mark.regression
@pytest.mark.parametrize(("kind", "extension"), [("excel", "xlsx"), ("pdf", "pdf"), ("csv", "csv")])
def test_adm_030_to_032_download(admin_flow: AdminFlow, kind: str, extension: str) -> None:
    """ADM-030 Excel, ADM-031 PDF, ADM-032 CSV."""
    download = admin_flow.toolbar.download(kind)

    assert re.match(EXPORT_NAME.format(ext=extension), download.suggested_filename), download.suggested_filename
    assert download.failure() is None


@pytest.mark.regression
def test_adm_033_export_respects_search_filter(admin_flow: AdminFlow, tmp_path: Path) -> None:
    names = [n for n in admin_flow.overview.grid().column("Short Name") if n]
    if len(names) < 2:
        pytest.skip("Needs at least two admins in the grid.")
    term = names[0]
    other = next((n for n in names[1:] if term.casefold() not in n.casefold()), None)
    if other is None:
        pytest.skip("No second admin with a different short name.")
    admin_flow.search("Short Name", term, lambda row: term.casefold() in row["Short Name"].casefold())

    download = admin_flow.toolbar.download("csv")
    path = tmp_path / download.suggested_filename
    download.save_as(path)
    content = path.read_text(encoding="utf-8-sig", errors="replace")

    assert term in content
    assert other not in content


@pytest.mark.regression
def test_adm_034_share_is_not_available_for_super_admin(admin_flow: AdminFlow) -> None:
    admin_flow.overview.click_share(0)

    text = admin_flow.overview.share_popup_text()
    admin_flow.overview.close_popup()

    assert "Share Credentials" in text
    assert "This feature not avaible for Super Admin" in text  # application wording, including its typo
