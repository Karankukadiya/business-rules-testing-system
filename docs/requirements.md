# DemoCorp Employee Management - Requirements

## Purpose
DemoCorp (a fictional company) keeps employee records. The system must accept employee data, apply the
business rules below, and store only valid records.

## Business rules
| ID | Rule |
|----|------|
| BR-01 | Employee ID is mandatory and must be unique. |
| BR-02 | Employee name is mandatory and cannot contain only whitespace. |
| BR-03 | Age must be between 18 and 60, inclusive. |
| BR-04 | Monthly salary must be greater than zero and no more than Rs. 200,000. |
| BR-05 | Department must be IT, HR, Finance, Sales or Operations. |
| BR-06 | Employment type must be Full-time, Part-time or Contract. |
| BR-07 | Joining date cannot be in the future. |
| BR-08 | Status must be Active, On Leave or Inactive. |
| BR-09 | Only valid employee records can be saved to the database. |
| BR-10 | Updating an employee must not create duplicate IDs or modify unrelated records. |
| BR-11 | Deleting an employee requires confirmation. |
| BR-12 | Validation errors must identify the invalid field and explain how to correct it. |

## Assumptions
1. Employee IDs are case-sensitive; leading/trailing spaces are trimmed before checking and saving.
2. Age must be a whole number (25.5 is rejected). Salary may have decimals (e.g. 0.01).
3. Salary is in Indian rupees per month; the currency symbol is not entered.
4. Joining date format is YYYY-MM-DD. "Today" is the date on the computer running the app.
5. Allowed values for department, employment type and status are case-sensitive (e.g. "IT", not "it").
6. Names are trimmed of surrounding spaces. No other name formatting rules exist.
7. Updating may change an employee's ID, provided the new ID is not used by another employee.
8. BR-11 is enforced by a confirmation tick-box in the UI and by a `confirmed` flag in the data layer.
9. The database enforces most rules as a safety net; "no future date" cannot be a SQLite CHECK
   (needs `date('now')`), so it is enforced by the application and checked with SQL query Q7.
10. Validation-only checks (Business Rule Validation page) never write to the database.
