"""Local-only HTTP/SQLite demo. No authentication: do not expose publicly."""
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from common import text

def analyze(data):
    return {"title": text(data["title"], "title"), "status": "open"}

def make_server(port=0):
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.execute("CREATE TABLE ticket(id INTEGER PRIMARY KEY, title TEXT, status TEXT)")
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def send(self, code, data, content_type="application/json"):
            payload = data.encode() if isinstance(data, str) else json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(payload)
        def do_GET(self):
            if self.path == "/":
                self.send(200, Path(__file__).with_name("index.html").read_text(encoding="utf-8"), "text/html")
            elif self.path == "/api/tickets":
                self.send(200, [dict(zip(("id", "title", "status"), r))
                                for r in db.execute("SELECT * FROM ticket ORDER BY id")])
            else:
                self.send(404, {"error": "not found"})
        def do_POST(self):
            if self.path != "/api/tickets":
                return self.send(404, {"error": "not found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096:
                    raise ValueError("body size must be 1..4096 bytes")
                ticket = analyze(json.loads(self.rfile.read(length)))
                if len(ticket["title"]) > 200:
                    raise ValueError("title too long")
                cursor = db.execute("INSERT INTO ticket(title,status) VALUES(?,?)",
                                    (ticket["title"], ticket["status"]))
                db.commit()
                self.send(201, {"id": cursor.lastrowid, **ticket})
            except (ValueError, KeyError, TypeError) as exc:
                self.send(400, {"error": str(exc)})
    server = HTTPServer(("127.0.0.1", port), Handler)
    server.database = db
    return server

if __name__ == "__main__":
    server = make_server(8765)
    print("Local demo: http://127.0.0.1:8765 (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.database.close()

