# Test Cases: Settings > General > Users > Admin

**Status:** Automated, **not executed yet** (waiting for permission to run). See [Automation mapping](#automation-mapping).
**Environment explored:** QA (`https://qa.uffizio.com`), logged in as super admin, Chromium.
**Scope:** Admin overview (grid, search, paging, exports, share) and the add form's **My Account** tab. The other 16 tabs of the form are listed but not covered (see [Open questions](#open-questions)).

---

## 1. What was found while exploring

### Navigation
`Settings` (sidebar) → `General` → `Users` → `Admin`

- The menu lives in the frame `divframe`. `Users` contains: Super Admin, Admin, Reseller, Company, Sub Users, Branch.
- The Admin overview loads in the frame `contentframe` (`Overview.jsp?screenid=2266`).
- The bottom toolbar is in the frame `bottomframe`.
- The add/edit form loads in `contentframe` (`DetailScreen.jsp?screenid=2263&mode=insert` or `mode=update`).

### Admin overview
| Part | Details |
|---|---|
| Grid columns | Short Name, User Name, Password, Share, Application, User Group, Mobile No, Last Login Time, User Time Zone, Payment Status, User Status, Document, Expiry Date, Extended Date |
| Default sort | Short Name, ascending (arrow on header) |
| Bottom toolbar, left | New (+), Reset, Download Excel, Download PDF, Download CSV |
| Search | Text box `searchterm`, field list `searchfield`: All, Short Name, User Name, Application, User Group, Email, Mobile. Search icon. |
| Paging | Records per page: 10, 20, 30, 40, 50, 100, 200, 300, 400, 500, 1000 (default 1000). Page number list, Previous, Next/Last. Counter shows `start-end (total)`, for example `1-47 (47)`. |
| Top-right icons | Search, Favorite Report, Settings, Help |
| Share icon (per row) | As super admin, opens "Share Credentials" with "This feature not avaible for Super Admin" |
| Password column | Shows passwords in plain text |
| No match | Grid shows "No Records Found", counter `0-0 (0)` |
| Export file names | `Admin_<dd-MM-yyyy>_<hh-mm-ss>_<AM/PM>.xlsx` / `.pdf` / `.csv` |
| Open a row | Double-click opens the form in `mode=update` |

No delete action was found on the overview or the form toolbar.

### Add form
Opened with (+). Bottom toolbar: **Back**, **Save**, **Reset**.

**Tabs:** My Account, Rule, User Setting, Screen Access, Data Access, Map, Email, SMS, Payment Gateway, Rename Label, IVR, White Label, ChatBot, Social Media API, Document, Authentication, SSO (Single Sign On).

**My Account fields**

| Field | Name | Mandatory | Max length | Default |
|---|---|---|---|---|
| Logo upload | (file) | No | | |
| Country | dropdown (257 options) | No | | Afghanistan |
| State | dropdown, depends on Country | No | | Badakhshan |
| Short Name | `short_name` | **Yes** | 50 | |
| User Name | `username` | **Yes** | 70 | placeholder "Use Email Address as Username" |
| Confirm Username | `confirm_username` | **Yes** | | |
| Share Credentials Via | Email, SMS checkboxes | No | | unchecked |
| Password | `password_value` | **Yes** | 50 | eye icon, info icon |
| Retype Password | `retype_password` | **Yes** | 50 | eye icon |
| Enable Security Pin | checkbox | No | | unchecked |
| Password Recovery Email | `password_recovery_email` | No | | |
| City | `city` | No | 30 | |
| Zip - Code | `zipcode` | No | 10 | 0 |
| Street 1, Street 2 | `street1`, `street2` | No | 50 | |
| Internet Address | `internet_address` | No | 50 | |
| Contact Person | `contact_person` | No | 50 | |
| Help Desk Telephone Number | `tel_no` | No | 20 | |
| Help Desk Email | `help_desk_email` | No | | |
| Mobile Number | `mob_no` | No | 20 | |
| WhatsApp Contact Number | `calling_code` + `whatsapp_contact_number` | No | 20 | +93 |
| Fax Number | `fax_no` | No | 20 | 0 |
| Disable All Object, Inventory, KYC | checkboxes | No | | unchecked |
| Auto-Suggest IMEI | checkbox | No | | checked |
| Welcome Message | `welcome_msg` | No | 200 | |
| License Type | Tariff / Non-Tariff | No | | Tariff |
| Data Storage (days) | `data_storage` | **Yes** | 3 | 90 |
| Admin Code | `admin_code` | **Yes** | | |

**Data Access tab** marks Alert, Language, SIM Provider, Billing Cycle, Billing Start Month and Billing Start Day as mandatory. During exploration, a save succeeded with these left untouched (see question 5).

### Validation messages
Save checks the fields in this order and shows one message at a time, in a box with a **Close** button:

| Condition | Message |
|---|---|
| Short Name blank | Short Name Field can not be blank |
| User Name blank | User Name Field can not be blank |
| User Name not an email | User Name Invalid Format |
| Confirm Username blank | Confirm User Name Field can not be blank |
| Usernames differ | User Name and Confirm User Name Not Match |
| Password blank | Password Field can not be blank |
| Retype Password blank | Retype Password Field can not be blank |
| Passwords differ | Password and Retype Password Not Match |
| Admin Code blank | Admin Code Field can not be blank |

---

## 2. Test cases

**Priority:** P1 = critical path, P2 = important, P3 = nice to have.
**Data:** "Read-only" cases change nothing. "Creates data" cases add an admin to QA.
**Generated data:** values come from the data generator at run time (section 3). No test data is hard-coded.

### A. Navigation and overview (read-only)
| ID | Title | Pri | Steps | Expected |
|---|---|---|---|---|
| ADM-001 | Open Admin overview from the menu | P1 | Settings → General → Users → Admin | Overview opens with title "Admin" and the grid loaded |
| ADM-002 | Users submenu lists all user types | P3 | Settings → General → Users | Super Admin, Admin, Reseller, Company, Sub Users, Branch are shown |
| ADM-003 | Grid shows all expected columns | P2 | Open overview | The 14 columns in section 1 are shown, in that order |
| ADM-004 | Default sort is Short Name ascending | P3 | Open overview | Short Name header shows the ascending arrow, rows are in A-Z order |
| ADM-005 | Record counter matches the grid | P2 | Open overview | Counter `start-end (total)` matches the number of rows shown |
| ADM-006 | Bottom toolbar icons are present | P3 | Open overview | New, Reset, Excel, PDF, CSV, search box, field list and search icon are visible |

### B. Search (read-only)
| ID | Title | Pri | Steps | Expected |
|---|---|---|---|---|
| ADM-010 | Search field list has all options | P3 | Open the field list | All, Short Name, User Name, Application, User Group, Email, Mobile |
| ADM-011 | Search by Short Name | P1 | Field "Short Name", enter an existing short name, search | Only matching rows; counter updates |
| ADM-012 | Search by User Name | P1 | Field "User Name", enter an existing user name | Only matching rows |
| ADM-013 | Search with "All" | P2 | Field "All", enter an existing short name | Matching rows |
| ADM-014 | Partial text matches | P2 | Search with part of a user name | Rows containing the text are shown |
| ADM-015 | Search is case-insensitive | P3 | Search an existing name in different case | Same rows as the original case (to confirm) |
| ADM-016 | Search by Email, Mobile, Application, User Group | P3 | One search per field with a known value | Only matching rows |
| ADM-017 | No match | P2 | Search a generated random string | "No Records Found", counter `0-0 (0)` |
| ADM-018 | Reset clears the search | P2 | Search, then Reset | Full list returns, counter shows the original total |

### C. Paging (read-only)
| ID | Title | Pri | Steps | Expected |
|---|---|---|---|---|
| ADM-020 | Records-per-page options | P3 | Open the list | 10, 20, 30, 40, 50, 100, 200, 300, 400, 500, 1000. Default 1000 |
| ADM-021 | Page size 10 | P2 | Select 10 | Counter `1-10 (total)`; page list has ceil(total/10) pages |
| ADM-022 | Go to page 2 | P2 | Size 10, select page 2 | Counter `11-20 (total)`; different rows from page 1 |
| ADM-023 | Previous and Next/Last icons | P3 | Size 10, use the icons | Page and counter change accordingly |

### D. Sorting (read-only)
| ID | Title | Pri | Steps | Expected |
|---|---|---|---|---|
| ADM-025 | Sort by a column | P3 | Click a column header twice | Ascending, then descending. *Header click did not respond during exploration; to confirm manually.* |

### E. Export and share (read-only)
| ID | Title | Pri | Steps | Expected |
|---|---|---|---|---|
| ADM-030 | Download Excel | P2 | Click Excel icon | File `Admin_<date>_<time>.xlsx` downloads |
| ADM-031 | Download PDF | P2 | Click PDF icon | File `Admin_<date>_<time>.pdf` downloads |
| ADM-032 | Download CSV | P2 | Click CSV icon | File `Admin_<date>_<time>.csv` downloads |
| ADM-033 | Export respects the search filter | P3 | Search, then export CSV | CSV holds only the filtered rows (to confirm) |
| ADM-034 | Share as super admin | P3 | Click a row's share icon | "Share Credentials" shows "This feature not avaible for Super Admin" |

### F. Add form display (read-only)
| ID | Title | Pri | Steps | Expected |
|---|---|---|---|---|
| ADM-040 | (+) opens the add form | P1 | Click New (+) | Form opens in insert mode on My Account, with the 17 tabs |
| ADM-041 | Mandatory fields are marked | P2 | Open form | Short Name, User Name, Confirm Username, Password, Retype Password, Data Storage, Admin Code show `*` |
| ADM-042 | Default values | P2 | Open form | Country Afghanistan, State Badakhshan, Zip 0, Fax 0, Data Storage 90, License Type Tariff, Auto-Suggest IMEI checked, WhatsApp code +93 |
| ADM-043 | User Name placeholder | P3 | Open form | "Use Email Address as Username" |
| ADM-044 | Password eye icon | P3 | Type a password, click the eye | Text becomes visible; click again hides it |
| ADM-045 | Password policy tooltip | P3 | Hover the info icon | Policy text is shown (capture text) |
| ADM-046 | State list follows Country | P2 | Choose another Country | State list changes to that country's states |
| ADM-047 | Back without saving | P2 | Fill fields, click Back | Overview returns; no new row |
| ADM-048 | Reset clears the form | P2 | Fill fields, click Reset | Fields return to defaults |

### G. Field validation (read-only: one mandatory field is always left blank, so nothing is saved)
| ID | Title | Pri | Steps | Expected |
|---|---|---|---|---|
| ADM-050 | All blank | P1 | Save | "Short Name Field can not be blank" |
| ADM-051 | User Name blank | P1 | Fill Short Name, save | "User Name Field can not be blank" |
| ADM-052 | User Name not an email | P1 | Generated non-email user name | "User Name Invalid Format" |
| ADM-053 | Confirm Username blank | P1 | Valid user name only | "Confirm User Name Field can not be blank" |
| ADM-054 | Usernames differ | P1 | Two different generated emails | "User Name and Confirm User Name Not Match" |
| ADM-055 | Password blank | P1 | Usernames match | "Password Field can not be blank" |
| ADM-056 | Retype Password blank | P1 | Password only | "Retype Password Field can not be blank" |
| ADM-057 | Passwords differ | P1 | Two different generated passwords | "Password and Retype Password Not Match" |
| ADM-058 | Admin Code blank | P1 | All other mandatory fields valid | "Admin Code Field can not be blank" |
| ADM-059 | Data Storage blank or invalid | P2 | Clear Data Storage, or enter letters, with Admin Code blank | Message for Data Storage, or input rejected (capture) |
| ADM-060 | Max lengths enforced | P2 | Type longer text than the limit into each field in section 1 | Input stops at the limit |
| ADM-061 | Weak password | P2 | Matching weak password (for example 3 lowercase letters), Admin Code blank | Policy message expected before the Admin Code message (to confirm) |
| ADM-062 | Invalid emails in optional fields | P3 | Invalid Password Recovery Email / Help Desk Email | Format message (capture) |
| ADM-063 | Letters in number fields | P3 | Letters in Mobile, Zip, Fax, Telephone | Rejected or message (capture) |
| ADM-064 | Message box behavior | P3 | Trigger any message, click Close | One message at a time; Close removes it |

### H. Create admin (creates data)
| ID | Title | Pri | Steps | Expected |
|---|---|---|---|---|
| ADM-070 | **Create admin with mandatory fields** | **P1** | (+), fill mandatory fields with generated data, Save. Then search by Short Name on the overview | Overview returns. Search shows exactly 1 row with the generated Short Name and User Name, User Status "Active". Credentials are stored for later login tests |
| ADM-071 | Create admin with all My Account fields | P2 | Fill mandatory and optional fields with generated data, Save, open the row | Every value is saved and shown in edit mode |
| ADM-072 | Duplicate User Name is rejected | P1 | Create with the User Name from ADM-070 | Error message, no second row (capture text) |
| ADM-073 | Duplicate Short Name or Admin Code | P2 | Create reusing one of them | Accepted or rejected (capture, then confirm expected) |
| ADM-074 | Edit view shows saved data | P2 | Double-click the created row | Update mode; Short Name, User Name and Admin Code match; password fields are empty |
| ADM-075 | Created admin can log in | P1 | Log out, log in with stored credentials | Login succeeds. First login may show Terms and Conditions (to confirm) |
| ADM-076 | Data Access mandatory fields | P2 | Create without touching Data Access | Expected behavior to confirm (see question 5) |

---

## 3. Run-time data generation

Every run generates fresh, valid data from the field rules above. Nothing is hard-coded, and values are unique per run so creates don't clash.

| Field | Rule | Example |
|---|---|---|
| Short Name | `Auto Admin <timestamp>`, at most 50 | `Auto Admin 261126010203` |
| User Name | `auto.admin.<timestamp>@<domain>`, at most 70 | `auto.admin.261126010203@yopmail.com` |
| Confirm Username | Same as User Name | |
| Password | 12 characters with upper, lower, digit and special | `Qa7#kLm2@xYz` |
| Retype Password | Same as Password | |
| Admin Code | `AC<timestamp>` | `AC261126010203` |
| Data Storage | Default 90 kept, or a number 1-999 | `90` |
| City | Realistic city, at most 30 | `Pune` |
| Zip - Code | Digits, at most 10 | `411001` |
| Street 1 / 2 | Realistic street, at most 50 | |
| Contact Person | Realistic name, at most 50 | |
| Mobile / WhatsApp / Telephone | Digits, at most 20 | `9876543210` |
| Emails (recovery, help desk) | Generated, same domain | |
| Welcome Message | Short sentence, at most 200 | |
| Negative data | Built from the same rules: over-length text, non-email user name, mismatched values | |

The generated credentials of a successfully created admin are saved to `.auth/created_admins.json` (git-ignored), so later tests can log in as that admin. Passwords are never written to logs or reports.

---

## 4. Planned code locations (navigation-based)

Folders already created, following `Settings > General > Users > Admin`:

| Layer | Location |
|---|---|
| Page objects | `src/gridzee_qa/pages/settings/general/users/admin/` (overview page, add/edit form page) |
| Flow | `src/gridzee_qa/flows/settings/general/users/admin_flow.py` |
| Shared parts | `src/gridzee_qa/components/` (sidebar menu, bottom toolbar, message box) |
| Data generator | `src/gridzee_qa/factories/` |
| Tests | `tests/ui/settings/general/users/admin/` |
| Static data | `data/settings/general/users/admin/` |
| This document | `docs/test-cases/settings/general/users/admin.md` |

---

## Automation mapping
All tests are in `tests/ui/settings/general/users/admin/`. Each test name starts with its ID, for example `test_adm_070_...`.

| Group | IDs | File | Changes data? |
|---|---|---|---|
| A. Navigation and overview | ADM-001 to 006 | `test_admin_navigation.py` | No |
| B. Search | ADM-010 to 018 | `test_admin_search.py` | No |
| C/D. Paging and sorting | ADM-020 to 025 | `test_admin_paging_sorting.py` | No |
| E. Export and share | ADM-030 to 034 | `test_admin_export_share.py` | No |
| F. Form display | ADM-040 to 048 | `test_admin_form_display.py` | No |
| G. Validation | ADM-050 to 064 | `test_admin_validation.py` | No (one mandatory field always blank) |
| H. Create | ADM-070 to 076 | `test_admin_create.py` | **Yes** (`creates_data` marker) |

**Defaults used for the open questions** (change them once you answer):
- Generated emails use `yopmail.com` (`config/base.yaml`, `test_data.email_domain`).
- Generated passwords have 12 characters with upper, lower, digit and special.
- Data Access is left untouched. ADM-076 is skipped until question 5 is answered.
- ADM-073 expects a duplicate Short Name and a duplicate Admin Code to be rejected.
- No cleanup: each run of group H adds admins (ADM-070, ADM-071, and ADM-072/073 if the app accepts duplicates).
- Search terms for group B are read from the grid at run time.

**Run commands**
```powershell
pytest -m admin                              # all Admin tests
pytest -m "admin and not creates_data"       # read-only Admin tests only
pytest -m "admin and smoke"                  # Admin smoke tests
pytest tests/ui/settings/general/users/admin/test_admin_create.py::test_adm_070_create_admin_with_mandatory_fields
```

## Open questions
1. **Leftover record:** exploration created one admin on QA: Short Name `Probe Short`, User Name `probe.user@example.com`, Admin Code `PROBECODE1`. Should it be removed, and how? No delete action was found.
2. **Cleanup:** every create run adds an admin, and no delete was found. Is accumulating test admins on QA acceptable? Is the `Auto Admin` prefix fine for spotting them?
3. **Email domain:** the existing admins use `yopmail.com`. Use that for generated user names? `Email Verification` is checked by default on the Email tab, which may require a real inbox before the new admin can log in.
4. **Password policy:** what are the rules (length, character types)? The info icon text was not captured.
5. **Data Access mandatory fields:** Alert, Language, SIM Provider, Billing Cycle and Billing Start Month are marked mandatory, but a save went through without touching them. Is that expected, or should the test fill them?
6. **Admin Code:** any format or uniqueness rule?
7. **Other tabs:** only My Account is covered now. Should the other 16 tabs (User Setting, Screen Access, Data Access and so on) be covered later?
8. **New admin login:** does the first login need Terms and Conditions acceptance or email verification?
