import sqlite3
from datetime import date

import pytest

import database as db
from validation import RecordNotSavedError

TODAY = date(2026, 6, 1)


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"          # isolated database, never the real one
    db.init_db(path)
    return path


def emp(emp_id="EMP-001", **changes):
    data = {"employee_id": emp_id, "name": "Asha Patel", "age": 30, "salary": 50000,
            "department": "IT", "employment_type": "Full-time",
            "joining_date": "2024-01-15", "status": "Active"}
    data.update(changes)
    return data


def test_fresh_database_is_empty(db_path):
    assert db.list_employees(db_path) == []


def test_add_valid_employee(db_path):
    db.add_employee(emp(name="  Asha Patel  "), db_path, TODAY)
    assert db.get_employee("EMP-001", db_path)["name"] == "Asha Patel"


def test_invalid_record_is_rejected_and_not_saved(db_path):
    with pytest.raises(RecordNotSavedError) as info:
        db.add_employee(emp(age=61, salary=0), db_path, TODAY)
    assert {e.field for e in info.value.errors} == {"age", "salary"}
    assert db.list_employees(db_path) == []


def test_duplicate_id_rejected(db_path):
    db.add_employee(emp(), db_path, TODAY)
    with pytest.raises(RecordNotSavedError):
        db.add_employee(emp(name="Other"), db_path, TODAY)
    assert len(db.list_employees(db_path)) == 1


def test_update_changes_only_target_record(db_path):
    db.add_employee(emp("EMP-001"), db_path, TODAY)
    db.add_employee(emp("EMP-002", name="Ravi Shah"), db_path, TODAY)
    db.update_employee("EMP-001", emp("EMP-001", name="Asha P."), db_path, TODAY)
    assert db.get_employee("EMP-001", db_path)["name"] == "Asha P."
    assert db.get_employee("EMP-002", db_path)["name"] == "Ravi Shah"


def test_update_without_id_change_is_not_false_duplicate(db_path):
    db.add_employee(emp(), db_path, TODAY)
    db.update_employee("EMP-001", emp(salary=60000), db_path, TODAY)
    assert db.get_employee("EMP-001", db_path)["salary"] == 60000


def test_update_to_existing_id_rejected_and_data_unchanged(db_path):
    db.add_employee(emp("EMP-001"), db_path, TODAY)
    db.add_employee(emp("EMP-002", name="Ravi Shah"), db_path, TODAY)
    with pytest.raises(RecordNotSavedError):
        db.update_employee("EMP-002", emp("EMP-001", name="Ravi Shah"), db_path, TODAY)
    assert [e["employee_id"] for e in db.list_employees(db_path)] == ["EMP-001", "EMP-002"]
    assert db.get_employee("EMP-001", db_path)["name"] == "Asha Patel"


def test_update_missing_employee(db_path):
    with pytest.raises(db.EmployeeNotFoundError):
        db.update_employee("NOPE", emp(), db_path, TODAY)


def test_delete_requires_confirmation(db_path):
    db.add_employee(emp(), db_path, TODAY)
    with pytest.raises(db.ConfirmationRequiredError):
        db.delete_employee("EMP-001", confirmed=False, db_path=db_path)
    assert db.get_employee("EMP-001", db_path) is not None


def test_confirmed_delete_removes_only_that_record(db_path):
    db.add_employee(emp("EMP-001"), db_path, TODAY)
    db.add_employee(emp("EMP-002"), db_path, TODAY)
    db.delete_employee("EMP-001", confirmed=True, db_path=db_path)
    assert [e["employee_id"] for e in db.list_employees(db_path)] == ["EMP-002"]


def test_search_by_id_and_name(db_path):
    db.add_employee(emp("EMP-001"), db_path, TODAY)
    db.add_employee(emp("EMP-002", name="Ravi Shah"), db_path, TODAY)
    assert len(db.list_employees(db_path, "ravi")) == 1
    assert len(db.list_employees(db_path, "EMP-00")) == 2


def test_search_is_safe_from_sql_injection(db_path):
    db.add_employee(emp(), db_path, TODAY)
    assert db.list_employees(db_path, "'; DROP TABLE employees; --") == []
    assert len(db.list_employees(db_path)) == 1


def test_database_constraints_block_bad_direct_insert(db_path):
    conn = sqlite3.connect(db_path)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO employees VALUES ('X','Name',61,1000,'IT','Contract','2024-01-01','Active')")
    conn.close()


def test_counts_and_validation_queries(db_path):
    db.add_employee(emp("EMP-001"), db_path, TODAY)
    db.add_employee(emp("EMP-002", status="Inactive", department="HR"), db_path, TODAY)
    assert db.summary_counts(db_path) == {"total": 2, "active": 1}
    assert {d["department"] for d in db.department_counts(db_path)} == {"IT", "HR"}
    queries = db.parse_sql_queries()
    assert len(queries) == 10
    for q in queries[:8]:
        assert db.run_readonly_query(q["sql"], db_path) == []   # clean data -> no violations


def test_readonly_runner_refuses_non_select(db_path):
    with pytest.raises(ValueError):
        db.run_readonly_query("DELETE FROM employees", db_path)
