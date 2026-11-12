import sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/"output/catalogue.sqlite"
SQL="""CREATE TABLE IF NOT EXISTS fiches (produit_id TEXT PRIMARY KEY, nom TEXT NOT NULL, marque TEXT,
 categorie TEXT, defauts TEXT, valeur_estimee_eur REAL, recommandation TEXT, validation_humaine INTEGER)"""
def store(x,path=DEFAULT):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute(SQL)
        db.execute("""INSERT INTO fiches VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(produit_id) DO UPDATE SET
         nom=excluded.nom,marque=excluded.marque,categorie=excluded.categorie,defauts=excluded.defauts,
         valeur_estimee_eur=excluded.valeur_estimee_eur,recommandation=excluded.recommandation,
         validation_humaine=excluded.validation_humaine""",
         tuple(x.get(k) for k in ("produit_id","nom","marque","categorie","defauts","valeur_estimee_eur","recommandation","validation_humaine")))
