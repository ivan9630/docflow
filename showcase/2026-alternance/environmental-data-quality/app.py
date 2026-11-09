"""Contrôles qualité de données environnementales fictives."""
import csv
from io import StringIO
FACTORS = {"electricite_kwh":0.05,"diesel_l":2.68,"train_km":0.03}
def ingest(text):
    rows=list(csv.DictReader(StringIO(text)))
    errors=[];clean=[];seen=set()
    for i,row in enumerate(rows,2):
        key=(row.get("site","").strip(),row.get("month","").strip(),row.get("metric","").strip())
        if any(not x for x in key): errors.append((i,"dimension manquante"));continue
        if key in seen: errors.append((i,"doublon"));continue
        seen.add(key)
        if key[2] not in FACTORS: errors.append((i,"unité non reconnue"));continue
        try:
            value=float(row["value"])
            if value<0:raise ValueError
        except (ValueError,TypeError,KeyError): errors.append((i,"valeur invalide"));continue
        clean.append({"site":key[0],"month":key[1],"metric":key[2],"value":value,
                      "estimate_kgco2e":round(value*FACTORS[key[2]],3)})
    return clean,errors
def summary(rows):
    out={}
    for x in rows:out[x["site"]]=round(out.get(x["site"],0)+x["estimate_kgco2e"],3)
    return out
if __name__=="__main__":
    data="site,month,metric,value\nParis,2026-10,electricite_kwh,1200\nLyon,2026-10,train_km,200\n"
    rows,errors=ingest(data)
    print({"quality_errors":errors,"estimates":summary(rows)})
