"""SQLite data layer. Every function takes db_path so tests can use a temp database."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from validation import RecordNotSavedError, clean_employee, validate_employee

BASE_DIR = Path(__file__).parent
DEFAULT_DB = BASE_DIR / "employees.db"
SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"
VALIDATION_SQL_FILE = BASE_DIR / "sql" / "validation_queries.sql"
COLUMNS = ["employee_id", "name", "age", "salary", "department",
           "employment_type", "joining_date", "status"]


class ConfirmationRequiredError(Exception):
    """Raised when delete is attempted without confirmation (BR-11)."""


class EmployeeNotFoundError(Exception):
    pass


@contextmanager
def get_connection(db_path=DEFAULT_DB):
    """Open a connection and always close it."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path=DEFAULT_DB):
    """Create the employees table if it does not exist (fresh DB on first run)."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def list_employees(db_path=DEFAULT_DB, search=""):
    """All employees, optionally filtered by ID or name (case-insensitive contains)."""
    sql = f"SELECT {', '.join(COLUMNS)} FROM employees"
    params = ()
    if search.strip():
        sql += " WHERE employee_id LIKE ? OR name LIKE ?"
        like = f"%{search.strip()}%"
        params = (like, like)
    with get_connection(db_path) as conn:
        return [dict(r) for r in conn.execute(sql + " ORDER BY employee_id", params)]


def get_employee(employee_id, db_path=DEFAULT_DB):
    with get_connection(db_path) as conn:
        row = conn.execute(f"SELECT {', '.join(COLUMNS)} FROM employees WHERE employee_id = ?",
                           (employee_id,)).fetchone()
    return dict(row) if row else None


def existing_ids(db_path=DEFAULT_DB, exclude=None):
    """Set of employee IDs already in the database (optionally excluding one)."""
    with get_connection(db_path) as conn:
        ids = {r[0] for r in conn.execute("SELECT employee_id FROM employees")}
    ids.discard(exclude)
    return ids


def add_employee(data, db_path=DEFAULT_DB, today=None):
    """Validate then insert. Invalid records are rejected (BR-09)."""
    errors = validate_employee(data, existing_ids(db_path), today)
    if errors:
        raise RecordNotSavedError(errors)
    record = clean_employee(data)
    with get_connection(db_path) as conn:
        conn.execute(f"INSERT INTO employees ({', '.join(COLUMNS)}) VALUES ({', '.join('?' * 8)})",
                     [record[c] for c in COLUMNS])
    return record


def update_employee(original_id, data, db_path=DEFAULT_DB, today=None):
    """Update exactly one record. The new ID must not clash with any OTHER record (BR-10)."""
    if get_employee(original_id, db_path) is None:
        raise EmployeeNotFoundError(f"Employee '{original_id}' was not found.")
    errors = validate_employee(data, existing_ids(db_path, exclude=original_id), today)
    if errors:
        raise RecordNotSavedError(errors)
    record = clean_employee(data)
    assignments = ", ".join(f"{c} = ?" for c in COLUMNS)
    with get_connection(db_path) as conn:
        conn.execute(f"UPDATE employees SET {assignments} WHERE employee_id = ?",
                     [record[c] for c in COLUMNS] + [original_id])
    return record


def delete_employee(employee_id, confirmed=False, db_path=DEFAULT_DB):
    """Delete one record, only if the user confirmed (BR-11)."""
    if not confirmed:
        raise ConfirmationRequiredError("Deletion requires confirmation.")
    with get_connection(db_path) as conn:
        cursor = conn.execute("DELETE FROM employees WHERE employee_id = ?", (employee_id,))
        if cursor.rowcount == 0:
            raise EmployeeNotFoundError(f"Employee '{employee_id}' was not found.")


def department_counts(db_path=DEFAULT_DB):
    with get_connection(db_path) as conn:
        return [dict(r) for r in conn.execute(
            "SELECT department, COUNT(*) AS total FROM employees GROUP BY department ORDER BY department")]


def summary_counts(db_path=DEFAULT_DB):
    with get_connection(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM employees WHERE status = 'Active'").fetchone()[0]
    return {"total": total, "active": active}


def parse_sql_queries(path=VALIDATION_SQL_FILE):
    """Split validation_queries.sql into [{'id','title','sql'}] using the '-- Qn' comments."""
    queries, current = [], None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("-- Q") and ":" in line:
            if current:
                queries.append(current)
            head, title = line[3:].split(":", 1)
            current = {"id": head.split()[0], "title": title.strip(), "sql": ""}
        elif current is not None:
            current["sql"] += line + "\n"
    if current:
        queries.append(current)
    for q in queries:
        q["sql"] = q["sql"].strip()
    return queries


def run_readonly_query(sql, db_path=DEFAULT_DB):
    """Run a single SELECT statement only; refuse anything else."""
    statement = sql.strip().rstrip(";")
    if not statement.upper().startswith("SELECT") or ";" in statement:
        raise ValueError("Only a single SELECT query is allowed.")
    with get_connection(db_path) as conn:
        return [dict(r) for r in conn.execute(statement)]
