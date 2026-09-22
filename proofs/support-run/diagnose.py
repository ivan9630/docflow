"""Offline RUN exercise: validate a synthetic snapshot; never contact production."""
import argparse
import json
from pathlib import Path

SERVICES = ("api", "database", "queue", "worker", "storage")


def diagnose(snapshot):
    if not isinstance(snapshot, dict) or set(snapshot) != set(SERVICES):
        raise ValueError("Exactly api, database, queue, worker and storage are required")
    if any(type(value) is not bool for value in snapshot.values()):
        raise ValueError("Statuses must be JSON booleans, not strings or null")
    failed = [name for name in SERVICES if not snapshot[name]]
    if not failed:
        return {"severity": "OK", "failed": [], "next_steps": [
            "Record the healthy snapshot; this does not prove end-to-end processing."]}
    steps = []
    # Dependency-first triage; these are checks, not a claim of root cause.
    for name, advice in (
        ("database", "Check database availability and application connection errors."),
        ("queue", "Check queue availability and pending jobs before retrying."),
        ("storage", "Check object storage availability and access configuration."),
        ("worker", "Inspect worker logs and upstream dependencies; do not purge jobs."),
        ("api", "Inspect API logs and database connectivity; reproduce with a test request."),
    ):
        if name in failed:
            steps.append(advice)
    steps.append("Capture redacted evidence and escalate; no automatic restart or deletion.")
    return {"severity": "P1" if "api" in failed or "database" in failed else "P2",
            "failed": failed, "next_steps": steps}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path, help="Synthetic service-status JSON")
    args = parser.parse_args()
    try:
        result = diagnose(json.loads(args.snapshot.read_text(encoding="utf-8")))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Invalid snapshot: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
