"""Synthetic medal ETL using Python's built-in SQLite; no real Olympic data."""

from __future__ import annotations

import sqlite3

CREATE_SQL = """
CREATE TABLE medals (
    athlete_id TEXT NOT NULL,
    country TEXT NOT NULL,
    event TEXT NOT NULL,
    year INTEGER NOT NULL CHECK (year BETWEEN 1896 AND 2024),
    medal TEXT NOT NULL CHECK (medal IN ('Gold', 'Silver', 'Bronze')),
    PRIMARY KEY (athlete_id, event, year)
)
"""
AGGREGATE_SQL = """
SELECT country, COUNT(*) AS medals,
       SUM(CASE WHEN medal = 'Gold' THEN 1 ELSE 0 END) AS gold_medals
FROM medals
GROUP BY country
ORDER BY medals DESC, country ASC
"""


def run_pipeline(rows: list[dict[str, str | int]]) -> dict[str, object]:
    connection = sqlite3.connect(":memory:")
    connection.execute(CREATE_SQL)
    rejected = []
    for row in rows:
        try:
            connection.execute(
                "INSERT INTO medals VALUES (?, ?, ?, ?, ?)",
                (row["athlete_id"], row["country"], row["event"], int(row["year"]), row["medal"]),
            )
        except (KeyError, ValueError, sqlite3.IntegrityError) as error:
            rejected.append({"row": dict(row), "reason": str(error)})
    result = [dict(zip(("country", "medals", "gold_medals"), row))
              for row in connection.execute(AGGREGATE_SQL)]
    accepted = connection.execute("SELECT COUNT(*) FROM medals").fetchone()[0]
    connection.close()
    return {"accepted_count": accepted, "rejected": rejected, "by_country": result}
