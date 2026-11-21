# TelecomOps — Java / Angular / REST API

**Projet personnel de démonstration** : application de suivi des incidents réseau dans un contexte télécom fictif. Conçu comme portfolio pour une candidature de développeur Java / Angular. **Ce n'est pas une mission réalisée pour un opérateur télécom.**

## Fonctionnalités
- API REST Java 21 / Spring Boot 3 (création, consultation, recherche, changement de statut).
- Tableau de bord Angular 18 (standalone components) : KPI, recherche, filtrage, formulaire de création et suivi.
- Validation des requêtes, codes HTTP adaptés, CORS local, gestion des erreurs.
- Tests JUnit/MockMvc du contrôleur.
- Jeu de données fictives préchargé en mémoire, sans base de données ni credentials.

## Stack
Java 21, Spring Boot 3.3, Maven, Spring Web, Jakarta Validation, JUnit 5, MockMvc, TypeScript, Angular 18, RxJS, HTML/CSS, API REST, JSON.

## Démarrer
Prérequis : **Java 21, Maven 3.9+, Node 20+**.

```bash
cd backend
mvn test
mvn spring-boot:run
```

Dans un second terminal :

```bash
cd frontend
npm install
npm start
```

Ouvrir **http://localhost:4200** ; API sur **http://localhost:8080**.

## Endpoints
| Méthode | Route | Usage |
|---|---|---|
| GET | `/api/incidents` | Liste, avec `?status=OPEN&priority=HIGH&q=fibre` |
| GET | `/api/incidents/{id}` | Détails |
| POST | `/api/incidents` | Déclarer un incident |
| PATCH | `/api/incidents/{id}/status` | Changer le statut |
| GET | `/api/metrics` | Statistiques |

Exemple de création :
```bash
curl -X POST http://localhost:8080/api/incidents -H 'Content-Type: application/json' -d '{"title":"Rupture lien fibre","site":"PAR-12","priority":"CRITICAL","category":"FIBER","description":"Perte de liaison sur un tronçon"}'
```

Exemple de changement de statut :
```bash
curl -X PATCH http://localhost:8080/api/incidents/1/status -H 'Content-Type: application/json' -d '{"status":"IN_PROGRESS"}'
```

## Architecture
```
backend/src/main/java/com/ivan/telecomops/
  TelecomOpsApplication.java
  domain/{Incident,Priority,Status}.java
  api/{IncidentController,IncidentDtos,ApiExceptionHandler}.java
  service/IncidentService.java
frontend/src/app/
  app.component.{ts,html,css}
  incident.service.ts
  incident.model.ts
```

## Pistes de production
Persistance PostgreSQL, Spring Data JPA, migrations Flyway, tests E2E Angular, auth OAuth2/JWT, observabilité Micrometer/OpenTelemetry, CI/CD et Docker. Cette version volontairement autonome ne revendique pas ces composants.

## Correspondance avec l'offre
**Java, Angular, API REST, intégration front/back, TypeScript, contexte fonctionnel télécommunications, tests, validation, gestion d'incidents.**

Les données sont inventées ; aucune donnée client, réseau ou télécom réelle.
