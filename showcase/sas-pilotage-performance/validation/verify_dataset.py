from pathlib import Path
import pandas as pd
r=Path(__file__).resolve().parents[1]
a=pd.read_csv(r/'data/agences.csv');c=pd.read_csv(r/'data/campagnes.csv');x=pd.read_csv(r/'data/interactions.csv')
assert len(x)==605
assert x.interaction_id.duplicated().sum()==1
u=x.drop_duplicates('interaction_id')
m=u.merge(a,on='agency_id',how='left').merge(c,on='campaign_id',how='left')
ok=m.loc[m.region.notna()&m.canal.notna()&m.impressions.gt(0)&m.clics.ge(0)&m.clics.le(m.impressions)&m.contacts.ge(0)&m.contacts.le(m.clics)&m.rdv.ge(0)&m.rdv.le(m.contacts)&m.cout_eur.ge(0)&m.jour.notna()].copy()
assert len(ok)==600 and len(u)-len(ok)==4
report=ok.groupby('region',as_index=False).agg(observations=('interaction_id','size'),impressions=('impressions','sum'),clics=('clics','sum'),contacts=('contacts','sum'),rdv=('rdv','sum'),cout_eur=('cout_eur','sum'))
report['ctr_pct']=100*report.clics/report.impressions
report['conversion_rdv_pct']=100*report.rdv/report.clics
report['cout_par_rdv']=report.cout_eur/report.rdv
report.to_csv(r/'validation/reference_kpi_region.csv',index=False,float_format='%.5f')
print('OK: 605 sources, 1 doublon, 4 autres rejets, 600 valides')
print(report.to_string(index=False))