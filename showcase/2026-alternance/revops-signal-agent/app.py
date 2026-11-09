"""Qualification de comptes et signaux de croissance fictifs."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Account:
    name:str
    employees:int
    sector:str
    funding_signal:bool=False
    hiring_signal:bool=False
def score(a):
    if not a.name or a.employees<0:raise ValueError("Compte invalide")
    n=30 if a.employees>=500 else 15 if a.employees>=100 else 0
    n+=20 if a.sector.lower() in ("tech","industry","education") else 0
    n+=25 if a.funding_signal else 0
    n+=25 if a.hiring_signal else 0
    return min(100,n)
def pipeline(accounts):
    seen=set();results=[]
    for a in accounts:
        s=score(a);k=a.name.strip().casefold()
        if k in seen:continue
        seen.add(k)
        results.append({"name":a.name,"score":s,"tier":"A" if s>=70 else "B" if s>=40 else "C",
                        "action":"Revue commerciale" if s>=40 else "Veille"})
    return sorted(results,key=lambda x:(-x["score"],x["name"]))
if __name__=="__main__":
    print(pipeline([Account("Campus Alpha",800,"education",True,True),Account("Beta",30,"services")]))
