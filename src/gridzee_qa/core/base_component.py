"""Base class for UI parts shared by many screens (menu, toolbar, message box).

A component has the same helpers as a page object. It describes one part of
the screen and holds no test assertions.
"""

from gridzee_qa.core.base_page import BasePage


class BaseComponent(BasePage):
    pass
