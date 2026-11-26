"""Meaningful test data, generated at run time from field descriptions.

Standalone: standard library only, no imports from this project. The file can be
copied into any other project as is.

Describe a field by its name, label, input type and max length. The generator
works out what kind of value fits (email, password, phone, city, code, ...) and
returns a realistic value that respects the max length. Values that must be
unique (names, emails, codes) carry a token, so parallel runs do not clash.

Examples
--------
    gen = DataGenerator(email_domain="yopmail.com")

    gen.value(FieldSpec("city", max_length=30))                         # 'Pune'
    gen.value(FieldSpec("mob_no", label="Mobile Number", max_length=20))  # '9876543210'
    gen.value(FieldSpec("short_name", prefix="Auto Admin"))             # 'Auto Admin 261126...'

    # A whole form. "confirm_*" and "retype_*" fields copy their partner field.
    gen.record([FieldSpec("username", placeholder="Use Email Address as Username"),
                FieldSpec("confirm_username"),
                FieldSpec("password_value", input_type="password"),
                FieldSpec("retype_password", input_type="password")])

    # Straight from captured form fields (dicts with name, label, type, maxlength, options)
    gen.record([FieldSpec.from_dict(f) for f in captured_fields])

    # Negative data from the same rules
    gen.over_length(FieldSpec("zipcode", max_length=10))   # 15 digits
    gen.invalid_email(), gen.weak_password(), gen.letters()
"""

from __future__ import annotations

import itertools
import random
import re
import secrets
import string
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

# Kinds of values the generator can produce
EMAIL = "email"
PASSWORD = "password"
PHONE = "phone"
ZIPCODE = "zipcode"
CITY = "city"
STREET = "street"
URL = "url"
PERSON_NAME = "person_name"
CODE = "code"
INTEGER = "integer"
SENTENCE = "sentence"
DATE = "date"
LABEL = "label"  # unique display name, for example a short name
CHOICE = "choice"  # one of the given options
TEXT = "text"

NUMERIC_KINDS = {PHONE, ZIPCODE, INTEGER}

# Inference rules: first match wins. Keywords are matched against the
# normalized name, label and placeholder of the field.
_RULES: list[tuple[str, tuple[str, ...]]] = [
    (EMAIL, ("email", "e mail", "mail id")),
    (PASSWORD, ("password", "passwd", "pwd", "pin code secret")),
    (URL, ("url", "website", "web site", "internet address", "link", "domain")),
    (PHONE, ("mobile", "phone", "telephone", "tel no", "fax", "whatsapp", "contact number", "mob no")),
    (ZIPCODE, ("zip", "zipcode", "postal", "postcode", "pin code", "pincode")),
    (CITY, ("city", "town")),
    (STREET, ("street", "address", "addr", "landmark")),
    (PERSON_NAME, ("contact person", "person", "first name", "last name", "full name", "owner name", "driver name")),
    (CODE, ("code",)),
    (DATE, ("date", "dob")),
    (INTEGER, ("days", "count", "qty", "quantity", "age", "storage", "limit", "duration", "number", "no of")),
    (SENTENCE, ("message", "description", "remark", "note", "comment", "welcome", "about")),
    (LABEL, ("short name", "name", "title")),
]

_PLACEHOLDER_OPTIONS = {"", "--", "select", "--select--", "-- select --", "none", "all"}
_CONFIRM_PREFIX = re.compile(r"^(confirm|retype|re|repeat|verify)[_\s-]+", re.IGNORECASE)


def _normalize(*parts: str | None) -> str:
    text = " ".join(p for p in parts if p)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)  # camelCase -> camel Case
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


@dataclass(frozen=True)
class FieldSpec:
    """Description of one input field."""

    name: str
    label: str = ""
    input_type: str = "text"
    max_length: int | None = None
    required: bool = False
    options: Sequence[str] = field(default_factory=tuple)
    placeholder: str = ""
    kind: str | None = None  # set to force a kind; otherwise it is inferred
    prefix: str = ""  # for unique values, for example "Auto Admin" or "AC"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FieldSpec:
        """Build from a captured field (keys: name, label, type, maxlength, mandatory, options, placeholder)."""
        return cls(
            name=str(data.get("name") or data.get("id") or ""),
            label=str(data.get("label") or ""),
            input_type=str(data.get("type") or "text"),
            max_length=data.get("maxlength") or data.get("max_length"),
            required=bool(data.get("mandatory") or data.get("required")),
            options=tuple(data.get("options") or ()),
            placeholder=str(data.get("placeholder") or ""),
        )

    @property
    def resolved_kind(self) -> str:
        if self.kind:
            return self.kind
        if self.options and [o for o in self.options if o.strip().lower() not in _PLACEHOLDER_OPTIONS]:
            return CHOICE
        if self.input_type.lower() == "email":
            return EMAIL
        if self.input_type.lower() == "password":
            return PASSWORD
        if self.input_type.lower() in {"number", "tel"}:
            return PHONE if self.input_type.lower() == "tel" else INTEGER
        if self.input_type.lower() == "date":
            return DATE
        if self.input_type.lower() == "url":
            return URL
        key = f" {_normalize(self.name, self.label, self.placeholder)} "
        for kind, keywords in _RULES:
            # whole words only, singular or plural ("remark" matches "remarks", "age" does not match "message")
            if any(f" {k} " in key or f" {k}s " in key for k in keywords):
                return kind
        return TEXT

    @property
    def confirms(self) -> str | None:
        """For 'confirm_username' or 'retype_password': the base word ('username', 'password')."""
        match = _CONFIRM_PREFIX.match(self.name)
        return _normalize(self.name[match.end():]) if match else None


class DataGenerator:
    CITIES = ("Pune", "Mumbai", "Ahmedabad", "Bengaluru", "Chennai", "Hyderabad", "Jaipur", "Kolkata", "Nagpur", "Surat")
    FIRST_NAMES = ("Aarav", "Diya", "Rohan", "Ananya", "Kabir", "Isha", "Vihaan", "Meera", "Arjun", "Sara")
    LAST_NAMES = ("Sharma", "Patel", "Iyer", "Khan", "Reddy", "Mehta", "Nair", "Joshi", "Gupta", "Das")
    STREETS = ("MG Road", "Station Road", "Ring Road", "Park Street", "Church Street", "Lake View Road", "Nehru Nagar")
    WORDS = ("alpha", "bravo", "delta", "falcon", "harbor", "orbit", "summit", "vector", "zenith", "meadow")
    SENTENCES = (
        "Automated test record {token}.",
        "Created by the automation suite on {date}.",
        "Welcome to the test portal, reference {token}.",
    )
    SPECIALS = "@#$!"
    DATE_FORMAT = "%d-%m-%Y"

    _counter = itertools.count(1)

    def __init__(self, email_domain: str = "example.com", seed: int | None = None) -> None:
        self.email_domain = email_domain
        self._random = random.Random(seed) if seed is not None else random.SystemRandom()

    # --- unique token -------------------------------------------------------
    def token(self) -> str:
        """Timestamp, a per-process counter and a random suffix. Unique across parallel workers."""
        return f"{datetime.now():%y%m%d%H%M%S}{next(self._counter):03d}{self._random.randint(0, 999):03d}"

    # --- single values ------------------------------------------------------
    def value(self, spec: FieldSpec, token: str | None = None) -> str:
        """A realistic value for ``spec`` within its max length."""
        token = token or self.token()
        kind = spec.resolved_kind
        maker = {
            EMAIL: lambda: self.email(spec.prefix or "auto", token),
            PASSWORD: lambda: self.password(min(12, spec.max_length or 12)),
            PHONE: self.mobile,
            ZIPCODE: lambda: str(self._random.randint(110001, 855999)),
            CITY: lambda: self._random.choice(self.CITIES),
            STREET: lambda: f"{self._random.randint(1, 999)} {self._random.choice(self.STREETS)}",
            URL: lambda: f"www.{_normalize(spec.prefix or 'auto').replace(' ', '')}{token}.com",
            PERSON_NAME: lambda: f"{self._random.choice(self.FIRST_NAMES)} {self._random.choice(self.LAST_NAMES)}",
            CODE: lambda: f"{spec.prefix or 'C'}{token}",
            INTEGER: lambda: self.integer(spec.max_length),
            SENTENCE: lambda: self._random.choice(self.SENTENCES).format(token=token, date=date.today().strftime(self.DATE_FORMAT)),
            DATE: lambda: (date.today() + timedelta(days=self._random.randint(1, 30))).strftime(self.DATE_FORMAT),
            LABEL: lambda: f"{spec.prefix or 'Auto'} {token}",
            CHOICE: lambda: self.choice(spec.options),
            TEXT: lambda: f"{self._random.choice(self.WORDS)} {token}",
        }[kind]
        return self._fit(maker(), spec, kind, token)

    def record(self, specs: Iterable[FieldSpec], overrides: dict[str, str] | None = None, only_required: bool = False) -> dict[str, str]:
        """Values for a whole form. All unique values share one token, so a record is easy to trace."""
        token = self.token()
        values: dict[str, str] = {}
        for spec in specs:
            if only_required and not spec.required:
                continue
            partner = self._partner(spec, values)
            values[spec.name] = values[partner] if partner else self.value(spec, token)
        values.update(overrides or {})
        return values

    # --- reusable building blocks -------------------------------------------
    def email(self, label: str = "auto", token: str | None = None) -> str:
        local = re.sub(r"[^a-z0-9.]+", ".", label.lower()).strip(".") or "auto"
        return f"{local}.{token or self.token()}@{self.email_domain}"

    def password(self, length: int = 12) -> str:
        """Upper, lower, digit and special character, shuffled. Minimum length 8."""
        length = max(8, length)
        chars = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice(self.SPECIALS),
        ]
        pool = string.ascii_letters + string.digits + self.SPECIALS
        chars += [secrets.choice(pool) for _ in range(length - len(chars))]
        self._random.shuffle(chars)
        return "".join(chars)

    def mobile(self) -> str:
        return f"{self._random.choice('6789')}{self._random.randint(100000000, 999999999)}"

    def integer(self, max_length: int | None = None, low: int = 1, high: int = 999) -> str:
        if max_length:
            high = min(high, 10**max_length - 1)
        return str(self._random.randint(low, max(low, high)))

    def choice(self, options: Sequence[str]) -> str:
        real = [o for o in options if o.strip().lower() not in _PLACEHOLDER_OPTIONS]
        if not real:
            raise ValueError("No selectable options.")
        return self._random.choice(real)

    # --- negative data ------------------------------------------------------
    def invalid_email(self) -> str:
        """Looks like a user name but has no @domain."""
        return f"auto.{self.token()}"

    def weak_password(self) -> str:
        return "".join(secrets.choice(string.ascii_lowercase) for _ in range(3))

    def letters(self, length: int = 6) -> str:
        return "".join(secrets.choice(string.ascii_letters) for _ in range(length))

    def over_length(self, spec_or_max: FieldSpec | int, digits: bool | None = None, extra: int = 5) -> str:
        """Text longer than the field's max length. Digits for numeric fields."""
        if isinstance(spec_or_max, FieldSpec):
            if not spec_or_max.max_length:
                raise ValueError(f"Field '{spec_or_max.name}' has no max length.")
            max_length = spec_or_max.max_length
            digits = spec_or_max.resolved_kind in NUMERIC_KINDS if digits is None else digits
        else:
            max_length = spec_or_max
        alphabet = string.digits if digits else string.ascii_lowercase
        return "".join(secrets.choice(alphabet) for _ in range(max_length + extra))

    # --- helpers ------------------------------------------------------------
    @staticmethod
    def _partner(spec: FieldSpec, values: dict[str, str]) -> str | None:
        base = spec.confirms
        if not base:
            return None
        for name in reversed(list(values)):
            if base in _normalize(name) or _normalize(name) in base:
                return name
        return None

    def _fit(self, value: str, spec: FieldSpec, kind: str, token: str) -> str:
        limit = spec.max_length
        if not limit or len(value) <= limit:
            return value
        if kind in {LABEL, CODE}:  # keep the unique token, shorten the prefix
            room = limit - len(token) - (1 if kind == LABEL else 0)
            if room < 0:
                return token[-limit:]
            head = (spec.prefix or ("Auto" if kind == LABEL else "C"))[:room].rstrip()
            return f"{head} {token}" if kind == LABEL and head else f"{head}{token}"
        if kind == EMAIL:
            return f"{token}@{self.email_domain}"[-limit:] if len(f"{token}@{self.email_domain}") > limit else f"{token}@{self.email_domain}"
        return value[:limit].rstrip()
