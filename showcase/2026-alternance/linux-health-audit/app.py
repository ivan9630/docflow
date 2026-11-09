"""Audit pédagogique de métadonnées système synthétiques."""
import json
from datetime import date
def audit(hosts,today=date(2026,11,9)):
    findings=[]
    for h in hosts:
        name=h.get("host","inconnu")
        if not isinstance(h.get("disk_pct"),int) or not 0<=h["disk_pct"]<=100:
            findings.append({"host":name,"severity":"error","issue":"Donnée disque invalide"});continue
        if h["disk_pct"]>=90:findings.append({"host":name,"severity":"high","issue":"Disque critique"})
        if not h.get("backups_enabled"):findings.append({"host":name,"severity":"high","issue":"Sauvegarde désactivée"})
        try:
            last=date.fromisoformat(h.get("last_patch",""))
            if (today-last).days>60:findings.append({"host":name,"severity":"medium","issue":"Correctifs anciens"})
        except ValueError:findings.append({"host":name,"severity":"error","issue":"Date invalide"})
    return findings
def summary(hosts):
    rows=audit(hosts)
    return {"hosts":len(hosts),"findings":len(rows),"high":sum(x["severity"]=="high" for x in rows),"details":rows}
if __name__=="__main__":
    print(json.dumps(summary([{"host":"srv-01","disk_pct":95,"backups_enabled":True,"last_patch":"2026-10-15"},
                              {"host":"srv-02","disk_pct":35,"backups_enabled":False,"last_patch":"2026-05-01"}]),indent=2,ensure_ascii=False))
