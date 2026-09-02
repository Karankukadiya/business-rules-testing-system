"""Template-based test-scenario drafting and defect summarising.

NOTE: This is a deterministic, rule-based fallback (predefined templates + string
processing). It is NOT a generative AI model and needs no API key or network.
"""
from validation import BUSINESS_RULES

SCENARIO_TEMPLATES = {
    "BR-01": ["Save a record with an empty Employee ID - expect rejection naming Employee ID.",
              "Save a record whose ID already exists - expect a duplicate-ID error.",
              "Save an ID made only of spaces - expect rejection.",
              "Save a unique ID with leading/trailing spaces - expect it saved trimmed."],
    "BR-02": ["Save a record with an empty name - expect rejection naming Name.",
              "Save a name made only of spaces - expect rejection.",
              "Save a valid one-word name - expect success."],
    "BR-03": ["Test age 17 (just below minimum) - expect rejection.",
              "Test age 18 (minimum) - expect success.",
              "Test age 60 (maximum) - expect success.",
              "Test age 61 (just above maximum) - expect rejection.",
              "Test non-numeric age 'abc' - expect a clear numeric error."],
    "BR-04": ["Test salary 0 - expect rejection.", "Test salary 0.01 - expect success.",
              "Test salary 200000 - expect success.", "Test salary 200001 - expect rejection.",
              "Test negative salary -500 - expect rejection."],
    "BR-05": ["Select each allowed department - expect success for all five.",
              "Submit department 'Marketing' - expect rejection.",
              "Submit empty department - expect rejection."],
    "BR-06": ["Select each employment type - expect success for all three.",
              "Submit type 'Intern' - expect rejection."],
    "BR-07": ["Joining date today - expect success.", "Joining date tomorrow - expect rejection.",
              "Joining date in the past - expect success.",
              "Invalid date such as 2024-02-30 - expect a format error."],
    "BR-08": ["Select each status - expect success for all three.",
              "Submit status 'Retired' - expect rejection."],
    "BR-09": ["Submit an invalid record, then search for it - expect it is not in the database.",
              "Submit a record with several invalid fields - expect all errors shown and nothing saved."],
    "BR-10": ["Edit a name only - expect other records unchanged.",
              "Change an ID to another employee's ID - expect rejection.",
              "Save an edit without changing the ID - expect no false duplicate error."],
    "BR-11": ["Click Delete without confirming - expect the record remains.",
              "Confirm deletion - expect only that record removed.",
              "Cancel after clicking Delete - expect no change."],
    "BR-12": ["Submit an invalid record - expect each message to name the field.",
              "Check every message says how to fix the problem."],
}


def draft_scenarios(rule_id):
    """Return a list of draft scenario dicts for one business rule."""
    if rule_id not in BUSINESS_RULES:
        raise ValueError(f"Unknown rule '{rule_id}'. Choose from {', '.join(BUSINESS_RULES)}.")
    return [{"Draft ID": f"{rule_id}-D{i}", "Requirement": rule_id, "Scenario": text,
             "Note": "Template-based draft - review before use."}
            for i, text in enumerate(SCENARIO_TEMPLATES[rule_id], 1)]


def _severity_guess(text):
    lowered = text.lower()
    if any(w in lowered for w in ("crash", "data loss", "corrupt", "duplicate saved", "deleted without")):
        return "High"
    if any(w in lowered for w in ("accepted", "saved", "wrong", "incorrect", "not rejected")):
        return "Medium"
    return "Low"


def summarize_defects(descriptions):
    """Turn a list of defect descriptions (one per line/item) into a structured summary."""
    items = [d.strip() for d in descriptions if d and d.strip()]
    if not items:
        return {"total": 0, "by_severity": {}, "rules_mentioned": [], "text": "No defects supplied."}
    by_severity, rules = {}, set()
    lines = []
    for number, item in enumerate(items, 1):
        severity = _severity_guess(item)
        by_severity[severity] = by_severity.get(severity, 0) + 1
        rules.update(r for r in BUSINESS_RULES if r in item.upper())
        short = item if len(item) <= 90 else item[:87] + "..."
        lines.append(f"{number}. [{severity}] {short}")
    text = (f"Defect summary: {len(items)} defect(s). "
            + ", ".join(f"{k}: {v}" for k, v in sorted(by_severity.items())) + ".\n"
            + "\n".join(lines))
    return {"total": len(items), "by_severity": by_severity,
            "rules_mentioned": sorted(rules), "text": text}
