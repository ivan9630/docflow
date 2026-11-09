# Odyssée Energy Lab — simulation énergétique interactive

**Démonstrateur portfolio personnel original**, inspiré d'une expérience en stage R&D énergétique avec des chercheurs. Aucune source, donnée ou interface confidentielle d'EDF n'est utilisée ou reproduite.

## Utilisation immédiate
- Ouvrez `index.html` dans Chrome/Firefox/Edge : tout fonctionne hors ligne, sans installation ni API.
- Choisissez un des trois sites et changez les capacités de production, demande et batterie.
- Testez les scénarios « pic de demande », « temps couvert », « hors réseau » et « stockage H₂ ».
- Examinez les trois courbes horaires et les KPI, puis exportez les données en CSV.
- Découvrez une approche produit : découverte des besoins, conception IHM, développement, critères d'acceptation, tests et restitution.

Le fichier `index.html` est volontairement autonome : son moteur intégré et son interface fonctionnent ensemble, même sans serveur. `engine.js` fournit un moteur séparé à réutiliser en JavaScript/Node.js et `tests/engine.test.js` vérifie les invariants essentiels.

## Tests
```bash
node --test tests/engine.test.js
```
**7 tests unitaires** : bornage du stockage, non-négativité, bilans énergétiques, réseau/isolation, hydrogène, reproductibilité.

## Pilotage produit
Ce projet a été cadré comme un MVP : besoins et scénarios avec chercheurs, règles de gestion, parcours IHM, séparation calcul/présentation, backlog de démonstration, critères d'acceptation, recette et documentation. Il illustre la capacité à faire le lien entre équipes métier et techniques. Il ne constitue pas la preuve d'un poste officiel de chef de projet/PO chez EDF.

## Limites
Simulation horaire déterministe, météo et consommation synthétiques, pertes de charge/décharge simplifiées ; H₂ représenté par une réserve énergétique abstraite (pas un électrolyseur industriel). Pas d'optimisation économique, de connexion réseau industriel ou de jumeau numérique EDF. Ne pas utiliser pour dimensionner une installation réelle.

**Auteur :** Ivan TCHOMTE. Licence MIT.
