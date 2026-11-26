"""Masks secrets and personal data before anything is sent to the AI service.

Masked:
- values of .env variables whose names contain PASSWORD, SECRET, TOKEN or KEY
- email addresses, long digit sequences (phone numbers), bearer/JWT-like tokens
- values of password inputs, and grid cells under a column whose header contains "password"

Usernames such as "admin" are not masked, because masking a common word would
corrupt the page text the AI needs.
"""

import os
import re
from typing import Any

_SECRET_NAME = re.compile(r"PASSWORD|SECRET|TOKEN|KEY", re.IGNORECASE)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
_LONG_DIGITS = re.compile(r"(?<!\d)\+?\d[\d\s-]{7,}\d(?!\d)")
_TOKEN = re.compile(r"\b(Bearer\s+[\w.-]+|eyJ[\w-]+\.[\w-]+\.[\w-]+)")


def _secret_values() -> list[str]:
    values = [v for k, v in os.environ.items() if _SECRET_NAME.search(k) and v and len(v) >= 6]
    return sorted(set(values), key=len, reverse=True)


def mask_text(text: str, secrets: list[str] | None = None) -> str:
    for value in secrets if secrets is not None else _secret_values():
        text = text.replace(value, "<SECRET>")
    text = _TOKEN.sub("<TOKEN>", text)
    text = _EMAIL.sub("<EMAIL>", text)
    return _LONG_DIGITS.sub("<NUMBER>", text)


def sanitize(data: Any) -> Any:
    """Return a masked copy of strings, lists and dicts."""
    secrets = _secret_values()

    def walk(item: Any) -> Any:
        if isinstance(item, str):
            return mask_text(item, secrets)
        if isinstance(item, list):
            return [walk(i) for i in item]
        if isinstance(item, dict):
            if str(item.get("type", "")).lower() == "password" and "value" in item:
                item = {**item, "value": "<SECRET>"}
            if isinstance(item.get("headers"), list) and isinstance(item.get("rows"), list):
                item = _mask_password_columns(item)
            return {k: walk(v) for k, v in item.items()}
        return item

    return walk(data)


def _mask_password_columns(table: dict[str, Any]) -> dict[str, Any]:
    columns = [i for i, h in enumerate(table["headers"]) if "password" in str(h).lower()]
    if not columns:
        return table
    rows = [[("<SECRET>" if i in columns else cell) for i, cell in enumerate(row)] for row in table["rows"]]
    return {**table, "rows": rows}
