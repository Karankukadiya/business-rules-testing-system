-- DemoCorp employee database schema (SQLite).
-- Application-level validation gives friendly messages; these constraints are a safety net.
-- Note: SQLite cannot use date('now') inside CHECK, so BR-07 (future dates) is enforced
-- by the application and verified by query Q7 in validation_queries.sql.

CREATE TABLE IF NOT EXISTS employees (
    employee_id     TEXT PRIMARY KEY CHECK (length(trim(employee_id)) > 0),            -- BR-01
    name            TEXT NOT NULL    CHECK (length(trim(name)) > 0),                   -- BR-02
    age             INTEGER NOT NULL CHECK (age BETWEEN 18 AND 60),                    -- BR-03
    salary          REAL NOT NULL    CHECK (salary > 0 AND salary <= 200000),          -- BR-04
    department      TEXT NOT NULL    CHECK (department IN ('IT','HR','Finance','Sales','Operations')),  -- BR-05
    employment_type TEXT NOT NULL    CHECK (employment_type IN ('Full-time','Part-time','Contract')),   -- BR-06
    joining_date    TEXT NOT NULL    CHECK (joining_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'), -- BR-07 (format only)
    status          TEXT NOT NULL    CHECK (status IN ('Active','On Leave','Inactive'))                 -- BR-08
);
