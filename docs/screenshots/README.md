# Screenshot checklist

Save each screenshot in this folder with EXACTLY these file names (the main README links to them).
Use Windows `Win + Shift + S`, save as PNG. Only capture REAL results - never edit or fake them.
Hide personal info (taskbar notifications, email, other browser tabs).

| # | File name | What to capture |
|---|-----------|-----------------|
| 1 | 01-dashboard.png | Dashboard with 3-5 sample employees, chart and SQL checks all PASS |
| 2 | 02-validation-error-add.png | Employee Management > Add, saving age 61 -> red error naming the age field |
| 3 | 03-duplicate-id-error.png | Duplicate ID error (BR-01) |
| 4 | 04-employee-list-search.png | View / Search tab after searching a name |
| 5 | 05-delete-confirmation.png | Delete tab with the confirmation tick-box |
| 6 | 06-rule-validation-fail.png | Business Rule Validation with Age 61: BR-03 FAIL, other rules PASS |
| 7 | 07-rule-validation-pass.png | Same page with all rules PASS and the "NOT saved" message |
| 8 | 08-sql-reference.png | SQL Validation Reference showing queries and a result |
| 9 | 09-reports-page.png | Testing and Reports page with metrics and download buttons |
| 10 | 10-excel-test-suite.png | manual_test_suite.xlsx with your real Actual Result / Status filled in |
| 11 | 11-traceability-matrix.png | Requirements Traceability sheet |
| 12 | 12-defect-log.png | defect_log.xlsx (keep the SAMPLE labels visible if samples remain) |
| 13 | 13-test-summary.png | test_summary.xlsx with your real counts |
| 14 | 14-db-browser-sql.png | DB Browser for SQLite running a validation query |
| 15 | 15-pytest-passing.png | PowerShell showing `python -m pytest -q` -> 46 passed |

Tip: capture Excel screenshots AFTER you execute tests so they show real Pass/Fail values.
