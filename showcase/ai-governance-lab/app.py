"""AI Governance Lab: scoring pédagogique de cas d'usage IA, sans dépendances."""
from __future__ import annotations
import argparse
import csv
import json
import re
from pathlib import Path

EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE = re.compile(r"(?:\+33|0)[1-9](?:[ .-]?\d{2}){4}")
WEIGHTS = {
    "personal_data": 15,
    "sensitive_data": 20,
    "external_users": 10,
    "impactful_decision": 20,
    "third_party_llm": 10,
    "no_human_oversight": 15,
    "pii_in_sample": 10,
}
RECOMMENDATIONS = {
    "personal_data": "Cartographier les données et documenter la base légale avec le DPO.",
    "sensitive_data": "Évaluer la nécessité des données sensibles et renforcer les contrôles d'accès.",
    "external_users": "Définir les mécanismes d'information et de contestation des utilisateurs.",
    "impactful_decision": "Documenter l'impact métier et réaliser une revue de risques dédiée.",
    "third_party_llm": "Vérifier les transferts, la rétention et les engagements contractuels du fournisseur.",
    "no_human_oversight": "Mettre en place une validation humaine pour les sorties à enjeu.",
    "pii_in_sample": "Retirer ou pseudonymiser les données personnelles dans les exemples et les journaux.",
}

def detect_pii(text: str) -> dict[str, int]:
    if not isinstance(text, str):
        raise ValueError("sample_text doit être une chaîne.")
    return {"emails": len(EMAIL.findall(text)), "phones": len(PHONE.findall(text))}

def analyze_case(item: dict) -> dict:
    if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"].strip():
        raise ValueError("Chaque cas doit contenir un champ name non vide.")
    flags = {k: bool(item.get(k, False)) for k in WEIGHTS if k != "pii_in_sample" and k != "no_human_oversight"}
    flags["no_human_oversight"] = not bool(item.get("human_oversight", False))
    pii = detect_pii(item.get("sample_text", ""))
    flags["pii_in_sample"] = sum(pii.values()) > 0
    score = sum(WEIGHTS[k] for k, active in flags.items() if active)
    priority = "ÉLEVÉE" if score >= 55 else "MODÉRÉE" if score >= 25 else "FAIBLE"
    actions = [RECOMMENDATIONS[k] for k, active in flags.items() if active]
    if not actions:
        actions = ["Maintenir les contrôles documentés et planifier une revue périodique."]
    return {
        "name": item["name"].strip(),
        "owner": str(item.get("owner", "À désigner")),
        "score": score,
        "priority": priority,
        "flags": [k for k, active in flags.items() if active],
        "pii_counts": pii,
        "recommended_actions": actions,
    }

def export_reports(items: list[dict], output: Path) -> list[dict]:
    if not isinstance(items, list):
        raise ValueError("Le fichier d'entrée doit contenir une liste JSON.")
    results = [analyze_case(item) for item in items]
    output.mkdir(parents=True, exist_ok=True)
    (output / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (output / "risk_register.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "owner", "score", "priority", "flags"])
        writer.writeheader()
        for r in results:
            writer.writerow({k: ("|".join(r[k]) if k == "flags" else r[k]) for k in writer.fieldnames})
    lines = ["# Synthèse de gouvernance IA", "", "Priorisation indicative — ne constitue pas un avis juridique.", ""]
    for r in sorted(results, key=lambda x: x["score"], reverse=True):
        lines += [f"## {r['name']} — {r['priority']} ({r['score']}/100)", f"Responsable : {r['owner']}", ""]
        lines += [f"- {a}" for a in r["recommended_actions"]] + [""]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return results

def main() -> None:
    parser = argparse.ArgumentParser(description="Registre pédagogique de risques IA")
    parser.add_argument("--input", type=Path, default=Path("examples/use_cases.json"))
    parser.add_argument("--output", type=Path, default=Path("out"))
    args = parser.parse_args()
    try:
        items = json.loads(args.input.read_text(encoding="utf-8"))
        results = export_reports(items, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(f"{len(results)} cas analysés. Rapport: {args.output / 'report.md'}")

if __name__ == "__main__":
    main()
