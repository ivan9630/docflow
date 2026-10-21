"""Deterministic workload/capacity comparison for a fictitious planning case."""


def project_months(rows: list[dict[str, int | str]]) -> list[dict[str, int | str | None]]:
    if not rows:
        raise ValueError("at least one month is required")
    result = []
    for row in rows:
        demand, capacity = row["demand_days"], row["capacity_days"]
        if not isinstance(demand, int) or not isinstance(capacity, int) or demand < 0 or capacity < 0:
            raise ValueError("demand and capacity must be non-negative integers")
        result.append({
            "month": row["month"],
            "demand_days": demand,
            "capacity_days": capacity,
            "gap_days": demand - capacity,
            "utilization_pct": round(demand / capacity * 100) if capacity else None,
        })
    return result
