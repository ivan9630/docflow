# Cas d'usage et critères d'acceptation — Simulation France Travail Pro

Cas de figure **entièrement fictif** : une direction marketing souhaite mesurer l'efficacité de campagnes de mobilisation des entreprises, suivre les indicateurs clés à l'échelle locale et nationale et réaliser des études d'impact.

## Demandes représentatives
- **Direction générale** : tableau de bord consolidé, suivi des dépenses, performance des campagnes, indicateurs clés.
- **Directions régionales et équipes réseau** : comparatifs territoriaux, analyses sectorielles, lecture des écarts par canal.
- **Direction marketing** : taux de clics, contacts, rendez-vous, coût par résultat; exposés/témoins avant/après.
- **Équipes techniques** : reproductibilité de l'ingestion, suivi qualité, modèle SQL en étoile, documentation des traitements.

## Tests d'acceptation
1. Lire 605 lignes brutes, détecter 1 doublon + 4 incohérences, conserver exactement 600 enregistrements.
2. Calculer les KPI en ratios pondérés des sommes, y compris après filtres territoriaux.
3. Stocker les observations dans une base SQLite avec six dimensions et une table de faits.
4. Produire une synthèse nationale, un rapport par région, un rapport par secteur et par campagne, avec exports CSV.
5. Produire une analyse descriptive des écarts avant/après exposés/témoins avec interprétation prudente.
6. Proposer des traitements complémentaires SAS (PROC IMPORT, SQL, MEANS, TTEST, GLM, REPORT), R (test t, régression) et Python (pandas/SQLite).
7. Documenter les mesures DAX et les quatre pages d'un tableau de bord Power BI.

## Définitions des KPI
- CTR = clics / impressions.
- Taux de contact = contacts / clics.
- Taux de transformation RDV = rendez-vous / contacts.
- Coût par RDV = dépenses / rendez-vous.
- RDV pour 1 000 impressions = 1 000 × rendez-vous / impressions.
- DiD descriptif = (exposés après − exposés avant) − (témoins après − témoins avant), en RDV / 1 000 impressions.

Les données de démonstration n'appartiennent à aucun organisme réel; les analyses statistiques ne prouvent pas un effet causal.
