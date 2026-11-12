"""Génération d'un flux client CSV à partir de données CRM validées (mode local)."""
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
RULES=ROOT/'data/regles_livraison_demo.json'


def prepare_delivery(contacts:pd.DataFrame, rules_path=RULES):
    rules=json.loads(Path(rules_path).read_text(encoding='utf-8'))
    candidates=contacts.copy()
    for field in ('secteur','region','segment'):
        allowed=rules.get(field)
        if allowed:
            candidates=candidates[candidates[field].isin(allowed)]
    candidates=candidates[candidates['score_qualite']>=rules.get('qualite_min',0)]
    candidates=candidates.sort_values(['score_conversion_ml','score_qualite'],ascending=False)
    candidates=candidates.head(rules.get('volume_max',100))
    cols=['lead_id','email','entreprise','secteur','region','segment','score_qualite','score_conversion_ml']
    return candidates[cols].reset_index(drop=True)


if __name__=='__main__':
    from .pipeline import load_clean,enrich
    source=load_clean()[0]
    scored,_=enrich(source)
    out=ROOT/'output/livraison_client_demo.csv'
    out.parent.mkdir(parents=True,exist_ok=True)
    prepare_delivery(scored).to_csv(out,index=False)
    print(f'Flux de démonstration créé : {out}')
