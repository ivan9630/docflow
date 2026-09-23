"""Executable acceptance rules for a tiny order workflow."""
from common import integer, unique

def transition(state, event, stock, quantity):
    integer(stock, "stock")
    integer(quantity, "quantity", 1)
    transitions = {("new", "reserve"): "reserved", ("reserved", "pick"): "picked",
                   ("picked", "ship"): "shipped", ("reserved", "cancel"): "cancelled"}
    if (state, event) not in transitions:
        raise ValueError("invalid transition")
    if event == "reserve":
        if stock < quantity:
            raise ValueError("insufficient stock")
        stock -= quantity
    elif event == "cancel":
        stock += quantity
    return transitions[state, event], stock

def analyze(data):
    unique(data["scenarios"], "id")
    results = []
    for case in data["scenarios"]:
        try:
            state, stock = transition(case["state"], case["event"], case["stock"], case["quantity"])
            actual = {"state": state, "stock": stock}
        except ValueError as exc:
            actual = {"error": str(exc)}
        results.append({"id": case["id"], "actual": actual, "expected": case["expected"],
                        "passed": actual == case["expected"]})
    return {"scenarios": results, "release_ready": bool(results) and all(r["passed"] for r in results)}

