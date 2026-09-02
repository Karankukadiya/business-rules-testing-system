-- Read-only validation queries for the DemoCorp employees table (SQLite).
-- Run each query separately. Every query is a SELECT; none changes data.
-- Rows returned by queries Q1-Q8 indicate BAD data. An empty result means PASS.

-- Q1 (BR-01): Finds employee IDs that appear more than once.
SELECT employee_id, COUNT(*) AS occurrences
FROM employees
GROUP BY employee_id
HAVING COUNT(*) > 1;

-- Q2 (BR-02): Finds records whose name is missing or only whitespace.
SELECT * FROM employees
WHERE name IS NULL OR TRIM(name) = '';

-- Q3 (BR-03): Finds employees whose age is outside 18-60.
SELECT * FROM employees
WHERE age IS NULL OR age < 18 OR age > 60;

-- Q4 (BR-04): Finds salaries that are zero, negative, missing or above 200000.
SELECT * FROM employees
WHERE salary IS NULL OR salary <= 0 OR salary > 200000;

-- Q5 (BR-05): Finds departments outside the allowed list.
SELECT * FROM employees
WHERE department IS NULL
   OR department NOT IN ('IT', 'HR', 'Finance', 'Sales', 'Operations');

-- Q6 (BR-06): Finds employment types outside the allowed list.
SELECT * FROM employees
WHERE employment_type IS NULL
   OR employment_type NOT IN ('Full-time', 'Part-time', 'Contract');

-- Q7 (BR-07): Finds joining dates later than today.
SELECT * FROM employees
WHERE joining_date > DATE('now');

-- Q8 (BR-08): Finds statuses outside the allowed list.
SELECT * FROM employees
WHERE status IS NULL
   OR status NOT IN ('Active', 'On Leave', 'Inactive');

-- Q9 (reporting): Counts all employee records per department.
SELECT department, COUNT(*) AS total_employees
FROM employees
GROUP BY department
ORDER BY department;

-- Q10 (reporting): Counts Active employees per department.
SELECT department, COUNT(*) AS active_employees
FROM employees
WHERE status = 'Active'
GROUP BY department
ORDER BY department;
