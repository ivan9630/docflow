"""Jeu de données CRM entièrement fictif, reproductible, sans informations personnelles réelles."""
from __future__ import annotations
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / 'data/leads_demo.csv'
SOURCES = ('Google Ads','Meta Ads','SEO','Partenaire','Email','LinkedIn')
INDUSTRIES = ('Logiciels','Industrie','BTP','Services','Commerce')
STATUSES = ('nouveau','qualifie','contacte','proposition','gagne','perdu')
REGIONS = ('Île-de-France','Occitanie','Bretagne','Hauts-de-France','Auvergne-Rhône-Alpes')
FIELDS = ['lead_id','nom','email','entreprise','source','secteur','region','statut','derniere_interaction',
          'nb_interactions','pages_visitees','taille_entreprise','budget_indicatif','contacts_livres',
          'contacts_convertis','litiges','cout_acquisition','ca_facture','montant_facture','date_creation']


def build(path: Path = DATA_PATH) -> int:
    rng = random.Random(20261112)
    leads = []
    start = datetime(2026, 7, 1)
    for i in range(240):
        source = SOURCES[i % len(SOURCES)]
        sector = INDUSTRIES[(i * 7 + 2) % len(INDUSTRIES)]
        reg = REGIONS[(i * 11 + 1) % len(REGIONS)]
        interaction = rng.randint(0, 25)
        pages = rng.randint(1, 22)
        company_size = rng.choice([3, 15, 40, 120, 500])
        age = rng.randint(0, 95)
        dt = (start + timedelta(days=105 - age)).strftime('%Y-%m-%d')
        status = STATUSES[(i * 5 + rng.randint(0, 5)) % len(STATUSES)]
        deliveries = rng.randint(1, 25)
        prob = min(.90, .10 + .027 * min(interaction, 20) + .008 * min(pages, 20) + (.10 if source in ('SEO','Partenaire') else 0))
        won = rng.random() < prob
        successes = min(deliveries, max(1,round(deliveries * rng.uniform(.15,.75)))) if won else 0
        litiges = int(rng.random() < .07)
        acquisition_cost = round(25 + deliveries * rng.uniform(5, 15), 2)
        billed = round(successes * rng.uniform(100, 330), 2)
        nominal_invoice = max(0, round(billed + (rng.choice([-80, 90]) if i % 23 == 0 else 0), 2))
        leads.append(dict(lead_id=f'LD-{i+1:04}',nom=f'Contact Démo {i+1:03}',
           email=f'contact{i+1:03}@example.com',entreprise=f'Société Démo {1+i//3:03}',source=source,
           secteur=sector,region=reg,statut=status,derniere_interaction=dt,nb_interactions=interaction,
           pages_visitees=pages,taille_entreprise=company_size,budget_indicatif=rng.randint(150,12000),
           contacts_livres=deliveries,contacts_convertis=successes,litiges=litiges,
           cout_acquisition=acquisition_cost,ca_facture=billed,montant_facture=nominal_invoice,
           date_creation='2026-07-01'))
    # Doublons de contacts : meilleure version selon la date de mise à jour, déterministe.
    for j in range(12):
        copy = leads[(j * 13 + 7) % 240].copy()
        copy['lead_id'] = f'DUP-{j+1:03}'
        copy['derniere_interaction'] = '2026-11-01'
        copy['nb_interactions'] += 1
        leads.append(copy)
    # Anomalies indépendantes des doublons, avec causes différentes.
    for k in range(8):
        bad = leads[40+k].copy()
        bad['lead_id'] = f'BAD-{k+1:03}'
        bad['email'] = f'erreur{k+1}@example.com'
        if k in (0,1): bad['email'] = 'adresse-invalide'
        elif k in (2,3): bad['cout_acquisition'] = -25
        elif k in (4,5): bad['contacts_convertis'] = bad['contacts_livres']+5
        else: bad['derniere_interaction'] = 'date-erronee'
        leads.append(bad)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w = csv.DictWriter(f,fieldnames=FIELDS)
        w.writeheader();w.writerows(leads)
    return len(leads)

if __name__ == '__main__': print(f'{build()} leads CRM simulés enregistrés')
