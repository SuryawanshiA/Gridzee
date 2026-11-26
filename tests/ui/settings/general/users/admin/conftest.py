"""Fixtures for Settings > General > Users > Admin tests."""

from collections.abc import Callable

import pytest
from playwright.sync_api import Dialog, Page

from gridzee_qa.core.config_loader import Config
from gridzee_qa.core.logger import get_logger
from gridzee_qa.factories.admin_factory import AdminData, AdminFactory
from gridzee_qa.flows.auth_flow import AuthFlow
from gridzee_qa.flows.settings.general.users.admin_flow import AdminFlow
from gridzee_qa.utils.credential_store import save_admin

_CREATED_ADMIN = pytest.StashKey[AdminData]()
_log = get_logger("admin_fixtures")


def _accept_dialog(dialog: Dialog) -> None:
    _log.info("Browser dialog (%s) accepted: %s", dialog.type, dialog.message)
    dialog.accept()


@pytest.fixture
def admin_flow_at_home(page: Page, config: Config, auth_flow: AuthFlow) -> AdminFlow:
    """Logged in as super admin, on the landing page."""
    page.on("dialog", _accept_dialog)
    auth_flow.login_as("superadmin")
    return AdminFlow(page, config)


@pytest.fixture
def admin_flow(admin_flow_at_home: AdminFlow) -> AdminFlow:
    """Logged in as super admin, on the Admin overview."""
    admin_flow_at_home.open_overview()
    return admin_flow_at_home


@pytest.fixture
def admin_form(admin_flow: AdminFlow) -> AdminFlow:
    """Logged in as super admin, on an empty add-admin form."""
    admin_flow.open_add_form()
    return admin_flow


@pytest.fixture
def admin_factory(config: Config) -> AdminFactory:
    return AdminFactory(config.email_domain)


@pytest.fixture
def remember_admin(request: pytest.FixtureRequest, config: Config) -> Callable[[AdminData], None]:
    """Save a created admin for this run and to .auth/created_admins.json."""

    def remember(admin: AdminData) -> None:
        request.config.stash[_CREATED_ADMIN] = admin
        save_admin(config.env, admin)
        _log.info("Stored credentials of created admin %s", admin.short_name)

    return remember


@pytest.fixture
def created_admin(
    request: pytest.FixtureRequest,
    admin_flow: AdminFlow,
    admin_factory: AdminFactory,
    remember_admin: Callable[[AdminData], None],
) -> AdminData:
    """The admin created earlier in this run, or a new one if none exists yet."""
    existing = request.config.stash.get(_CREATED_ADMIN, None)
    if existing is not None:
        return existing
    admin = admin_flow.create_admin(admin_factory.build())
    remember_admin(admin)
    return admin
