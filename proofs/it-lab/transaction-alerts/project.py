"""Explainable outlier baseline. Not an AML model or fraud determination."""
from statistics import median
from common import number, unique

def analyze(data):
    history = [number(v, "history", .01) for v in data["history"]]
    if len(history) < 5:
        raise ValueError("at least five historical amounts required")
    center = median(history)
    mad = median(abs(x-center) for x in history)
    # A zero MAD cannot be a divisor. Use a documented monetary floor.
    scale = max(mad, 1.0)
    unique(data["transactions"], "id")
    alerts = []
    for row in data["transactions"]:
        amount = number(row["amount"], "amount", .01)
        score = abs(amount-center) / scale
        alerts.append({"id": row["id"], "amount": amount, "score": round(score, 3),
                       "review": score > 6, "reason": "distance from historical median"})
    return {"baseline_median": center, "median_absolute_deviation": mad,
            "scale": scale, "threshold": 6, "transactions": alerts}

