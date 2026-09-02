"""Business-rule validation for DemoCorp employee records (BR-01 .. BR-12).

Pure functions only: no database or UI code, so they are easy to unit test.
"""
from dataclasses import dataclass
from datetime import date, datetime

DEPARTMENTS = ["IT", "HR", "Finance", "Sales", "Operations"]
EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract"]
STATUSES = ["Active", "On Leave", "Inactive"]
MIN_AGE, MAX_AGE = 18, 60
MAX_SALARY = 200_000

BUSINESS_RULES = {
    "BR-01": "Employee ID is mandatory and must be unique.",
    "BR-02": "Employee name is mandatory and cannot be only whitespace.",
    "BR-03": "Age must be between 18 and 60, inclusive.",
    "BR-04": "Monthly salary must be > 0 and <= Rs. 200,000.",
    "BR-05": "Department must be IT, HR, Finance, Sales or Operations.",
    "BR-06": "Employment type must be Full-time, Part-time or Contract.",
    "BR-07": "Joining date cannot be in the future.",
    "BR-08": "Status must be Active, On Leave or Inactive.",
    "BR-09": "Only valid employee records can be saved to the database.",
    "BR-10": "Updating an employee must not create duplicate IDs or modify other records.",
    "BR-11": "Deleting an employee requires confirmation.",
    "BR-12": "Validation errors must identify the invalid field and explain the fix.",
}

# Which field each field-level rule checks.
RULE_FIELDS = {
    "BR-01": "employee_id", "BR-02": "name", "BR-03": "age", "BR-04": "salary",
    "BR-05": "department", "BR-06": "employment_type",
    "BR-07": "joining_date", "BR-08": "status",
}


@dataclass
class ValidationError:
    field: str
    rule: str
    message: str


class RecordNotSavedError(Exception):
    """Raised when an invalid record is sent to the database layer (BR-09)."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__("; ".join(f"{e.field}: {e.message}" for e in errors))


def _is_blank(value):
    return value is None or str(value).strip() == ""


def _to_int(value):
    """Return int, or None if the value is not a whole number."""
    if isinstance(value, bool) or _is_blank(value):
        return None
    try:
        number = float(str(value).strip())
    except ValueError:
        return None
    return int(number) if number == int(number) else None


def _to_float(value):
    if isinstance(value, bool) or _is_blank(value):
        return None
    try:
        number = float(str(value).strip())
    except ValueError:
        return None
    return number if number == number and abs(number) != float("inf") else None


def _to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if _is_blank(value):
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def check_rule(rule, data, existing_ids=(), today=None):
    """Check one field-level rule. Returns an error message, or None if PASS."""
    today = today or date.today()
    if rule == "BR-01":
        emp_id = data.get("employee_id")
        if _is_blank(emp_id):
            return "Employee ID is required. Enter a unique ID such as EMP-001."
        if str(emp_id).strip() in set(existing_ids):
            return f"Employee ID '{str(emp_id).strip()}' already exists. Use a different, unique ID."
    elif rule == "BR-02":
        if _is_blank(data.get("name")):
            return "Name is required and cannot be only spaces. Enter the employee's full name."
    elif rule == "BR-03":
        age = _to_int(data.get("age"))
        if age is None:
            return f"Age must be a whole number between {MIN_AGE} and {MAX_AGE}."
        if not MIN_AGE <= age <= MAX_AGE:
            return f"Age {age} is out of range. Enter an age from {MIN_AGE} to {MAX_AGE}."
    elif rule == "BR-04":
        salary = _to_float(data.get("salary"))
        if salary is None:
            return f"Salary must be a number greater than 0 and at most {MAX_SALARY:,}."
        if salary <= 0 or salary > MAX_SALARY:
            return f"Salary {salary:,.2f} is invalid. Enter an amount above 0 and up to {MAX_SALARY:,}."
    elif rule == "BR-05":
        if data.get("department") not in DEPARTMENTS:
            return f"Department must be one of: {', '.join(DEPARTMENTS)}."
    elif rule == "BR-06":
        if data.get("employment_type") not in EMPLOYMENT_TYPES:
            return f"Employment type must be one of: {', '.join(EMPLOYMENT_TYPES)}."
    elif rule == "BR-07":
        joined = _to_date(data.get("joining_date"))
        if joined is None:
            return "Joining date is required in YYYY-MM-DD format, e.g. 2024-01-15."
        if joined > today:
            return f"Joining date {joined} is in the future. Enter today's date or earlier."
    elif rule == "BR-08":
        if data.get("status") not in STATUSES:
            return f"Status must be one of: {', '.join(STATUSES)}."
    return None


def rule_results(data, existing_ids=(), today=None):
    """PASS/FAIL result for each field-level rule BR-01..BR-08."""
    results = []
    for rule, field in RULE_FIELDS.items():
        message = check_rule(rule, data, existing_ids, today)
        results.append({
            "Rule": rule, "Field": field, "Description": BUSINESS_RULES[rule],
            "Result": "PASS" if message is None else "FAIL",
            "Explanation": message or "OK",
        })
    return results


def validate_employee(data, existing_ids=(), today=None):
    """Return a list of ValidationError (empty list means the record is valid)."""
    errors = []
    for rule, field in RULE_FIELDS.items():
        message = check_rule(rule, data, existing_ids, today)
        if message:
            errors.append(ValidationError(field, rule, message))
    return errors


def clean_employee(data):
    """Return a normalised copy of a VALID record (trimmed text, proper types)."""
    return {
        "employee_id": str(data["employee_id"]).strip(),
        "name": str(data["name"]).strip(),
        "age": _to_int(data["age"]),
        "salary": _to_float(data["salary"]),
        "department": data["department"],
        "employment_type": data["employment_type"],
        "joining_date": _to_date(data["joining_date"]).isoformat(),
        "status": data["status"],
    }
