"""Admin test data for Settings > General > Users > Admin.

A thin layer over the generic ``utils/data_generator.py``: it lists the My
Account fields (name, label, max length, prefix) and maps the generated values
to ``AdminData``. All value rules live in the generator.

Every ``build()`` returns new, unique, valid values. Negative values come from
the same generator.
"""

from dataclasses import dataclass, field, replace

from gridzee_qa.utils.data_generator import DataGenerator, FieldSpec

SHORT_NAME_PREFIX = "Auto Admin"
USERNAME_PREFIX = "auto.admin"
ADMIN_CODE_PREFIX = "AC"
DATA_STORAGE_DEFAULT = "90"

# My Account fields in form order (validation order). Max lengths from the form.
MY_ACCOUNT_FIELDS = (
    FieldSpec("short_name", "Short Name", max_length=50, required=True, prefix=SHORT_NAME_PREFIX),
    FieldSpec("username", "User Name", max_length=70, required=True, placeholder="Use Email Address as Username", prefix=USERNAME_PREFIX),
    FieldSpec("confirm_username", "Confirm Username", required=True),
    FieldSpec("password_value", "Password", input_type="password", max_length=50, required=True),
    FieldSpec("retype_password", "Retype Password", input_type="password", max_length=50, required=True),
    FieldSpec("password_recovery_email", "Password Recovery Email", prefix="recovery"),
    FieldSpec("city", "City", max_length=30),
    FieldSpec("zipcode", "Zip - Code", max_length=10),
    FieldSpec("street1", "Street 1", max_length=50),
    FieldSpec("street2", "Street 2", max_length=50),
    FieldSpec("internet_address", "Internet Address", max_length=50),
    FieldSpec("contact_person", "Contact Person", max_length=50),
    FieldSpec("tel_no", "Help Desk Telephone Number", max_length=20),
    FieldSpec("help_desk_email", "Help Desk Email", prefix="helpdesk"),
    FieldSpec("mob_no", "Mobile Number", max_length=20),
    FieldSpec("whatsapp_contact_number", "WhatsApp Contact Number", max_length=20),
    FieldSpec("fax_no", "Fax Number", max_length=20),
    FieldSpec("welcome_msg", "Welcome Message", max_length=200),
    FieldSpec("admin_code", "Admin Code", required=True, prefix=ADMIN_CODE_PREFIX),
)

OPTIONAL_FIELDS = (
    "password_recovery_email", "city", "zipcode", "street1", "street2", "internet_address",
    "contact_person", "tel_no", "help_desk_email", "mob_no", "whatsapp_contact_number",
    "fax_no", "welcome_msg",
)


@dataclass(frozen=True)
class AdminData:
    # Mandatory on My Account
    short_name: str
    username: str
    password: str = field(repr=False)
    admin_code: str = ""
    data_storage: str = DATA_STORAGE_DEFAULT
    # Optional on My Account
    password_recovery_email: str = ""
    city: str = ""
    zipcode: str = ""
    street1: str = ""
    street2: str = ""
    internet_address: str = ""
    contact_person: str = ""
    tel_no: str = ""
    help_desk_email: str = ""
    mob_no: str = ""
    whatsapp_contact_number: str = ""
    fax_no: str = ""
    welcome_msg: str = ""

    def mandatory_fields(self) -> dict[str, str]:
        """Field name to value, in the order the form validates them."""
        return {
            "short_name": self.short_name,
            "username": self.username,
            "confirm_username": self.username,
            "password_value": self.password,
            "retype_password": self.password,
            "data_storage": self.data_storage,
            "admin_code": self.admin_code,
        }

    def optional_fields(self) -> dict[str, str]:
        return {name: getattr(self, name) for name in OPTIONAL_FIELDS}


class AdminFactory:
    def __init__(self, email_domain: str) -> None:
        self.generator = DataGenerator(email_domain=email_domain)

    def build(self, **overrides: str) -> AdminData:
        """A valid admin with every My Account text field filled."""
        values = self.generator.record(MY_ACCOUNT_FIELDS)
        data = AdminData(
            short_name=values["short_name"],
            username=values["username"],
            password=values["password_value"],
            admin_code=values["admin_code"],
            **{name: values[name] for name in OPTIONAL_FIELDS},
        )
        return replace(data, **overrides)

    # Single values, delegated to the generic generator
    def token(self) -> str:
        return self.generator.token()

    def email(self, label: str = USERNAME_PREFIX, token: str | None = None) -> str:
        return self.generator.email(label, token)

    def invalid_email(self) -> str:
        return self.generator.invalid_email()

    def password(self, length: int = 12) -> str:
        return self.generator.password(length)

    def weak_password(self) -> str:
        return self.generator.weak_password()

    def mobile(self) -> str:
        return self.generator.mobile()

    def letters(self, length: int = 6) -> str:
        return self.generator.letters(length)

    def over_length(self, max_length: int, digits: bool = False, extra: int = 5) -> str:
        return self.generator.over_length(max_length, digits=digits, extra=extra)
