"""Business steps for the auth module: logging in.

Role credentials come from config/<env>.yaml and .env through ``config.credentials``.
"""

from gridzee_qa.core.config_loader import Config
from gridzee_qa.pages.auth.login_page import LoginPage


class AuthFlow:
    def __init__(self, login_page: LoginPage, config: Config) -> None:
        self.login_page = login_page
        self.config = config

    def login_as(self, role: str) -> None:
        """Sign in as a configured ``role`` (for example ``superadmin``)."""
        credentials = self.config.credentials(role)
        self.login_with(credentials.username, credentials.password)

    def login_with(self, username: str, password: str) -> None:
        """Open the login page, sign in with the given credentials and wait for the landing page."""
        self.login_page.open()
        self.login_page.login(username, password)
        self.login_page.wait_until_logged_in()
