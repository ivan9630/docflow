"""Web analytics monthly KPIs; no third-party dependency or live traffic."""
from pathlib import Path
import csv
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]

def load_sessions(path=None):
    path=Path(path or ROOT/'data/sessions_demo.csv')
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def metrics(rows):
    n=len(rows)
    pageviews=sum(int(x['pageviews']) for x in rows)
    bounce=sum(int(x['bounced']) for x in rows)
    leads=sum(int(x['lead_converted']) for x in rows)
    durations=sum(int(x['duration_seconds']) for x in rows)
    return {'sessions':n,'pages_vues':pageviews,'leads':leads,'taux_conversion_pct':round(100*leads/n,2) if n else 0,
        'taux_rebond_pct':round(100*bounce/n,2) if n else 0,'duree_moy_sec':round(durations/n,1) if n else 0,
        'pages_par_session':round(pageviews/n,2) if n else 0}

def report(month='2026-10'):
    rows=load_sessions()
    current=[r for r in rows if r['date'].startswith(month)]
    prev=[r for r in rows if r['date'].startswith('2026-09')]
    k=metrics(current);k_prev=metrics(prev)
    by_channel={c:metrics([x for x in current if x['source']==c]) for c in ('organic','paid_search','direct')}
    def fr(n):return str(n).replace('.',',')
    txt=f'''# Rapport mensuel web analytics — {month}

> **Données entièrement simulées** : aucun accès à Matomo, Content Square, un site d'Arkema ou un concurrent réel.

## Indicateurs clés

- Trafic : **{k['sessions']} sessions** (mois précédent : {k_prev['sessions']}).
- Pages vues : **{k['pages_vues']}**, soit {fr(k['pages_par_session'])} pages/session.
- Taux de conversion **lead** : **{fr(k['taux_conversion_pct'])} %** ({k['leads']} formulaires de contact), distinct du CTR publicitaire.
- Taux de rebond : **{fr(k['taux_rebond_pct'])} %** (sessions à une seule page, définition de ce projet).
- Durée moyenne : **{fr(k['duree_moy_sec'])} secondes** par session (mesure synthétique).

## Acquisition par canal

| Canal | Sessions | Leads | Conversion | Rebond |
|---|---:|---:|---:|---:|
'''
    for c,m in by_channel.items():txt+=f"| {c} | {m['sessions']} | {m['leads']} | {fr(m['taux_conversion_pct'])} % | {fr(m['taux_rebond_pct'])} % |\n"
    txt+='''
## Parcours client, UX et SEO : recommandations

1. Vérifier la cohérence du plan de taggage : page_view, CTA_click, form_submit, goal_conversion.
2. Analyser la sortie du parcours sur les pages d'atterrissage, notamment paid_search.
3. Corriger les pages dont les méta descriptions, H1, liens canoniques ou attributs alt sont absents (audit SEO joint).
4. Coordonner la mise en œuvre avec les webmasters et développeurs via tickets et tests de recette.
5. Suivre les positions SEO et backlinks seulement avec des sources de données réelles autorisées ; le benchmark fourni est un scénario de démonstration.

Ce rapport illustre une méthode de pilotage, et non une performance d'entreprise.
'''
    (ROOT/'output').mkdir(exist_ok=True)
    p=ROOT/'output'/f'rapport_mensuel_{month}.md';p.write_text(txt,encoding='utf-8')
    return k

if __name__=='__main__':print(report())
