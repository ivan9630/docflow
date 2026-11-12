import csv,json,argparse
from pathlib import Path
from .llm_enrichment import enrich
from .storage import store
ROOT=Path(__file__).resolve().parents[1]
def run(use_llm=False):
    with (ROOT/"data/produits_demo.csv").open(encoding="utf-8") as f:items=list(csv.DictReader(f))
    output=[enrich(p,use_llm=use_llm) for p in items]
    for item in output:store(item)
    (ROOT/"output").mkdir(exist_ok=True)
    (ROOT/"output/fiches_enrichies.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    return items,output
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--openai",action="store_true");args=parser.parse_args()
    a,b=run(args.openai)
    print(f"{len(a)} fiches enrichies, mode OpenAI : {args.openai}")
