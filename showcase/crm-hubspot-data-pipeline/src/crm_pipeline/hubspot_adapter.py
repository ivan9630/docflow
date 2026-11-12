"""Adaptateur HubSpot CRM Contacts API v3, lecture seule.

Aucune écriture HubSpot n'est réalisée. Le mode fixture est utilisé par défaut.
"""
from __future__ import annotations
import os
import json
import time
from pathlib import Path
import requests

URL = 'https://api.hubapi.com/crm/v3/objects/contacts'
FIELDS = ['email','firstname','lastname','company','lifecyclestage','hs_lead_status','lastmodifieddate']


def read_fixture(path: Path):
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    return payload.get('results',[])


def get_contacts(limit: int = 500, token: str | None = None, session=None):
    """Récupère contacts en pagination. Arrêt sur 429/5xx après tentatives bornées."""
    token = token or os.getenv('HUBSPOT_PRIVATE_APP_TOKEN')
    if not token: raise RuntimeError('HUBSPOT_PRIVATE_APP_TOKEN requis pour le mode API')
    if not 1 <= limit <= 10000: raise ValueError('Limite hors plage')
    session = session or requests.Session()
    results=[];after=None
    while len(results) < limit:
        params={'limit': min(100,limit-len(results)), 'properties': ','.join(FIELDS)}
        if after:params['after']=after
        for attempt in range(4):
            response=session.get(URL,headers={'Authorization':f'Bearer {token}'},params=params,timeout=20)
            if response.status_code in (429,500,502,503,504):
                if attempt == 3: response.raise_for_status()
                time.sleep(min(2**attempt,8));continue
            response.raise_for_status();break
        payload=response.json()
        results.extend(payload.get('results',[]))
        new_after=payload.get('paging',{}).get('next',{}).get('after')
        if not new_after or new_after == after: break
        after=new_after
    return results[:limit]
