"""Loads the settings for the selected environment.

Merge order, later wins:
    1. config/base.yaml        defaults for every environment
    2. config/<env>.yaml       environment values (URL, login path, credential variable names)
    3. process environment      real secrets read from .env or the CI secret store

Passwords are never stored in YAML. The YAML holds only the *names* of the
environment variables that contain them.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from gridzee_qa.core.exceptions import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_ENV = "qa"
SUPPORTED_BROWSERS = ("chromium", "firefox", "webkit")


@dataclass(frozen=True)
class Viewport:
    width: int
    height: int


@dataclass(frozen=True)
class Timeouts:
    default_ms: int
    navigation_ms: int
    expect_ms: int


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str = field(repr=False)  # keeps the password out of logs and tracebacks


@dataclass(frozen=True)
class Config:
    env: str
    base_url: str
    login_path: str
    browser: str
    headless: bool
    slow_mo_ms: int
    viewport: Viewport
    timeouts: Timeouts
    email_domain: str  # domain used for generated email addresses
    _credentials: dict[str, dict[str, str]] = field(repr=False)

    @property
    def login_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/{self.login_path.lstrip('/')}"

    def credentials(self, role: str) -> Credentials:
        """Return the username and password for ``role`` from the environment."""
        entry = self._credentials.get(role)
        if entry is None:
            known = ", ".join(sorted(self._credentials)) or "none"
            raise ConfigError(
                f"No credentials for role '{role}' in config/{self.env}.yaml. Known roles: {known}."
            )

        values = {}
        for key in ("username_env", "password_env"):
            variable = entry.get(key)
            if not variable:
                raise ConfigError(f"Role '{role}' in config/{self.env}.yaml is missing '{key}'.")
            value = os.getenv(variable)
            if not value:
                raise ConfigError(
                    f"Environment variable {variable} is not set. Add it to .env (see .env.example)."
                )
            values[key] = value

        return Credentials(username=values["username_env"], password=values["password_env"])


def resolve_env_name(cli_value: str | None = None) -> str:
    """Pick the environment: ``--env`` first, then the ENV variable, then the default."""
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    return cli_value or os.getenv("ENV") or DEFAULT_ENV


def load_config(env: str) -> Config:
    """Build the :class:`Config` for ``env`` (for example ``qa`` or ``demo``)."""
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    base = _read_yaml(CONFIG_DIR / "base.yaml")
    env_file = CONFIG_DIR / f"{env}.yaml"
    if not env_file.is_file():
        raise ConfigError(f"Unknown environment '{env}'. Available: {', '.join(available_envs())}.")

    merged = _deep_merge(base, _read_yaml(env_file))

    for key in ("base_url", "login_path"):
        if not merged.get(key):
            raise ConfigError(f"'{key}' is missing in config/{env}.yaml.")

    browser = str(merged.get("browser", "chromium")).lower()
    if browser not in SUPPORTED_BROWSERS:
        raise ConfigError(f"Unsupported browser '{browser}'. Use one of: {', '.join(SUPPORTED_BROWSERS)}.")

    try:
        viewport = Viewport(**merged["viewport"])
        timeouts = Timeouts(**merged["timeouts"])
    except (KeyError, TypeError) as error:
        raise ConfigError(f"'viewport' or 'timeouts' is missing or incomplete in config/base.yaml: {error}") from error

    return Config(
        env=env,
        base_url=merged["base_url"],
        login_path=merged["login_path"],
        browser=browser,
        headless=bool(merged.get("headless", True)),
        slow_mo_ms=int(merged.get("slow_mo_ms", 0)),
        viewport=viewport,
        timeouts=timeouts,
        email_domain=str((merged.get("test_data") or {}).get("email_domain", "yopmail.com")),
        _credentials=merged.get("credentials") or {},
    )


def available_envs() -> list[str]:
    return sorted(p.stem for p in CONFIG_DIR.glob("*.yaml") if p.stem != "base")


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigError(f"Config file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
