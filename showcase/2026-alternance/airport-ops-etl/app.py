"""ETL miniature et tableaux d'indicateurs pour des opérations fictives."""
from datetime import datetime
import sqlite3
def load_events(conn, events):
    conn.execute("CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, zone TEXT NOT NULL, ts TEXT NOT NULL, delay_min INTEGER NOT NULL)")
    loaded=0; rejected=[]
    for e in events:
        try:
            datetime.fromisoformat(e["ts"])
            delay=int(e["delay_min"])
            if delay<0 or not e["zone"]: raise ValueError
            conn.execute("INSERT INTO events VALUES (?, ?, ?, ?)",(e["id"],e["zone"],e["ts"],delay))
            loaded+=1
        except (KeyError,ValueError,sqlite3.IntegrityError): rejected.append(e.get("id","inconnu"))
    conn.commit()
    return loaded,rejected
def kpis(conn):
    return [{"zone":z,"events":n,"avg_delay_min":round(avg,2)} for z,n,avg in
            conn.execute("SELECT zone, COUNT(*), AVG(delay_min) FROM events GROUP BY zone ORDER BY zone")]
if __name__=="__main__":
    db=sqlite3.connect(":memory:")
    print(load_events(db,[{"id":"E01","zone":"T1","ts":"2026-11-07T08:20","delay_min":8},
                         {"id":"E02","zone":"T1","ts":"2026-11-07T09:10","delay_min":15}]))
    print(kpis(db))
