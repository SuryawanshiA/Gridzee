"""Fixtures shared by all UI tests: page objects and flows."""

import pytest
from playwright.sync_api import Page

from gridzee_qa.core.config_loader import Config
from gridzee_qa.flows.auth_flow import AuthFlow
from gridzee_qa.pages.auth.login_page import LoginPage


@pytest.fixture
def login_page(page: Page, config: Config) -> LoginPage:
    return LoginPage(page, config)


@pytest.fixture
def auth_flow(login_page: LoginPage, config: Config) -> AuthFlow:
    return AuthFlow(login_page, config)
