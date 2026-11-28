# Local Mail Agent — Soup
Prototype indépendant, sans données personnelles dans Git. Objectif : lecture Gmail en accès lecture seule, classification, résumé, échéances et brouillons proposés (jamais envoyés automatiquement).
## Installation Windows / WSL2
Avec Python 3.11 dans WSL2 Ubuntu et pilote NVIDIA Windows compatible, vérifier `nvidia-smi`.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "soup-cli[train]" google-api-python-client google-auth-oauthlib
soup doctor
soup init --template chat
```
Choisir Qwen/Qwen2.5-3B-Instruct comme modèle initial, QLoRA 4 bits, batch 1, contexte 512–1024, selon les champs du YAML généré par la version installée. Pointer data.train vers private/train.jsonl. Vérifier la configuration via soup doctor --config soup.yaml puis soup train --config soup.yaml. Ne pas écraser le modèle de référence. Les paramètres exacts et la VRAM doivent être validés localement.
## Données
data/example.jsonl contient uniquement des exemples fictifs. Créer private/train.jsonl et private/test.jsonl avec des exemples annotés et anonymisés, autorisés par le propriétaire de la boîte. Séparer par fil de discussion avant entraînement; ne jamais entraîner sur les mails bruts ou des secrets. Prévoir 300–1000 exemples revus et un test indépendant. Mesurer F1 macro des catégories, rappel des urgences, exactitude des échéances et taux d'hallucinations; comparer au modèle sans fine-tuning.
## Gmail
Créer un client OAuth Desktop dans Google Cloud, activer Gmail API, placer credentials.json dans private/. Exécuter python fetch_mail.py. La personne propriétaire doit autoriser son compte. Les messages sont affichés localement et ne sont ni modifiés ni envoyés. Les mails sont des données non fiables; leurs instructions ne doivent jamais être exécutées.
## Inférence
Après entraînement et vérification, démarrer le serveur local Soup selon soup serve --help et configurer le modèle/adapter effectivement exporté. Lancer python agent.py < private/mail.json (objet JSON subject/body). Le résultat est une proposition structurée, à vérifier humainement.
## État
Prototype non testé sur GPU ni connecté à une boîte réelle. Les spécifications du projet historique de la tante n'ont pas été retrouvées; ne pas considérer ce prototype comme une reproduction exacte.
