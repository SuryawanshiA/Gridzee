"""Group G: field validation (read-only). ADM-050 to ADM-064.

Safety: every test leaves at least one mandatory field blank (Admin Code is the
last one checked), so Save cannot create a record. ``save_expecting_message``
fails loudly if a save goes through anyway.
"""

from collections.abc import Callable

import pytest

from gridzee_qa.factories.admin_factory import AdminData, AdminFactory
from gridzee_qa.flows.settings.general.users.admin_flow import AdminFlow
from gridzee_qa.pages.settings.general.users.admin.admin_form_page import AdminFormPage

pytestmark = [pytest.mark.ui, pytest.mark.admin]

ADMIN_CODE_BLANK = "Admin Code Field can not be blank"
NUMBER_FIELDS = ["mob_no", "zipcode", "fax_no", "tel_no", "whatsapp_contact_number"]
OPTIONAL_EMAIL_FIELDS = ["password_recovery_email", "help_desk_email"]
DIGIT_FIELDS = {"zipcode", "tel_no", "mob_no", "whatsapp_contact_number", "fax_no", "data_storage"}


def all_but_admin_code(data: AdminData) -> dict[str, str]:
    return {k: v for k, v in data.mandatory_fields().items() if k != AdminFormPage.ADMIN_CODE}


# (test id, fields to fill built from generated data, expected message)
MANDATORY_CASES: list[tuple[str, Callable[[AdminData, AdminFactory], dict[str, str]], str]] = [
    ("ADM-050 all blank", lambda d, f: {}, "Short Name Field can not be blank"),
    ("ADM-051 user name blank", lambda d, f: {"short_name": d.short_name}, "User Name Field can not be blank"),
    (
        "ADM-052 user name not an email",
        lambda d, f: {"short_name": d.short_name, "username": f.invalid_email()},
        "User Name Invalid Format",
    ),
    (
        "ADM-053 confirm username blank",
        lambda d, f: {"short_name": d.short_name, "username": d.username},
        "Confirm User Name Field can not be blank",
    ),
    (
        "ADM-054 usernames differ",
        lambda d, f: {"short_name": d.short_name, "username": d.username, "confirm_username": f.email()},
        "User Name and Confirm User Name Not Match",
    ),
    (
        "ADM-055 password blank",
        lambda d, f: {"short_name": d.short_name, "username": d.username, "confirm_username": d.username},
        "Password Field can not be blank",
    ),
    (
        "ADM-056 retype password blank",
        lambda d, f: {
            "short_name": d.short_name, "username": d.username, "confirm_username": d.username,
            "password_value": d.password,
        },
        "Retype Password Field can not be blank",
    ),
    (
        "ADM-057 passwords differ",
        lambda d, f: {
            "short_name": d.short_name, "username": d.username, "confirm_username": d.username,
            "password_value": d.password, "retype_password": f.password(),
        },
        "Password and Retype Password Not Match",
    ),
    ("ADM-058 admin code blank", lambda d, f: all_but_admin_code(d), ADMIN_CODE_BLANK),
]


@pytest.mark.smoke
@pytest.mark.parametrize(("build_fields", "expected"), [c[1:] for c in MANDATORY_CASES], ids=[c[0] for c in MANDATORY_CASES])
def test_adm_050_to_058_mandatory_field_messages(
    admin_form: AdminFlow, admin_factory: AdminFactory, build_fields, expected: str
) -> None:
    admin_form.form.set_fields(build_fields(admin_factory.build(), admin_factory))

    assert admin_form.save_expecting_message() == expected


@pytest.mark.regression
@pytest.mark.parametrize("value", ["", "abc"], ids=["blank", "letters"])
def test_adm_059_data_storage_blank_or_invalid(admin_form: AdminFlow, admin_factory: AdminFactory, value: str) -> None:
    fields = all_but_admin_code(admin_factory.build())
    fields["data_storage"] = value
    admin_form.form.set_fields(fields)

    if value and admin_form.form.value("data_storage") != value:
        return  # the field refused the letters on input
    message = admin_form.save_expecting_message()
    assert "Data Storage" in message, message


@pytest.mark.regression
def test_adm_060_max_lengths_are_enforced(admin_form: AdminFlow, admin_factory: AdminFactory) -> None:
    form = admin_form.form
    too_long = {}
    for name, max_length in AdminFormPage.MAX_LENGTHS.items():
        form.set_field(name, admin_factory.over_length(max_length, digits=name in DIGIT_FIELDS))
        length = len(form.value(name))
        if length > max_length:
            too_long[name] = f"{length} > {max_length}"

    assert not too_long, f"Fields accept more than their max length: {too_long}"


@pytest.mark.regression
def test_adm_061_weak_password_is_rejected(admin_form: AdminFlow, admin_factory: AdminFactory) -> None:
    weak = admin_factory.weak_password()
    admin_form.form.set_fields(all_but_admin_code(admin_factory.build(password=weak)))

    message = admin_form.save_expecting_message()

    assert message != ADMIN_CODE_BLANK, "A weak password passed validation."


@pytest.mark.regression
@pytest.mark.parametrize("field", OPTIONAL_EMAIL_FIELDS)
def test_adm_062_invalid_email_in_optional_fields(admin_form: AdminFlow, admin_factory: AdminFactory, field: str) -> None:
    fields = all_but_admin_code(admin_factory.build())
    fields[field] = admin_factory.invalid_email()
    admin_form.form.set_fields(fields)

    message = admin_form.save_expecting_message()

    assert message != ADMIN_CODE_BLANK, f"An invalid email in {field} passed validation."


@pytest.mark.regression
@pytest.mark.parametrize("field", NUMBER_FIELDS)
def test_adm_063_letters_in_number_fields(admin_form: AdminFlow, admin_factory: AdminFactory, field: str) -> None:
    letters = admin_factory.letters()
    fields = all_but_admin_code(admin_factory.build())
    fields[field] = letters
    admin_form.form.set_fields(fields)

    if not any(ch.isalpha() for ch in admin_form.form.value(field)):
        return  # the field refused the letters on input
    message = admin_form.save_expecting_message()
    assert message != ADMIN_CODE_BLANK, f"Letters in {field} passed validation."


@pytest.mark.regression
def test_adm_064_message_box_shows_one_message_and_closes(admin_form: AdminFlow) -> None:
    admin_form.save_expecting_message()

    assert admin_form.messages.visible_count() == 1
    admin_form.messages.close()
    assert admin_form.messages.current_message() is None
