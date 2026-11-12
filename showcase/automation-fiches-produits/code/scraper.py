"""Analyse HTML locale ; extraction distante seulement après autorisation explicite."""
import json
from pathlib import Path
from bs4 import BeautifulSoup
def parse_html(html):
    soup=BeautifulSoup(html,"html.parser")
    answer={}
    for item in soup.select('script[type="application/ld+json"]'):
        try:
            value=json.loads(item.string or "{}")
            if isinstance(value,dict) and value.get("@type")=="Product":
                answer["nom"]=str(value.get("name",""))[:120]
                brand=value.get("brand",{})
                answer["marque"]=str(brand.get("name","") if isinstance(brand,dict) else brand)[:80]
                answer["description"]=str(value.get("description",""))[:700]
        except (ValueError,AttributeError,TypeError):continue
    return answer
def scrape_local(path):
    return parse_html(Path(path).read_text(encoding="utf-8"))
