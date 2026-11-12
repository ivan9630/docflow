"""Offline local-site crawler: internal links, metadata, H1, canonical, images alt."""
import csv
from html.parser import HTMLParser
from collections import deque,Counter
from pathlib import Path
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'demo'

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__();self.title='';self.in_title=False;self.h1=0;self.links=[];self.descriptions=[];self.canonicals=[];self.images=0;self.images_missing_alt=0;self.lang=''
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='html':self.lang=attrs.get('lang','')
        if tag=='title':self.in_title=True
        if tag=='h1':self.h1+=1
        if tag=='a' and attrs.get('href'):self.links.append(attrs['href'])
        if tag=='img':
            self.images+=1
            if not attrs.get('alt'):self.images_missing_alt+=1
        if tag=='meta' and attrs.get('name','').lower()=='description':self.descriptions.append(attrs.get('content',''))
        if tag=='link' and attrs.get('rel')=='canonical':self.canonicals.append(attrs.get('href',''))
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
    def handle_data(self,data):
        if self.in_title:self.title+=data

def local_url(from_path,href):
    parts=urlsplit(href)
    if parts.scheme or parts.netloc or href.startswith('#'):return None
    dest=(from_path.parent/unquote(parts.path)).resolve() if parts.path else from_path
    try:dest.relative_to(SITE.resolve())
    except ValueError:return None
    if dest.suffix.lower() not in {'.html','.htm'}:return None
    return dest

def audit(start=None):
    start=Path(start or SITE/'index.html').resolve()
    q=deque([start]);seen=set();result=[]
    while q:
        path=q.popleft()
        if path in seen or not path.exists() or not path.is_file():continue
        seen.add(path)
        content=path.read_text(encoding='utf-8')
        parsed=PageParser();parsed.feed(content)
        rel=path.relative_to(SITE.resolve()).as_posix()
        warnings=[]
        if not parsed.title.strip():warnings.append('title_absent')
        if not parsed.descriptions or not parsed.descriptions[0].strip():warnings.append('meta_description_absente')
        if parsed.h1!=1:warnings.append('h1_invalide')
        if not parsed.canonicals:warnings.append('canonical_absent')
        if parsed.images_missing_alt:warnings.append('image_alt_absent')
        if parsed.lang!='fr':warnings.append('lang_fr_absent')
        if len(parsed.title)>65:warnings.append('title_long')
        result.append({'page':rel,'title':parsed.title,'h1_count':parsed.h1,'images':parsed.images,'images_sans_alt':parsed.images_missing_alt,'anomalies':';'.join(warnings)})
        for href in parsed.links:
            target=local_url(path,href)
            if target is not None and target not in seen:q.append(target)
    return result

def build():
    results=audit();out=ROOT/'output';out.mkdir(exist_ok=True)
    with (out/'seo_findings.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=results[0]);w.writeheader();w.writerows(results)
    errors=Counter(x for r in results for x in r['anomalies'].split(';') if x)
    s='# Audit SEO on-page — démonstration\n\n'
    s+='> Site et pages générés localement : aucun crawl d’un site tiers.\n\n'
    s+=f'- Pages HTML explorées via liens internes : **{len(results)}**.\n'
    s+=f'- Pages présentant au moins un contrôle à corriger : **{sum(bool(r["anomalies"]) for r in results)}**.\n\n'
    s+='## Anomalies et priorisation\n\n'
    for name,n in sorted(errors.items(),key=lambda x:-x[1]):s+=f'- {name} : {n} pages\n'
    s+='\n### Actions\nCorriger les métadonnées et balises manquantes ; limiter les titres dupliqués ; enrichir le maillage interne ; planifier une recette technique et des contrôles UX. Les backlinks/off-page ne sont pas mesurés par ce crawler local.\n'
    (out/'audit_seo.md').write_text(s,encoding='utf-8')
    return len(results),errors

if __name__=='__main__':print(build())
