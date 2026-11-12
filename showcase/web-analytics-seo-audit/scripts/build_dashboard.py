"""Generate a standalone HTML analytics report plus a compact SVG preview."""
from pathlib import Path
from scripts.monthly_report import ROOT,load_sessions,metrics

def build():
    rows=[x for x in load_sessions() if x['date'].startswith('2026-10')]
    global_kpi=metrics(rows)
    channels={k:metrics([x for x in rows if x['source']==k]) for k in ('organic','paid_search','direct')}
    h='''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Web Analytics — Rapport octobre 2026 (simulation)</title><style>
    body{margin:0;background:#f5f7fa;color:#1a324a;font:16px Arial,sans-serif}.wrap{max-width:1050px;margin:auto;padding:32px}header{background:#163a60;color:white;border-radius:14px;padding:25px}header h1{margin:0;font-size:28px}header p{margin:9px 0 0;color:#d4e4ef}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin:19px 0}.card,section{background:white;border:1px solid #dce4eb;border-radius:12px;padding:19px}.card small{color:#596d80}.card strong{display:block;font-size:26px;margin-top:8px}section{margin:14px 0}h2{margin:3px 0 18px;font-size:19px}.barline{display:grid;grid-template-columns:150px 1fr 110px;gap:13px;align-items:center;margin:14px 0}.bg{height:24px;background:#e6eef7;border-radius:5px;overflow:hidden}.fg{height:100%;background:#327ab6}.note{font-size:13px;color:#60758a;line-height:1.6}@media(max-width:650px){.cards{grid-template-columns:repeat(2,1fr)}.wrap{padding:12px}.barline{grid-template-columns:110px 1fr 65px}}</style></head><body><div class="wrap"><header><h1>Web Analytics · Rapport mensuel</h1><p>Octobre 2026 · SEO, SEA, conversion et parcours utilisateur</p></header><div class="cards">'''
    for label,val in [
      ('Sessions',global_kpi['sessions']),('Pages vues',global_kpi['pages_vues']),('Leads',global_kpi['leads']),('Conversion',f"{global_kpi['taux_conversion_pct']} %"),
      ('Rebond',f"{global_kpi['taux_rebond_pct']} %"),('Durée moy.',f"{global_kpi['duree_moy_sec']} s"),('Pages / session',global_kpi['pages_par_session']),('Canaux',3)]:
        h+=f'<div class="card"><small>{label}</small><strong>{val}</strong></div>'
    h+='</div><section><h2>Sessions par canal</h2>'
    for name,k in channels.items():
        w=int(100*k['sessions']/max(v['sessions'] for v in channels.values()))
        h+=f'<div class="barline"><span>{name}</span><div class="bg"><div class="fg" style="width:{w}%"></div></div><b>{k["sessions"]}</b></div>'
    h+='</section><section><h2>Points de décision</h2><p>Suivre le taux de rebond des pages d’atterrissage, tester les CTA, auditer les métadonnées et partager les indicateurs avec les équipes digitales.</p><p class="note">Données entièrement fictives. Maquette de reporting, sans connexion réelle à Piwik/Matomo, Content Square ni à Arkema.</p></section></div></body></html>'
    (ROOT/'output/dashboard.html').write_text(h,encoding='utf-8')
    cols=['#327ab6','#79a2c5','#b5cadd'];bars=''
    for i,(name,k) in enumerate(channels.items()):
        w=round(410*k['sessions']/max(v['sessions'] for v in channels.values()));y=281+i*52
        bars+=f'<text x="50" y="{y+20}" font-size="18" fill="#28415a">{name}</text><rect x="225" y="{y}" rx="4" width="{w}" height="26" fill="{cols[i]}"/><text x="{240+w}" y="{y+20}" font-size="17" fill="#28415a">{k["sessions"]}</text>'
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="500"><rect width="1000" height="500" fill="#f5f7fa"/><rect x="22" y="20" width="956" height="455" rx="14" fill="white" stroke="#dfe8f0"/><text x="50" y="66" font-family="Arial" font-size="29" fill="#163a60" font-weight="bold">Web Analytics · Octobre 2026</text><text x="50" y="97" font-family="Arial" font-size="16" fill="#67809a">Aperçu de rapport généré à partir des sessions de démonstration</text><text x="50" y="154" font-family="Arial" font-size="20" fill="#28415a">Sessions : {global_kpi['sessions']}</text><text x="287" y="154" font-family="Arial" font-size="20" fill="#28415a">Conversion : {global_kpi['taux_conversion_pct']} %</text><text x="600" y="154" font-family="Arial" font-size="20" fill="#28415a">Rebond : {global_kpi['taux_rebond_pct']} %</text><text x="50" y="224" font-family="Arial" font-size="21" fill="#28415a" font-weight="bold">Trafic par canal</text><g font-family="Arial">{bars}</g><text x="50" y="454" font-size="14" font-family="Arial" fill="#76899e">Synthèse simulée · Matomo (Piwik) en configuration d'exemple</text></svg>'''
    (ROOT/'assets/apercu_rapport.svg').write_text(svg,encoding='utf-8')
    return global_kpi
if __name__=='__main__':print(build())
