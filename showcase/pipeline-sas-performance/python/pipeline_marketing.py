"""Pipeline de pilotage marketing : qualité, indicateurs, études d'impact, SQL."""
from __future__ import annotations
import argparse
import csv
import json
import sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "campagnes_ft_pro_demo.csv"
OUT = ROOT / "output"
SCHEMA = ROOT / "sql" / "star_schema.sql"
REGIONS = {"Ile-de-France", "Hauts-de-France", "Bretagne", "Occitanie", "Auvergne-Rhone-Alpes"}
SECTEURS = {"BTP", "Sante", "Industrie", "Commerce", "Numerique"}
CAMPAGNES = {"FT-Pro-Acquisition", "FT-Pro-Relance", "FT-Pro-Secteurs"}

def validate(df: pd.DataFrame):
    """Un seul motif principal de rejet par ligne, pour audit sans double comptage."""
    df = df.copy()
    reasons = pd.Series("", index=df.index, dtype="object")
    def flag(mask, label):
        nonlocal reasons
        reasons = reasons.mask(mask & reasons.eq(""), label)
    flag(df.duplicated(subset=["record_id"], keep="first"), "DOUBLON_ID")
    flag(~df["region"].isin(REGIONS), "REGION_INCONNUE")
    flag(~df["secteur"].isin(SECTEURS) | ~df["campagne"].isin(CAMPAGNES), "REFERENTIEL_INCONNU")
    parsed = pd.to_datetime(df["semaine"], format="%Y-%m-%d", errors="coerce")
    flag(parsed.isna(), "DATE_INVALIDE")
    for column in ["record_id","expose","post","impressions","clics","contacts","rdv","cout_eur"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    flag(df[["impressions","clics","contacts","rdv","cout_eur"]].isna().any(axis=1), "CHAMPS_MANQUANTS")
    flag((df["impressions"] <= 0) | (df["clics"] < 0) | (df["clics"] > df["impressions"]), "CLICS_IMPRESSIONS_INCOHERENTS")
    flag((df["contacts"] < 0) | (df["contacts"] > df["clics"]) | (df["rdv"] < 0) | (df["rdv"] > df["contacts"]), "PARCOURS_INCOHERENT")
    flag(df["cout_eur"] < 0, "COUT_NEGATIF")
    flag(~df["expose"].isin([0,1]) | ~df["post"].isin([0,1]), "GROUPE_INCOHERENT")
    errors=df.loc[reasons.ne("")].copy()
    errors["motif_rejet"]=reasons.loc[reasons.ne("")].values
    clean=df.loc[reasons.eq("")].copy()
    assert len(clean)+len(errors)==len(df)
    return clean,errors

def ratio(num, den, multiplier=1.0):
    return round(float(num)/float(den)*multiplier,4) if den else None

def metrics(df):
    impressions=int(df["impressions"].sum())
    clicks=int(df["clics"].sum())
    contacts=int(df["contacts"].sum())
    rdv=int(df["rdv"].sum())
    cout=float(df["cout_eur"].sum())
    return {"observations":len(df),"impressions":impressions,"clics":clicks,"contacts":contacts,
        "rdv":rdv,"depenses_eur":round(cout,2),
        "ctr_pct":ratio(clicks,impressions,100),
        "contact_par_clic_pct":ratio(contacts,clicks,100),
        "rdv_par_contact_pct":ratio(rdv,contacts,100),
        "cout_par_rdv_eur":ratio(cout,rdv),
        "rdv_pour_1000_impressions":ratio(rdv,impressions,1000)}

def summary_table(df, dimensions):
    output=[]
    for key,subset in df.groupby(dimensions,sort=True,dropna=False):
        if not isinstance(key,tuple): key=(key,)
        output.append(dict(zip(dimensions,key),**metrics(subset)))
    return pd.DataFrame(output)

def impact_did(df):
    """Double différence descriptive ; ne démontre pas une causalité."""
    pre_t=metrics(df[(df.expose==1)&(df.post==0)])["rdv_pour_1000_impressions"]
    post_t=metrics(df[(df.expose==1)&(df.post==1)])["rdv_pour_1000_impressions"]
    pre_c=metrics(df[(df.expose==0)&(df.post==0)])["rdv_pour_1000_impressions"]
    post_c=metrics(df[(df.expose==0)&(df.post==1)])["rdv_pour_1000_impressions"]
    return {"avant_exposes":pre_t,"apres_exposes":post_t,
            "avant_temoins":pre_c,"apres_temoins":post_c,
            "difference_de_differences":round((post_t-pre_t)-(post_c-pre_c),4),
            "unite":"rendez-vous pour 1000 impressions","interpretation":"descriptive, non causale"}

def create_star_schema(df, out=OUT):
    out.mkdir(exist_ok=True,parents=True)
    dims = {}
    for name in ["region","secteur","campagne","segment","canal","semaine"]:
        dim=pd.DataFrame({name:sorted(df[name].unique())})
        dim[name+"_id"]=range(1,len(dim)+1)
        dims[name]=dim
        dim.to_csv(out/("dim_"+name+".csv"),index=False)
    fact=df[["record_id","impressions","clics","contacts","rdv","cout_eur","expose","post"]].copy()
    for name,dim in dims.items():
        fact[name+"_id"]=df[name].map(dict(zip(dim[name],dim[name+"_id"])))
    fact.to_csv(out/"fact_campagnes.csv",index=False)
    db_path = out / "pilotage_campagnes.sqlite"
    db_path.unlink(missing_ok=True)  # Exécution reproductible, sans doublons SQL lors des relances
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        for name,dim in dims.items():
            dim.to_sql("dim_"+name,conn,if_exists="append",index=False)
        fact.to_sql("fact_campagnes",conn,if_exists="append",index=False)
        fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        assert not fk_errors, f"Foreign-key violations: {fk_errors}"
    return fact

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    source=pd.read_csv(RAW)
    clean,errors=validate(source)
    if len(source)!=605 or len(clean)!=600 or len(errors)!=5:
        raise ValueError(f"Contrôle qualité inattendu: {len(source)}/{len(clean)}/{len(errors)}")
    clean.to_csv(OUT/"campagnes_fiabilisees.csv",index=False)
    errors.to_csv(OUT/"anomalies_campagnes.csv",index=False)
    detail={}
    for axis in ["region","secteur","campagne","canal","semaine"]:
        t=summary_table(clean,[axis])
        t.to_csv(OUT/("kpi_"+axis+".csv"),index=False)
        detail[axis]=t.to_dict(orient="records")
    summary_table(clean,["region","secteur","campagne"]).to_csv(OUT/"kpi_local_sectoriel.csv",index=False)
    fact=create_star_schema(clean)
    result={"audit":{"source":len(source),"valides":len(clean),"anomalies":len(errors)},
            "national":metrics(clean),"impact":impact_did(clean),"nombre_lignes_faits":len(fact)}
    (OUT/"synthese.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    return result

def main():
    result=build()
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
