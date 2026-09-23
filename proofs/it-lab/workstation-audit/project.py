"""Offline inventory audit; never inspects the host or modifies settings."""
from common import unique, number, text

def analyze(data):
    unique(data["devices"], "id")
    report = []
    for d in data["devices"]:
        text(d["os"], "os")
        free = number(d["disk_free_gb"], "disk_free_gb")
        total = number(d["disk_total_gb"], "disk_total_gb", 1)
        ram = number(d["ram_gb"], "ram_gb")
        if free > total or type(d["encrypted"]) is not bool:
            raise ValueError("inconsistent disk or encryption boolean")
        actions = []
        if free / total < .10:
            actions.append("Review disk usage with user; do not delete automatically")
        if ram < 8:
            actions.append("Confirm application memory requirements")
        if not d["encrypted"]:
            actions.append("Escalate encryption review to authorized administrator")
        report.append({"id": d["id"], "os": d["os"], "actions": actions,
                       "status": "review" if actions else "healthy"})
    return {"devices": report, "review_count": sum(x["status"] == "review" for x in report)}

