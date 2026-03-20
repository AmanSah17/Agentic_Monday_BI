from __future__ import annotations

import re

FORBIDDEN_SQL_PATTERNS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bATTACH\b",
    r"\bDETACH\b",
]


def validate_read_only_sql(sql: str) -> tuple[bool, str | None]:
    cleaned = sql.strip().strip(";")
    if not cleaned:
        return False, "Empty SQL query."

    start_ok = cleaned.upper().startswith("SELECT") or cleaned.upper().startswith("WITH")
    if not start_ok:
        return False, "Only SELECT/WITH read-only SQL is allowed."

    for pattern in FORBIDDEN_SQL_PATTERNS:
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            return False, f"Forbidden SQL pattern found: {pattern}"

    return True, None

