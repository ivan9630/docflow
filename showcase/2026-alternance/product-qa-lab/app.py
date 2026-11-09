"""Product QA Lab : triage de tickets et critères d'acceptation."""
import json
from collections import Counter

SEVERITY = {"bloquant": 4, "majeur": 3, "mineur": 2, "cosmetique": 1}

def priority(ticket):
    if ticket.get("severity") not in SEVERITY:
        raise ValueError("Sévérité inconnue")
    impact = max(1, min(int(ticket.get("affected_users", 1)), 1000))
    release = 2 if ticket.get("release_blocker") else 0
    return SEVERITY[ticket["severity"]] * 10 + min(impact // 100, 10) + release

def test_story(story):
    criteria = story.get("criteria", [])
    if not criteria:
        raise ValueError("Critères d'acceptation obligatoires")
    passed = sum(bool(c.get("passed")) for c in criteria)
    return {"story": story["name"], "passed": passed, "total": len(criteria),
            "ready": passed == len(criteria)}

def report(stories, tickets):
    tested = [test_story(s) for s in stories]
    ordered = sorted(tickets, key=priority, reverse=True)
    return {"tests": tested, "bugs": ordered, "status": dict(Counter("OK" if t["ready"] else "KO" for t in tested))}

if __name__ == "__main__":
    sample = report([{"name": "Parcours de réservation", "criteria": [{"passed": True}, {"passed": False}]}],
                    [{"id": "BUG-12", "severity": "bloquant", "affected_users": 380, "release_blocker": True}])
    print(json.dumps(sample, ensure_ascii=False, indent=2))
