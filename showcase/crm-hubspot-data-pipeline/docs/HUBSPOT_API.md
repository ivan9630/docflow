# Connexion HubSpot CRM (mode facultatif)

Le projet fonctionne **sans compte HubSpot** grâce au fichier `data/hubspot_fixture.json` et au pipeline local. `src/crm_pipeline/hubspot_adapter.py` expose également un adaptateur **lecture seule** sur l'API officielle `/crm/v3/objects/contacts` (propriétés Contacts et pagination).

## Exécution optionnelle

```bash
export HUBSPOT_PRIVATE_APP_TOKEN='...' # ne jamais inscrire le jeton dans un fichier
PYTHONPATH=src python -m crm_pipeline hubspot-api
```

- Utiliser une application privée et uniquement les accès CRM autorisés ; le programme ne demande aucun accès d'écriture.
- Limite configurable, pagination via `paging.next.after`, 4 tentatives maximales pour HTTP 429 et erreurs 5xx, délai et timeout.
- Ne pas publier de vrais noms, e-mails, tokens ou propriétés privées. Les données du dépôt sont toutes fictives.
- Les contacts obtenus par l'API ne sont **pas injectés automatiquement** dans le pipeline de démonstration ; un mapping ETL, la gestion de la confidentialité et une validation métier restent nécessaires.
- Aucune requête HubSpot réelle n'a été effectuée lors de la création du projet.

## Correspondance des champs

| HubSpot API | CRM de démonstration |
|---|---|
| `id` | `lead_id` |
| `properties.email` | `email` |
| `properties.firstname`, `lastname` | `nom` |
| `properties.company` | `entreprise` |
| `properties.hs_lead_status` | `statut` (table de correspondance nécessaire) |
| `properties.lastmodifieddate` | `derniere_interaction` (conversion date nécessaire) |

Les données additionnelles `source`, `secteur`, `litiges`, `facturation` et `score_qualite` proviennent ici de la simulation. Dans un cas réel, ces champs nécessiteraient des propriétés CRM configurées, un rapprochement avec les systèmes de livraison et la facturation, plus un contrôle des autorisations.
