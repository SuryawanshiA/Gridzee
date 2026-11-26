"""Group F: add form display (read-only). ADM-040 to ADM-048.

Nothing is saved. Tests leave the form unsaved or use Back and Reset.
"""

import pytest

from gridzee_qa.factories.admin_factory import AdminFactory
from gridzee_qa.flows.settings.general.users.admin_flow import AdminFlow
from gridzee_qa.pages.settings.general.users.admin.admin_form_page import AdminFormPage

pytestmark = [pytest.mark.ui, pytest.mark.admin]

TEXT_DEFAULTS = {"zipcode": "0", "fax_no": "0", "data_storage": "90"}


@pytest.mark.smoke
def test_adm_040_new_opens_add_form_with_all_tabs(admin_form: AdminFlow) -> None:
    form = admin_form.form

    assert form.mode() == "insert"
    missing = [tab for tab in AdminFormPage.TABS if not form.is_tab_visible(tab)]
    assert not missing, f"Missing tabs: {missing}"


@pytest.mark.regression
def test_adm_041_mandatory_fields_are_marked(admin_form: AdminFlow) -> None:
    unmarked = {
        name: admin_form.form.label(name)
        for name in AdminFormPage.MANDATORY_FIELDS
        if "*" not in (admin_form.form.label(name) or "")
    }

    assert not unmarked, f"Mandatory fields without '*': {unmarked}"


@pytest.mark.regression
def test_adm_042_default_values(admin_form: AdminFlow) -> None:
    form = admin_form.form
    problems = {}
    for name, expected in TEXT_DEFAULTS.items():
        if form.value(name) != expected:
            problems[name] = form.value(name)
    for element_id, expected in AdminFormPage.CHECKBOX_DEFAULTS.items():
        if form.is_checked(element_id) != expected:
            problems[element_id] = form.is_checked(element_id)
    if form.calling_code() != "+93":
        problems["calling_code"] = form.calling_code()
    for label, expected in {"Country": "Afghanistan", "State": "Badakhshan"}.items():
        if form.dropdown_text(label) != expected:
            problems[label] = form.dropdown_text(label)

    assert not problems, f"Unexpected defaults: {problems}"


@pytest.mark.regression
def test_adm_043_user_name_placeholder(admin_form: AdminFlow) -> None:
    assert admin_form.form.placeholder(AdminFormPage.USERNAME) == "Use Email Address as Username"


@pytest.mark.regression
def test_adm_044_password_eye_icon_toggles_visibility(admin_form: AdminFlow, admin_factory: AdminFactory) -> None:
    form = admin_form.form
    form.set_field(AdminFormPage.PASSWORD, admin_factory.password())
    assert form.password_input_type() == "password"

    form.toggle_password_visibility()
    form.wait_until(lambda: form.password_input_type() == "text", description="password shown as text")

    form.toggle_password_visibility()
    form.wait_until(lambda: form.password_input_type() == "password", description="password hidden again")


@pytest.mark.regression
def test_adm_045_password_policy_tooltip(admin_form: AdminFlow) -> None:
    text = admin_form.form.password_info_text()

    assert text.strip(), "The password info icon shows no text."


@pytest.mark.regression
def test_adm_046_state_list_follows_country(admin_form: AdminFlow) -> None:
    form = admin_form.form

    form.choose("Country", "India")
    form.wait_until(lambda: form.dropdown_text("State") != "Badakhshan", description="the State list to change")
    form.choose("State", "Maharashtra")

    assert form.dropdown_text("Country") == "India"
    assert form.dropdown_text("State") == "Maharashtra"


@pytest.mark.regression
def test_adm_047_back_without_saving(admin_form: AdminFlow, admin_factory: AdminFactory) -> None:
    unsaved = admin_factory.build()
    admin_form.fill_my_account(unsaved, skip=(AdminFormPage.ADMIN_CODE,))

    admin_form.back_to_overview()

    assert admin_form.find_by_short_name(unsaved.short_name) == []


@pytest.mark.regression
def test_adm_048_reset_clears_the_form(admin_form: AdminFlow, admin_factory: AdminFactory) -> None:
    form = admin_form.form
    data = admin_factory.build()
    form.set_fields({"short_name": data.short_name, "city": data.city, "zipcode": data.zipcode})

    admin_form.toolbar.click_reset()

    form.wait_until(
        lambda: form.value("short_name") == "" and form.value("city") == "" and form.value("zipcode") == "0",
        description="fields back to their defaults",
    )
