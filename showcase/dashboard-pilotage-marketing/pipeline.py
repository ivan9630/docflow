"""Ingestion, contrôle qualité et modèle en étoile — données synthétiques."""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "campagnes_demo.csv"
OUT = ROOT / "output"

def clean_campaigns(path=DATA):
    df = pd.read_csv(path)
    df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
    num = ["clics", "impressions", "CTR", "ROI", "conversions", "depenses", "revenus"]
    for name in num:
        df[name] = pd.to_numeric(df[name], errors="coerce")
    invalid = (
        df["date_parsed"].isna()
        | df["segment"].isna() | df["segment"].astype(str).str.strip().eq("")
        | df[num].isna().any(axis=1)
        | (df["impressions"] <= 0) | (df["clics"] < 0) | (df["clics"] > df["impressions"])
        | (df["conversions"] < 0) | (df["conversions"] > df["clics"])
        | (df["depenses"] <= 0) | (df["revenus"] < 0)
    )
    clean, anomalies = df.loc[~invalid].copy(), df.loc[invalid].copy()
    clean["CTR_calcule"] = 100 * clean["clics"] / clean["impressions"]
    clean["ROI_calcule"] = 100 * (clean["revenus"] - clean["depenses"]) / clean["depenses"]
    clean["taux_conversion"] = 100 * clean["conversions"] / clean["clics"].where(clean["clics"] != 0)
    clean["date"] = clean["date_parsed"].dt.strftime("%Y-%m-%d")
    return clean.drop(columns="date_parsed"), anomalies

def build_star_schema(clean, out=OUT):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    dimensions = {}
    for entity in ("campagne", "segment", "canal", "date"):
        values = sorted(clean[entity].unique())
        dim = pd.DataFrame({entity + "_id": range(1, len(values) + 1), entity: values})
        dimensions[entity] = dim
        dim.to_csv(out / ("dim_" + entity + ".csv"), index=False)
    fact = clean[["id_ligne", "clics", "impressions", "conversions", "depenses", "revenus"]].copy()
    for entity, dim in dimensions.items():
        fact[entity + "_id"] = clean[entity].map(dict(zip(dim[entity], dim[entity + "_id"])))
    fact.to_csv(out / "fact_performance.csv", index=False)
    with sqlite3.connect(out / "marketing_demo.sqlite") as conn:
        for entity, dim in dimensions.items():
            dim.to_sql("dim_" + entity, conn, index=False, if_exists="replace")
        fact.to_sql("fact_performance", conn, index=False, if_exists="replace")
    return fact

def metrics(df):
    imp, clicks, conv = df["impressions"].sum(), df["clics"].sum(), df["conversions"].sum()
    spent, revenue = df["depenses"].sum(), df["revenus"].sum()
    return {"impressions": int(imp), "clics": int(clicks), "conversions": int(conv),
            "CTR_pct": round(100 * clicks / imp, 2),
            "conversion_pct": round(100 * conv / clicks, 2) if clicks else None,
            "ROI_pct": round(100 * (revenue - spent) / spent, 2)}

def main():
    OUT.mkdir(exist_ok=True)
    cleaned, errors = clean_campaigns()
    assert len(cleaned) == 600 and len(errors) == 5, "Contrôle qualité inattendu"
    cleaned.to_csv(OUT / "campagnes_fiabilisees.csv", index=False)
    errors.to_csv(OUT / "anomalies_detectees.csv", index=False)
    build_star_schema(cleaned)
    overall = metrics(cleaned)
    print("Source:", len(cleaned) + len(errors), "Fiabilisées:", len(cleaned), "Anomalies:", len(errors))
    print("Global:", overall)
    print("Par campagne:")
    for name, group in cleaned.groupby("campagne"):
        print(" ", name, metrics(group))
    print("Par segment:")
    for name, group in cleaned.groupby("segment"):
        print(" ", name, metrics(group))

if __name__ == "__main__":
    main()
