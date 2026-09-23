"""Synthetic N1 triage. SLA values are exercise conventions, not contracts."""
from datetime import datetime
from common import unique

def timestamp(value):
    date = datetime.fromisoformat(value)
    if date.tzinfo is None:
        raise ValueError("timezone required")
    return date

def analyze(data):
    now = timestamp(data["now"])
    unique(data["tickets"], "id")
    result = []
    for t in data["tickets"]:
        if t["impact"] not in ("single", "team", "site") or type(t["workaround"]) is not bool:
            raise ValueError("invalid impact/workaround")
        minutes = (now - timestamp(t["opened"])).total_seconds() / 60
        if minutes < 0:
            raise ValueError("ticket opened in future")
        priority = 1 if t["impact"] == "site" and not t["workaround"] else (
            2 if t["impact"] in ("team", "site") else 3)
        target = {1: 30, 2: 120, 3: 480}[priority]
        result.append({"id": t["id"], "priority": f"P{priority}",
                       "age_minutes": minutes, "target_minutes": target,
                       "escalate": minutes >= target})
    return {"tickets": sorted(result, key=lambda r: (r["priority"], -r["age_minutes"]))}

