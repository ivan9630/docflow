"""Synthetic claims ETL: validate, quarantine and aggregate with SQLite."""
import sqlite3
from contextlib import closing
from common import number, text

def analyze(data):
    valid, rejected, seen = [], [], set()
    for index, row in enumerate(data["claims"]):
        try:
            claim_id = text(row["id"], "id")
            if claim_id in seen:
                raise ValueError("duplicate id")
            team = text(row["team"], "team")
            amount = number(row["amount_eur"], "amount_eur")
            delay = number(row["delay_days"], "delay_days")
            valid.append((claim_id, team, amount, delay))
            seen.add(claim_id)
        except (ValueError, KeyError, TypeError) as exc:
            rejected.append({"row": index, "reason": str(exc)})
    with closing(sqlite3.connect(":memory:")) as db:
        db.execute("CREATE TABLE claims(id TEXT PRIMARY KEY, team TEXT, amount REAL, delay REAL)")
        db.executemany("INSERT INTO claims VALUES(?,?,?,?)", valid)
        groups = db.execute("SELECT team, COUNT(*), ROUND(SUM(amount),2), ROUND(AVG(delay),2) "
                            "FROM claims GROUP BY team ORDER BY team").fetchall()
    return {"kpis": [dict(zip(("team", "count", "amount_eur", "average_delay_days"), row))
                     for row in groups], "accepted": len(valid), "rejected": rejected}
