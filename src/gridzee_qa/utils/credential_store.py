"""Stores the credentials of admins created by tests, for later login tests.

File: ``.auth/created_admins.json`` (git-ignored). Entries are grouped by
environment, newest last. Never log the passwords read from here.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from gridzee_qa.core.config_loader import PROJECT_ROOT
from gridzee_qa.factories.admin_factory import AdminData

STORE_FILE = PROJECT_ROOT / ".auth" / "created_admins.json"


def _read(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def save_admin(env: str, admin: AdminData, path: Path = STORE_FILE) -> None:
    data = _read(path)
    data.setdefault(env, []).append(
        {
            "short_name": admin.short_name,
            "username": admin.username,
            "password": admin.password,
            "admin_code": admin.admin_code,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def latest_admin(env: str, path: Path = STORE_FILE) -> dict[str, Any] | None:
    entries = _read(path).get(env) or []
    return entries[-1] if entries else None
