"""API de démonstration de suivi des défauts industriels."""
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
ISSUES=[{"id":1,"station":"L1","severity":"high","status":"open","description":"Défaut fictif"}]
def validate(issue):
    if issue.get("severity") not in ("low","medium","high"):raise ValueError("severity invalide")
    if not isinstance(issue.get("station"),str) or not issue["station"].strip():raise ValueError("station requise")
    if not isinstance(issue.get("description"),str) or not issue["description"].strip():raise ValueError("description requise")
    return True
def metrics(issues):
    return {"total":len(issues),"open":sum(x["status"]=="open" for x in issues),
            "by_station":{s:sum(x["station"]==s for x in issues) for s in sorted({x["station"] for x in issues})}}
class Handler(BaseHTTPRequestHandler):
    def respond(self,content,status=200):
        data=json.dumps(content,ensure_ascii=False).encode("utf-8")
        self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if self.path=="/api/issues":self.respond(ISSUES)
        elif self.path=="/api/kpis":self.respond(metrics(ISSUES))
        else:self.respond({"error":"not found"},404)
    def do_POST(self):
        if self.path!="/api/issues":return self.respond({"error":"not found"},404)
        try:
            n=int(self.headers.get("Content-Length","0"))
            if n<=0 or n>10000:raise ValueError("taille invalide")
            obj=json.loads(self.rfile.read(n));validate(obj)
            obj={**obj,"id":max((x["id"] for x in ISSUES),default=0)+1,"status":"open"}
            ISSUES.append(obj);self.respond(obj,201)
        except (ValueError,TypeError,json.JSONDecodeError) as exc:self.respond({"error":str(exc)},400)
if __name__=="__main__":
    print("http://127.0.0.1:8000/api/kpis")
    ThreadingHTTPServer(("127.0.0.1",8000),Handler).serve_forever()
