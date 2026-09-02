"""DemoCorp Business Rules Validation & Manual Testing System (Streamlit UI)."""
import sqlite3
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import ai_assistant
import database as db
import report_generator as rg
from validation import (BUSINESS_RULES, DEPARTMENTS, EMPLOYMENT_TYPES, STATUSES,
                        RecordNotSavedError, rule_results, validate_employee)

st.set_page_config(page_title="DemoCorp Rules Testing", page_icon="✅", layout="wide")
db.init_db()
st.session_state.setdefault("validation_runs", {"runs": 0, "valid": 0, "invalid": 0})


def show_errors(errors):
    """BR-12: each message names the field and says how to fix it."""
    for e in errors:
        st.error(f"**{e.field}** ({e.rule}): {e.message}")


def db_call(action, *args, **kwargs):
    """Run a database action; show friendly messages instead of stack traces."""
    try:
        return action(*args, **kwargs), True
    except RecordNotSavedError as exc:
        st.error("Record NOT saved. Please fix the following:")
        show_errors(exc.errors)
    except (db.EmployeeNotFoundError, db.ConfirmationRequiredError) as exc:
        st.warning(str(exc))
    except sqlite3.Error:
        st.error("A database problem occurred. Please try again or restart the app.")
    return None, False


def employee_form(prefix, defaults=None):
    """Shared form fields for add/edit. Returns the entered data dict."""
    d = defaults or {}
    c1, c2 = st.columns(2)
    data = {
        "employee_id": c1.text_input("Employee ID", d.get("employee_id", ""), key=f"{prefix}_id"),
        "name": c2.text_input("Name", d.get("name", ""), key=f"{prefix}_name"),
        "age": c1.text_input("Age (18-60)", str(d.get("age", "")), key=f"{prefix}_age"),
        "salary": c2.text_input("Monthly salary (max 200000)", str(d.get("salary", "")), key=f"{prefix}_sal"),
        "department": c1.selectbox("Department", DEPARTMENTS,
                                   index=DEPARTMENTS.index(d.get("department", "IT")), key=f"{prefix}_dep"),
        "employment_type": c2.selectbox("Employment type", EMPLOYMENT_TYPES,
                                        index=EMPLOYMENT_TYPES.index(d.get("employment_type", "Full-time")),
                                        key=f"{prefix}_type"),
        "joining_date": c1.date_input("Joining date", date.fromisoformat(d["joining_date"]) if d.get("joining_date")
                                      else date.today(), min_value=date(1980, 1, 1),
                                      max_value=date.today() + timedelta(days=365), key=f"{prefix}_date"),
        "status": c2.selectbox("Status", STATUSES, index=STATUSES.index(d.get("status", "Active")),
                               key=f"{prefix}_status"),
    }
    return data


# ---------------------------------------------------------------- pages
def page_dashboard():
    st.title("Dashboard")
    counts, _ = db_call(db.summary_counts)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total employee records", counts["total"] if counts else 0)
    c2.metric("Active employees", counts["active"] if counts else 0)
    c3.metric("Validation checks run (this session)", st.session_state.validation_runs["runs"])
    st.subheader("Employees by department")
    dept, _ = db_call(db.department_counts)
    if dept:
        st.bar_chart(pd.DataFrame(dept).set_index("department"))
    else:
        st.info("No employee records yet. Add one under Employee Management.")
    st.subheader("Validation summary")
    v = st.session_state.validation_runs
    st.write(f"Validation-only checks this session: **{v['valid']} valid**, **{v['invalid']} invalid** "
             "(these records were not saved).")
    rows = []
    for q in db.parse_sql_queries()[:8]:
        result, ok = db_call(db.run_readonly_query, q["sql"])
        if ok:
            rows.append({"Check": q["id"], "What it checks": q["title"],
                         "Violations": len(result), "Result": "PASS" if not result else "FAIL"})
    st.caption("Database data-quality checks (SQL Q1-Q8):")
    st.dataframe(pd.DataFrame(rows), hide_index=True)


def page_employees():
    st.title("Employee Management")
    tab_add, tab_list, tab_edit, tab_delete = st.tabs(["Add", "View / Search", "Edit", "Delete"])
    with tab_add:
        with st.form("add_form"):
            data = employee_form("add")
            submitted = st.form_submit_button("Save employee")
        if submitted:
            _, ok = db_call(db.add_employee, data)
            if ok:
                st.success(f"Employee {data['employee_id'].strip()} saved.")
    with tab_list:
        term = st.text_input("Search by employee ID or name")
        rows, _ = db_call(db.list_employees, search=term)
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True)
        else:
            st.info("No matching employees.")
    ids = [e["employee_id"] for e in (db_call(db.list_employees)[0] or [])]
    with tab_edit:
        if not ids:
            st.info("No employees to edit.")
        else:
            chosen = st.selectbox("Employee to edit", ids, key="edit_choice")
            current = db.get_employee(chosen)
            with st.form(f"edit_form_{chosen}"):
                data = employee_form(f"edit_{chosen}", current)
                submitted = st.form_submit_button("Update employee")
            if submitted:
                _, ok = db_call(db.update_employee, chosen, data)
                if ok:
                    st.success("Employee updated. Refresh the list tab to see changes.")
    with tab_delete:
        if not ids:
            st.info("No employees to delete.")
        else:
            chosen = st.selectbox("Employee to delete", ids, key="delete_choice")
            confirmed = st.checkbox(f"I confirm I want to permanently delete {chosen}", key=f"confirm_{chosen}")
            if st.button("Delete employee"):
                _, ok = db_call(db.delete_employee, chosen, confirmed)
                if ok:
                    st.success(f"Employee {chosen} deleted.")
                


def page_validation():
    st.title("Business Rule Validation")
    st.info("VALIDATION ONLY: records entered here are checked against the rules but are **never saved** "
            "to the database. Use Employee Management to save real employee records.")
    c1, c2 = st.columns(2)
    data = {
        "employee_id": c1.text_input("Employee ID", "EMP-100"), "name": c2.text_input("Name", "Test User"),
        "age": c1.text_input("Age", "30"), "salary": c2.text_input("Monthly salary", "50000"),
        "department": c1.text_input("Department", "IT"), "employment_type": c2.text_input("Employment type", "Full-time"),
        "joining_date": c1.text_input("Joining date (YYYY-MM-DD)", str(date.today())),
        "status": c2.text_input("Status", "Active"),
    }
    if st.button("Validate"):
        ids, _ = db_call(db.existing_ids)
        results = rule_results(data, ids or set())
        failed = [r for r in results if r["Result"] == "FAIL"]
        runs = st.session_state.validation_runs
        runs["runs"] += 1
        runs["invalid" if failed else "valid"] += 1
        (st.error if failed else st.success)(
            f"{len(failed)} rule(s) FAILED - record would be rejected." if failed
            else "All rules PASSED - record would be accepted (but it was NOT saved).")
        st.dataframe(pd.DataFrame(results), hide_index=True)
        show_errors(validate_employee(data, ids or set()))
    with st.expander("Business rules reference"):
        st.table(pd.DataFrame(BUSINESS_RULES.items(), columns=["Rule", "Description"]))


def page_reports():
    st.title("Testing and Reports")
    if st.button("Generate missing reports / refresh summary"):
        st.success("Updated: " + ", ".join(rg.generate_all()))
    if not rg.SUITE_FILE.exists():
        st.info("Reports have not been generated yet. Click the button above.")
    else:
        c = rg.status_counts()
        cols = st.columns(6)
        for col, key in zip(cols, ["Total", "Pass", "Fail", "Blocked", "Not Executed", "Pass %"]):
            col.metric(key, c[key])
        st.caption("Counts are read from manual_test_suite.xlsx. Update the Status column there after testing, "
                   "then click the refresh button to rebuild test_summary.xlsx.")
    for label, path in [("Manual test suite", rg.SUITE_FILE), ("Defect log (contains SAMPLE defects)", rg.DEFECT_FILE),
                        ("Test summary", rg.SUMMARY_FILE)]:
        if path.exists():
            st.download_button(f"Download {label}", path.read_bytes(), file_name=path.name,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning(f"{path.name} has not been generated yet.")
    st.subheader("AI-assisted drafting (template-based, not a real AI model)")
    rule = st.selectbox("Business rule", list(BUSINESS_RULES))
    st.dataframe(pd.DataFrame(ai_assistant.draft_scenarios(rule)), hide_index=True)
    text = st.text_area("Paste defect descriptions (one per line)")
    if st.button("Summarise defects"):
        st.text(ai_assistant.summarize_defects(text.splitlines())["text"])


def page_sql():
    st.title("SQL Validation Reference")
    st.caption("Queries from sql/validation_queries.sql. Running them is read-only.")
    for q in db.parse_sql_queries():
        st.markdown(f"**{q['id']}** - {q['title']}")
        st.code(q["sql"], language="sql")
        if st.button(f"Run {q['id']}", key=f"run_{q['id']}"):
            result, ok = db_call(db.run_readonly_query, q["sql"])
            if ok:
                st.dataframe(pd.DataFrame(result), hide_index=True) if result else st.success(
                    "No rows returned (for Q1-Q8 this means PASS).")


PAGES = {"Dashboard": page_dashboard, "Employee Management": page_employees,
         "Business Rule Validation": page_validation, "Testing and Reports": page_reports,
         "SQL Validation Reference": page_sql}
st.sidebar.title("DemoCorp QA System")
PAGES[st.sidebar.radio("Navigate", list(PAGES))]()
