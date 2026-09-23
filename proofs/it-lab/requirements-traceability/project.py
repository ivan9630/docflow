"""Link requirements to acceptance evidence, not just a pass percentage."""
from common import unique, text

def analyze(data):
    requirements, tests = data["requirements"], data["tests"]
    ids = unique(requirements, "id")
    unique(tests, "id")
    for test in tests:
        if test["requirement"] not in ids or test["status"] not in ("pass", "fail", "not_run"):
            raise ValueError("unknown requirement or test status")
    report = []
    for requirement in requirements:
        text(requirement["description"], "description")
        linked = [t for t in tests if t["requirement"] == requirement["id"]]
        state = "uncovered" if not linked else (
            "failed" if any(t["status"] == "fail" for t in linked) else
            "pending" if any(t["status"] == "not_run" for t in linked) else "accepted")
        report.append({"requirement": requirement["id"], "status": state,
                       "tests": [t["id"] for t in linked]})
    accepted = sum(r["status"] == "accepted" for r in report)
    return {"requirements": report, "accepted": accepted, "total": len(report),
            "release_ready": bool(report) and accepted == len(report)}

