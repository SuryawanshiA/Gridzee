"""UI tests for the auth module: login."""

import re

import pytest
from playwright.sync_api import Page, expect

from gridzee_qa.flows.auth_flow import AuthFlow
from gridzee_qa.pages.auth.login_page import LoginPage


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.auth
def test_login_page_shows_the_login_form(login_page: LoginPage, page: Page) -> None:
    login_page.open()

    expect(page).to_have_title("Login")
    expect(page.locator(LoginPage.USERNAME)).to_be_visible()
    expect(page.locator(LoginPage.PASSWORD)).to_be_visible()
    expect(page.locator(LoginPage.SUBMIT)).to_be_visible()


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.auth
def test_superadmin_can_log_in(auth_flow: AuthFlow, page: Page) -> None:
    auth_flow.login_as("superadmin")

    expect(page).to_have_url(re.compile(r"/jsp/index\.html"))
    expect(page).to_have_title(re.compile(r"^Trakzee"))
