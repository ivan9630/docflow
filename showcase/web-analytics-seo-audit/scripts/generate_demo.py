"""Generate deterministic fictitious web sessions, 130 SEO pages, and benchmark samples."""
from __future__ import annotations
import csv
from datetime import date,timedelta
from pathlib import Path
import random
import html

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; PAGES=ROOT/'demo'/'pages'
R=random.Random(20261113)
SOURCES=('organic','paid_search','direct')

def write_csv(path,items,cols):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(items)

def html_page(i):
    """A connected synthetic site, with intentionally flawed SEO metadata for auditing."""
    name=f'Matériaux durables — Dossier {i:03}'
    title='Guide des matériaux durables' if i%17==0 else name
    desc='' if i%11==0 else f'Découvrez le dossier {i} sur les matériaux, les solutions industrielles et le réemploi.'
    heading='' if i%19==0 else f'<h1>{html.escape(name)}</h1>'
    canonical='' if i%23==0 else f'<link rel="canonical" href="https://www.exemple-audit.invalid/pages/page-{i:03}.html">'
    alt='alt="Matériau industriel"' if i%13 else ''
    image=f'<img src="../assets/symbol.svg" {alt}>'
    next_page=i+1 if i<130 else 1
    return f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
    {f'<meta name="description" content="{html.escape(desc)}">' if desc else ''}
    {canonical}</head><body><nav><a href="../index.html">Accueil</a></nav>{heading}
    <p>Contenu de démonstration sur les matériaux, le cycle de vie et les performances.</p>{image}
    <a href="page-{next_page:03}.html">Dossier suivant</a></body></html>'''

def generate():
    DATA.mkdir(parents=True,exist_ok=True);PAGES.mkdir(parents=True,exist_ok=True)
    for i in range(1,131):
        (PAGES/f'page-{i:03}.html').write_text(html_page(i),encoding='utf-8')
    pages=[{'path':'/index.html','type':'home','niveau':0}]
    pages.extend({'path':f'/pages/page-{i:03}.html','type':'article','niveau':1} for i in range(1,131))
    write_csv(DATA/'pages_demo.csv',pages,['path','type','niveau'])
    sessions=[]
    for i in range(720):
        month=9 if i<320 else 10
        day=1+(i*11)% (30 if month==9 else 31)
        source=SOURCES[(i*7+R.randrange(0,3))%3]
        pv=1 if R.random()<({'organic':.39,'paid_search':.45,'direct':.29}[source]) else 2+R.randrange(0,5)
        lead=int(R.random()<({'organic':.046,'paid_search':.072,'direct':.035}[source])*(1.18 if month==10 else 1))
        duration=0 if pv==1 else 15+R.randrange(10,420)
        sessions.append({'session_id':f'SES-{i+1:04}', 'date':f'2026-{month:02}-{day:02}', 'source':source,
        'campaign': 'SEO-contenu' if source=='organic' else ('SEA-prospection' if source=='paid_search' else 'Direct'),
        'device':'mobile' if R.random()<.58 else 'desktop',
        'landing_page':'/index.html' if i%5==0 else f'/pages/page-{1+(i*13)%130:03}.html',
        'pageviews':pv,'duration_seconds':duration,'bounced':int(pv==1),'lead_converted':lead,
        'variant':'B' if i%2 else 'A'})
    write_csv(DATA/'sessions_demo.csv',sessions,list(sessions[0]))
    competitors=[
        {'site':'acteur-a.example','trafic_mensuel_estime':4800,'position_seo_estimee':8,'backlinks_estimes':410,'note':'simulation'},
        {'site':'acteur-b.example','trafic_mensuel_estime':6200,'position_seo_estimee':5,'backlinks_estimes':670,'note':'simulation'},
        {'site':'acteur-c.example','trafic_mensuel_estime':3900,'position_seo_estimee':12,'backlinks_estimes':280,'note':'simulation'},
        {'site':'acteur-d.example','trafic_mensuel_estime':5200,'position_seo_estimee':7,'backlinks_estimes':550,'note':'simulation'}]
    write_csv(DATA/'benchmark_concurrents_demo.csv',competitors,list(competitors[0]))
    return {'sessions':len(sessions),'pages':len(pages),'benchmarks':len(competitors)}

if __name__=='__main__':print(generate())
