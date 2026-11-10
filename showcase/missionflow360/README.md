# MissionFlow 360 — pilotage de projets Java / Data / IA

**Projet personnel d'Ivan TCHOMTE.** Plateforme fictive de gestion de demandes techniques, conçue comme un petit produit SaaS avec réflexion métier, backlog, workflow, API Java 21 et tableau de bord interactif.

## Démo pour un recruteur
Ouvrez `web/index.html` après avoir téléchargé les fichiers : l'interface fonctionne sans installation en mode autonome, avec données fictives. Pour connecter le backend Java :

```bash
bash test.sh
bash run.sh
# http://localhost:8080
```

**Prérequis : JDK 21.** Aucune dépendance externe pour le serveur Java. Testé avec OpenJDK 21 en local. L'application expose `/api/health`, `/api/items`, `/api/metrics`, `/api/assist/IA`, `/api/export.csv`, une création et les transitions de statut.

Fonctions : gestion de tickets, règles de transition, priorités, indicateurs, suggestions de critères d'acceptation (règles explicables, **pas d'appel LLM**), saisie de demandes, export CSV. Voir `docs/PRODUCT.md` pour les user stories.

## Stack
Java 21 / HttpServer / threads virtuels / API REST, JavaScript, HTML, CSS, Docker, tests de règles métier. Le sous-dossier `spring-api/` contient une variante Spring Boot 3.4 / Spring Data JPA / Hibernate, H2, PostgreSQL et Swagger/OpenAPI. Elle est fournie avec ses tests JUnit, Docker Compose et CI GitHub, mais n'a pas été compilée dans l'environnement de création (Maven indisponible). Ne pas la présenter comme déployée ou industrialisée.

Pour tester Spring Boot sur votre machine : `cd spring-api && mvn test && mvn spring-boot:run` (API `http://localhost:8082/api/v2/tickets`, documentation `http://localhost:8082/swagger-ui.html`). Pour lancer les deux services et PostgreSQL : `docker compose up --build` depuis le dossier `missionflow360`.

## Limites
Données fictives en mémoire côté Java (remises à zéro au redémarrage). Pas de gestion des comptes, pas de sécurité d'accès multi-tenant, pas de LLM réel. Démonstrateur **non destiné à la production**. Les expériences et entreprises mentionnées dans les candidatures sont distinctes de ce projet personnel.

Licence MIT.
