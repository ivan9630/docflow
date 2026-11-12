"""Benchmarks from synthetic estimates, not measurements of real competitors."""
from pathlib import Path
import csv
ROOT=Path(__file__).resolve().parents[1]
def build():
    with (ROOT/'data/benchmark_concurrents_demo.csv').open(encoding='utf-8') as f: rows=list(csv.DictReader(f))
    rows.sort(key=lambda r:int(r['trafic_mensuel_estime']),reverse=True)
    s='# Benchmark SEO / SEA — simulation\n\n**Tous les domaines et chiffres ci-dessous sont fictifs, pas des observations de concurrents réels.**\n\n'
    s+='| Site simulé | Trafic mensuel estimé | Position SEO estimée | Backlinks estimés |\n|---|---:|---:|---:|\n'
    for x in rows:s+=f"| {x['site']} | {x['trafic_mensuel_estime']} | {x['position_seo_estimee']} | {x['backlinks_estimes']} |\n"
    s+='\n## Méthode pour une version réelle\nUtiliser des données d’outils autorisés (Search Console, Matomo, plateformes SEO), préciser la période, le périmètre, les biais des estimations et les sources. Comparer la visibilité SEO, les backlinks et le SEA sans inventer de rang réel.\n'
    ROOT.joinpath('output/benchmark.md').write_text(s,encoding='utf-8');return len(rows)
if __name__=='__main__':print(build())
