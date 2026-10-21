"""Offline quality gate for a synthetic document metadata migration."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

ALLOWED_TYPES = {"CONTRAT", "FACTURE", "EXPERTISE"}


def audit_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return row-level issues and a safe-to-export partition; never mutates input."""
    counts = Counter(record.get("document_id") for record in records if record.get("document_id"))
    checked = []
    for record in records:
        issues = []
        document_id = record.get("document_id", "").strip()
        if not document_id:
            issues.append("missing_document_id")
        elif counts[document_id] > 1:
            issues.append("duplicate_document_id")
        if not record.get("owner", "").strip():
            issues.append("missing_owner")
        if record.get("document_type") not in ALLOWED_TYPES:
            issues.append("unknown_document_type")
        try:
            date.fromisoformat(record.get("updated_at", ""))
        except ValueError:
            issues.append("invalid_updated_at")
        checked.append({"record": dict(record), "issues": issues})
    return {
        "checked": checked,
        "accepted": [row["record"] for row in checked if not row["issues"]],
        "rejected": [row for row in checked if row["issues"]],
    }
