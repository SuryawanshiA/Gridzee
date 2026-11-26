"""Shared pytest fixtures and options for every test.

Adds the ``--env`` option and applies the settings from ``config/`` to
pytest-playwright's browser, context and page fixtures.

Headless or headed, highest priority first:
    1. ``--headed`` on the command line
    2. ``headless: false`` in config/<env>.yaml
    3. ``headless: true`` in config/base.yaml (the default)
"""

import pytest
from playwright.sync_api import Page, expect

from gridzee_qa.core.config_loader import Config, available_envs, load_config, resolve_env_name
from gridzee_qa.core.exceptions import ConfigError

_CONFIG_KEY = pytest.StashKey[Config]()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help=f"Environment to test ({', '.join(available_envs())}). Defaults to the ENV variable, then 'qa'.",
    )


def pytest_configure(config: pytest.Config) -> None:
    env = resolve_env_name(config.getoption("--env"))
    try:
        settings = load_config(env)
    except ConfigError as error:
        raise pytest.UsageError(str(error)) from error

    config.stash[_CONFIG_KEY] = settings

    # Use the browser from config/ when --browser is not given.
    if not config.option.browser:
        config.option.browser = [settings.browser]


def pytest_report_header(config: pytest.Config) -> str:
    settings = config.stash[_CONFIG_KEY]
    mode = "headless" if settings.headless and not config.getoption("--headed") else "headed"
    return f"gridzee: env={settings.env} base_url={settings.base_url} mode={mode}"


@pytest.fixture(autouse=True)
def _no_data_changes_on_demo(request: pytest.FixtureRequest, pytestconfig: pytest.Config) -> None:
    """Tests marked ``creates_data`` never run on the shared demo environment."""
    if pytestconfig.stash[_CONFIG_KEY].env == "demo" and request.node.get_closest_marker("creates_data"):
        pytest.skip("Tests that create data do not run on the shared demo environment.")


@pytest.fixture(scope="session")
def config(pytestconfig: pytest.Config) -> Config:
    """Settings for the selected environment."""
    return pytestconfig.stash[_CONFIG_KEY]


@pytest.fixture(scope="session")
def base_url(config: Config) -> str:
    """Lets ``page.goto("/path")`` resolve against the environment URL."""
    return config.base_url


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args: dict, config: Config) -> dict:
    args = dict(browser_type_launch_args)
    args.setdefault("headless", config.headless)  # --headed already set it to False
    if config.slow_mo_ms:
        args.setdefault("slow_mo", config.slow_mo_ms)
    return args


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict, config: Config) -> dict:
    return {
        **browser_context_args,
        "viewport": {"width": config.viewport.width, "height": config.viewport.height},
    }


@pytest.fixture(scope="session", autouse=True)
def _expect_timeout(config: Config) -> None:
    expect.set_options(timeout=config.timeouts.expect_ms)


@pytest.fixture
def page(page: Page, config: Config) -> Page:
    page.set_default_timeout(config.timeouts.default_ms)
    page.set_default_navigation_timeout(config.timeouts.navigation_ms)
    return page
