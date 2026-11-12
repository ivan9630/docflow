"""Mode local reproductible ; appel Claude facultatif avec clé privée."""
import os, re, json, csv, argparse
from pathlib import Path
from .rag_knowledge import Knowledge
from .prompts import SYSTEM_PROMPT,FEW_SHOTS
ROOT=Path(__file__).resolve().parents[1]
DANGERS={"surchauffe","cable_abime","batterie_gonflee"}
VALID={"reconditionner","recycler","dechetterie","controle_expert"}
def decision(p):
    x=p.get("defauts",""); state=p.get("etat","");value=float(p.get("valeur_estimee",0))
    if x in DANGERS:return "recycler"
    if state=="irreparable":return "recycler" if value>=75 else "dechetterie"
    if x in {"fuite","carte_electronique"} and value<95:return "recycler"
    if state not in {"bon","moyen"}:return "controle_expert"
    return "reconditionner"
def ask_claude(p,sources,safe):
    token=os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    if not token:raise RuntimeError("La clé ANTHROPIC_API_KEY est nécessaire")
    from anthropic import Anthropic
    client=Anthropic(api_key=token)
    result=client.messages.create(model=os.getenv("CLAUDE_MODEL","claude-sonnet-4-5"),max_tokens=400,
      system=SYSTEM_PROMPT,messages=[{"role":"user","content":json.dumps({"produit":p,"documents":sources,"exemples":FEW_SHOTS},ensure_ascii=False)}])
    output="".join(getattr(x,"text","") for x in result.content)
    m=re.search(r"\{.*\}",output,re.S)
    if not m:raise ValueError("Claude n'a pas renvoyé de JSON")
    suggestion=json.loads(m.group())
    if suggestion.get("decision") not in VALID:raise ValueError("Décision invalide")
    return {"proposition_claude":suggestion["decision"],"commentaire_claude":str(suggestion.get("motif",""))[:150]}
def run(use_claude=False):
    with (ROOT/"data/fiches_produits_demo.csv").open(encoding="utf-8") as f:rows=list(csv.DictReader(f))
    k=Knowledge();out=[]
    for p in rows:
        safe=decision(p)
        sources=k.search(p["categorie"]+" "+p["defauts"])
        item={"produit_id":p["produit_id"],"decision":safe,"sources":"|".join(d["id"] for d in sources),"validation_humaine":"oui"}
        if use_claude:item.update(ask_claude(p,sources,safe))
        out.append(item)
    path=ROOT/"output/diagnostics.csv"
    path.parent.mkdir(exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=out[0].keys());writer.writeheader();writer.writerows(out)
    return out
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--claude",action="store_true");args=parser.parse_args()
    print(f"{len(run(args.claude))} fiches analysées ; mode Claude : {args.claude}")
