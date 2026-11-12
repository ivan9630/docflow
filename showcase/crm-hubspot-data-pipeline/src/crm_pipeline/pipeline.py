"""Pipeline CRM : déduplication, qualité, segmentation, scoring ML, SQLite et exports."""
from __future__ import annotations
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, balanced_accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT=Path(__file__).resolve().parents[2]
IN=ROOT/'data/leads_demo.csv'
OUT=ROOT/'output'
SCHEMA=ROOT/'sql/star_schema.sql'
CATEGORICAL=['source','secteur','region']
NUMERIC=['nb_interactions','pages_visitees','taille_entreprise','budget_indicatif','jours_depuis_interaction']
NUM_ALL=['nb_interactions','pages_visitees','taille_entreprise','budget_indicatif','contacts_livres',
         'contacts_convertis','litiges','cout_acquisition','ca_facture','montant_facture']


def load_clean(path=IN):
    df=pd.read_csv(path,dtype={'lead_id':'str','email':'str'},keep_default_na=False)
    df['email']=df['email'].astype(str).str.strip().str.lower()
    df['derniere_interaction_dt']=pd.to_datetime(df['derniere_interaction'],errors='coerce')
    for k in NUM_ALL:df[k]=pd.to_numeric(df[k],errors='coerce')
    fail=pd.Series('',index=df.index,dtype='object')
    def reject(cond,reason):
        nonlocal fail
        fail=fail.mask(cond & fail.eq(''),reason)
    reject(~df.email.str.match(r'^[^\s@]+@[^\s@]+\.[A-Za-z]{2,}$',na=False),'EMAIL_INVALIDE')
    reject(df.derniere_interaction_dt.isna(),'DATE_INVALIDE')
    reject(df[NUM_ALL].isna().any(axis=1),'DONNEE_MANQUANTE')
    reject((df['cout_acquisition']<0)|(df['ca_facture']<0)|(df['montant_facture']<0),'MONTANT_INVALIDE')
    reject((df['contacts_convertis']<0)|(df['contacts_convertis']>df['contacts_livres']),'CONVERSION_INVALIDE')
    reject((df['contacts_livres']<0)|(df['nb_interactions']<0)|(df['pages_visitees']<0),'VALEUR_INVALIDE')
    invalid=df.loc[fail.ne('')].copy()
    invalid['motif_rejet']=fail.loc[fail.ne('')].values
    good=df.loc[fail.eq('')].copy()
    good=good.sort_values(['derniere_interaction_dt','lead_id'],ascending=[False,True],kind='stable')
    duplicates=good.loc[good.duplicated('email',keep='first')].copy()
    duplicates['motif_rejet']='DOUBLON_EMAIL'
    valid=good.loc[~good.duplicated('email',keep='first')].copy()
    valid['derniere_interaction']=valid['derniere_interaction_dt'].dt.strftime('%Y-%m-%d')
    valid=valid.drop(columns='derniere_interaction_dt')
    audit=pd.concat([invalid,duplicates],ignore_index=True)
    audit=audit.drop(columns='derniere_interaction_dt')
    assert len(df)==len(valid)+len(audit)
    return valid.reset_index(drop=True),audit.reset_index(drop=True),len(df)


def score_quality(frame):
    d=frame.copy()
    result=(100
       -d['email'].str.endswith('@example.com').astype(int)*0 # Démo: domaines fictifs attendus
       -(d['nb_interactions']==0).astype(int)*20
       -(d['pages_visitees']<3).astype(int)*15
       -(d['budget_indicatif']<300).astype(int)*15
       -(d['derniere_interaction'].lt('2026-09-01')).astype(int)*10
       -(d['litiges']>0).astype(int)*15)
    return result.clip(lower=0,upper=100).astype(float)


def train_ml(d):
    """Classification supervisée uniquement sur le jeu artificiel, jamais revendiquée en production."""
    x=d[CATEGORICAL+NUMERIC].copy()
    y=(d['contacts_convertis']>0).astype(int)
    if y.nunique()<2:raise ValueError('Deux classes requises pour entraîner le classifieur')
    Xtr,Xte,Ytr,Yte=train_test_split(x,y,random_state=42,test_size=.25,stratify=y)
    pp=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore'),CATEGORICAL),
                          ('num',StandardScaler(),NUMERIC)])
    model=Pipeline([('preprocess',pp),('model',LogisticRegression(max_iter=300,random_state=42))])
    model.fit(Xtr,Ytr)
    proba=model.predict_proba(Xte)[:,1]
    metrics={'train_rows':len(Xtr),'test_rows':len(Xte),
             'roc_auc_synthetique':round(float(roc_auc_score(Yte,proba)),3),
             'balanced_accuracy_synthetique':round(float(balanced_accuracy_score(Yte,proba>=.5)),3)}
    model.fit(x,y)
    return model.predict_proba(x)[:,1],metrics


def enrich(df):
    d=df.copy()
    ref=pd.Timestamp('2026-11-12')
    d['jours_depuis_interaction']=(ref-pd.to_datetime(d['derniere_interaction'])).dt.days.clip(lower=0)
    d['score_qualite']=score_quality(d)
    scores,quality=train_ml(d)
    d['score_conversion_ml']=(scores*100).round(1)
    d['segment']=pd.qcut(d['score_conversion_ml'].rank(method='first'),q=3,labels=['À réengager','À qualifier','Prioritaire']).astype(str)
    d['ecart_facturation']=(d['montant_facture']-d['ca_facture']).round(2)
    return d,quality


def write_sqlite(d,path=OUT/'hubspot_demo.sqlite'):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.unlink(missing_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding='utf-8'))
        fact=d[['lead_id','nom','email','entreprise','derniere_interaction',*NUM_ALL,'score_qualite','score_conversion_ml','segment','ecart_facturation']].copy()
        for dim in ['source','secteur','region','statut']:
            values=sorted(d[dim].unique())
            mapping={v:i+1 for i,v in enumerate(values)}
            table=pd.DataFrame({dim+'_id':list(mapping.values()),dim:list(mapping.keys())})
            table.to_sql('dim_'+dim,conn,if_exists='append',index=False)
            fact[dim+'_id']=d[dim].map(mapping).values
        fact.to_sql('fact_leads',conn,if_exists='append',index=False)
        assert conn.execute('SELECT COUNT(*) FROM fact_leads').fetchone()[0]==len(d)
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()


def summary_by(d,axis):
    rows=[]
    for name,g in d.groupby(axis):
        volume=int(g['contacts_livres'].sum());converted=int(g['contacts_convertis'].sum())
        amount=float(g['ca_facture'].sum());cost=float(g['cout_acquisition'].sum())
        rows.append({axis:name,'leads':len(g),'livraisons':volume,'transformations':converted,
                     'taux_transformation_pct':round(100*converted/volume,2) if volume else 0,
                     'cout_par_lead_eur':round(cost/len(g),2),'marge_eur':round(amount-cost,2),
                     'litiges':int(g['litiges'].sum())})
    return pd.DataFrame(rows)


def run(path=IN,out=OUT):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    d,errors,source_count=load_clean(path)
    enriched,ml=train_ml_enrich(d)
    enriched.to_csv(out/'contacts_fiabilises_scores.csv',index=False)
    errors.to_csv(out/'rejets_audit.csv',index=False)
    for dim in ['source','segment','secteur','statut']:
        summary_by(enriched,dim).to_csv(out/f'kpi_{dim}.csv',index=False)
    write_sqlite(enriched,out/'hubspot_demo.sqlite')
    totals={
       'sources':source_count,'anomalies':len(errors),'doublons':int((errors['motif_rejet']=='DOUBLON_EMAIL').sum()),
       'rejets_invalides':int((errors['motif_rejet']!='DOUBLON_EMAIL').sum()),'contacts_uniques':len(enriched),
       'deduplication_pct':round(100*(errors['motif_rejet']=='DOUBLON_EMAIL').sum()/source_count,2),
       'score_qualite_moyen':round(float(enriched['score_qualite'].mean()),2),
       'segments':int(enriched['segment'].nunique()),
       'contacts_automatises':len(enriched),
       'livraisons':int(enriched['contacts_livres'].sum()),
       'transformations':int(enriched['contacts_convertis'].sum()),
       'cout_par_lead_eur':round(float(enriched['cout_acquisition'].sum())/len(enriched),2),
       'litiges':int(enriched['litiges'].sum()),'ecarts_facturation':int((enriched['ecart_facturation'].abs()>.01).sum()),
       'ml':ml}
    (out/'resultats.json').write_text(json.dumps(totals,ensure_ascii=False,indent=2),encoding='utf-8')
    return totals


def train_ml_enrich(d):
    return enrich(d)

if __name__=='__main__':
    print(json.dumps(run(),ensure_ascii=False,indent=2))
