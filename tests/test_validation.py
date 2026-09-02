from datetime import date, timedelta

import pytest

from validation import rule_results, validate_employee

TODAY = date(2026, 6, 1)


def valid(**changes):
    data = {"employee_id": "EMP-001", "name": "Asha Patel", "age": 30, "salary": 50000,
            "department": "IT", "employment_type": "Full-time",
            "joining_date": "2024-01-15", "status": "Active"}
    data.update(changes)
    return data


def fields(errors):
    return [e.field for e in errors]


def test_valid_employee_has_no_errors():
    assert validate_employee(valid(), today=TODAY) == []


def test_missing_employee_id():
    assert fields(validate_employee(valid(employee_id=""), today=TODAY)) == ["employee_id"]
    assert fields(validate_employee(valid(employee_id="   "), today=TODAY)) == ["employee_id"]


def test_duplicate_employee_id():
    errors = validate_employee(valid(), existing_ids={"EMP-001"}, today=TODAY)
    assert fields(errors) == ["employee_id"] and "already exists" in errors[0].message


def test_duplicate_id_ignores_surrounding_spaces():
    assert validate_employee(valid(employee_id=" EMP-001 "), existing_ids={"EMP-001"}, today=TODAY)


@pytest.mark.parametrize("name", ["", "   ", None])
def test_blank_name(name):
    assert fields(validate_employee(valid(name=name), today=TODAY)) == ["name"]


@pytest.mark.parametrize("age,ok", [(17, False), (18, True), (60, True), (61, False),
                                    ("abc", False), (25.5, False), ("", False)])
def test_age_boundaries(age, ok):
    assert (validate_employee(valid(age=age), today=TODAY) == []) is ok


@pytest.mark.parametrize("salary,ok", [(0, False), (0.01, True), (200000, True), (200001, False),
                                       (-1, False), ("abc", False), ("", False)])
def test_salary_limits(salary, ok):
    assert (validate_employee(valid(salary=salary), today=TODAY) == []) is ok


def test_invalid_department():
    assert fields(validate_employee(valid(department="Marketing"), today=TODAY)) == ["department"]


def test_invalid_employment_type():
    assert fields(validate_employee(valid(employment_type="Intern"), today=TODAY)) == ["employment_type"]


def test_future_joining_date():
    assert fields(validate_employee(valid(joining_date=str(TODAY + timedelta(days=1))), today=TODAY)) == ["joining_date"]
    assert validate_employee(valid(joining_date=str(TODAY)), today=TODAY) == []


def test_impossible_or_badly_formatted_date():
    assert validate_employee(valid(joining_date="2024-02-30"), today=TODAY)
    assert validate_employee(valid(joining_date="15/01/2024"), today=TODAY)


def test_invalid_status():
    assert fields(validate_employee(valid(status="Retired"), today=TODAY)) == ["status"]


def test_error_message_names_how_to_fix():
    message = validate_employee(valid(age=99), today=TODAY)[0].message
    assert "18" in message and "60" in message


def test_rule_results_shows_pass_and_fail():
    results = {r["Rule"]: r["Result"] for r in rule_results(valid(age=61), today=TODAY)}
    assert results["BR-03"] == "FAIL" and results["BR-01"] == "PASS" and len(results) == 8
