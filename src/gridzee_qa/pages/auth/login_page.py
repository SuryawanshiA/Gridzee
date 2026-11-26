"""Page object for the Trakzee login page (/jsp/trakzee_login.jsp)."""

import re

from gridzee_qa.core.base_page import BasePage

# After a successful login the application lands on /jsp/index.html.
LOGGED_IN_URL = re.compile(r"/jsp/index\.html")


class LoginPage(BasePage):
    USERNAME = "#username"
    PASSWORD = "#password"
    REMEMBER_ME = "#rememberMe"
    SUBMIT = "#login_form button[type=submit]"

    def open(self) -> None:
        self.goto(self.config.login_url)
        self.wait_for_visible(self.USERNAME)

    def login(self, username: str, password: str) -> None:
        self.fill(self.USERNAME, username)
        self.fill(self.PASSWORD, password)
        self.click(self.SUBMIT)

    def wait_until_logged_in(self) -> None:
        self.wait_for_url(LOGGED_IN_URL)
