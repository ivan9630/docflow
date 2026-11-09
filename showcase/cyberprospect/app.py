"""CyberProspect : scoring SDR sur des données CRM fictives, sans réseau."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path

SIGNAL_POINTS = {"nouveau_rssi": 25, "recrutement_cyber": 20, "projet_cloud": 15, "veille_nis2": 10}
SECTOR_POINTS = {"finance": 15, "sante": 15, "industrie": 10, "services_it": 10}

def clean(value: str) -> str:
    return (value or "").strip()

def score_contact(contact: dict) -> dict:
    name = clean(contact.get("company", ""))
    if not name:
        raise ValueError("Le champ company est obligatoire.")
    role = clean(contact.get("role", "")).lower()
    sector = clean(contact.get("sector", "")).lower()
    signal = clean(contact.get("signal", "")).lower()
    try:
        size = max(0, int(clean(contact.get("employees", "0")) or "0"))
    except ValueError as error:
        raise ValueError(f"Effectif invalide pour {name}") from error
    points = SECTOR_POINTS.get(sector, 0) + SIGNAL_POINTS.get(signal, 0)
    points += 15 if role in {"rssi", "dsi", "responsable securite", "directeur it"} else 0
    points += 15 if size >= 250 else 8 if size >= 50 else 0
    points += 10 if clean(contact.get("email")) else 0
    reasons = [f"Signal : {signal}" if signal in SIGNAL_POINTS else "Aucun signal prioritaire",
               f"Fonction : {role or 'non renseignée'}", f"Effectif : {size}"]
    return {**contact, "score": min(points, 100),
            "priority": "A" if points >= 65 else "B" if points >= 35 else "C",
            "reason": " | ".join(reasons)}

def deduplicate(contacts: list[dict]) -> list[dict]:
    seen, output = set(), []
    for c in contacts:
        key = (clean(c.get("company")).casefold(), clean(c.get("email")).casefold() or clean(c.get("role")).casefold())
        if key in seen:
            continue
        seen.add(key)
        output.append(c)
    return output

def draft_message(c: dict) -> str:
    company, signal = clean(c.get("company")), clean(c.get("signal")).lower()
    intros = {
        "nouveau_rssi": "Votre équipe sécurité semble récemment évoluer",
        "recrutement_cyber": "Votre recrutement de profils cybersécurité a retenu mon attention",
        "projet_cloud": "Vos projets Cloud laissent penser que vos enjeux de sécurité évoluent",
        "veille_nis2": "Les questions de conformité NIS2 sont un sujet actuel",
    }
    hook = intros.get(signal, "Je m'intéresse à vos priorités en cybersécurité")
    return (f"Bonjour, {hook.lower()} chez {company}. "
            "Seriez-vous disponible pour un bref échange sur vos priorités et vos besoins en expertise IT/cybersécurité ? "
            "Bien cordialement.")

def run(contacts: list[dict], output: Path) -> list[dict]:
    scored = sorted((score_contact(c) for c in deduplicate(contacts)),
                    key=lambda c: (-c["score"], clean(c.get("company"))))
    output.mkdir(parents=True, exist_ok=True)
    fields = ["company", "name", "role", "sector", "employees", "signal", "email", "status", "next_action", "score", "priority", "reason"]
    with (output / "qualified.csv").open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(scored)
    with (output / "messages_draft.csv").open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=["company", "priority", "message"])
        writer.writeheader()
        writer.writerows({"company": c["company"], "priority": c["priority"],
                           "message": draft_message(c)} for c in scored)
    lines = ["# Synthèse de prospection SDR (données fictives)", "",
             f"Contacts uniques : {len(scored)}", "", "| Priorité | Nombre |", "|---|---:|"]
    lines += [f"| {p} | {sum(c['priority'] == p for c in scored)} |" for p in ("A","B","C")]
    lines += ["", "Aucun message n'a été envoyé. Revue humaine et conformité requises."]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return scored

def main() -> None:
    parser = argparse.ArgumentParser(description="Qualification SDR à partir d'un CSV fictif")
    parser.add_argument("--contacts", type=Path, default=Path("examples/contacts.csv"))
    parser.add_argument("--output", type=Path, default=Path("out"))
    args = parser.parse_args()
    try:
        with args.contacts.open(encoding="utf-8", newline="") as fp:
            data = list(csv.DictReader(fp))
        scored = run(data, args.output)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"{len(scored)} prospects qualifiés — {args.output / 'qualified.csv'}")

if __name__ == "__main__":
    main()
