from pathlib import Path
import csv, random
r=random.Random(20261112)
root=Path(__file__).resolve().parent
(root/'data').mkdir(exist_ok=True)
agencies=[('A01','Ile-de-France','Urbain'),('A02','Ile-de-France','Periurbain'),('A03','Hauts-de-France','Urbain'),('A04','Hauts-de-France','Rural'),('A05','Occitanie','Urbain'),('A06','Occitanie','Rural'),('A07','Auvergne-Rhone-Alpes','Urbain'),('A08','Auvergne-Rhone-Alpes','Periurbain'),('A09','Bretagne','Urbain'),('A10','Bretagne','Rural')]
campaigns=[('C01','Email',2500),('C02','SMS',1800),('C03','Web',4200),('C04','Email',2700),('C05','Web',4100),('C06','SMS',2000)]
def write(name,columns,rows):
 with (root/'data'/name).open('w',newline='',encoding='utf8') as f:
  w=csv.writer(f);w.writerow(columns);w.writerows(rows)
write('agences.csv',['agency_id','region','territoire'],agencies)
write('campagnes.csv',['campaign_id','canal','budget_eur'],campaigns)
rows=[]
for i in range(1,601):
 agency=r.choice(agencies)[0];campaign=r.choice(campaigns)[0];impressions=r.randint(300,4500);clicks=int(impressions*r.uniform(.025,.15));leads=int(clicks*r.uniform(.12,.5));rdv=int(leads*r.uniform(.25,.78));cost=round(r.uniform(15,105),2)
 rows.append([f'I{i:04}',f'2026-10-{r.randint(1,28):02}',agency,campaign,impressions,clicks,leads,rdv,cost])
rows.append(rows[19].copy())
rows.extend([['I0602','2026-10-12','AXX','C01',1000,70,30,17,22],['I0603','2026-10-12','A01','C02','',80,40,20,17],['I0604','2026-10-12','A02','C03',70,95,20,12,21],['I0605','2026-10-12','A03','C04',1000,100,25,45,19]])
write('interactions.csv',['interaction_id','jour','agency_id','campaign_id','impressions','clics','contacts','rdv','cout_eur'],rows)
print('605 observations générées : 600 valides + 5 anomalies contrôlées')