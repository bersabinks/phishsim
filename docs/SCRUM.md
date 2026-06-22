# Artefacts Scrum

Document de pilotage du mini-projet. Regroupe le Product Backlog réordonné, le
Sprint Backlog, la traçabilité de la Definition of Done et la préparation de la
Sprint Review.

---

## 1. Sprint Goal

> Livrer un incrément utilisable de « Gestionnaire de campagnes de sensibilisation
> au phishing » permettant un parcours métier de bout en bout, avec une chaîne de
> livraison reproductible et un niveau minimal d'exploitabilité.

---

## 2. Product Backlog réordonné

Ordre établi pour livrer d'abord un **parcours vertical démontrable**, puis durcir.
Les points sont indicatifs (pas une mesure de productivité).

| Ordre | ID | User story | Pts | Dépend de | Statut |
|---|---|---|---|---|---|
| 1 | US1 | Créer une campagne (cadrer l'action) | 3 | — | ✅ Done |
| 2 | US2 | Ajouter des participants fictifs (manuel + CSV) | 3 | US1 | ✅ Done |
| 3 | US3 | Accéder à une simulation pédagogique (jeton, page sans collecte) | 5 | US2 | ✅ Done |
| 4 | US4 | Enregistrer les résultats (événements horodatés, règle unique) | 5 | US3 | ✅ Done |
| 5 | US5 | Consulter des indicateurs agrégés (sans classement nominatif) | 5 | US4 | ✅ Done |
| 6 | US6 | Sécuriser la chaîne de livraison (CI : dépendances + secrets) | 5 | US1–US5 | ✅ Done |

**Justification de l'ordre :** US1→US5 forment le parcours métier minimal qui doit
exister avant tout durcissement. US3 a été découpée implicitement en deux temps
(génération du jeton, puis page de simulation) pour rester démontrable tôt. US6
arrive en fin car elle outille la livraison de ce qui précède.

**Découpage d'une story trop grande :** US3 (5 pts) regroupait « générer un jeton »
et « page de simulation ». Elle a été réalisée en deux sous-tâches livrables
séparément pour réduire le risque et permettre une revue intermédiaire.

---

## 3. Sprint Backlog (tâches)

| Tâche | Story | État |
|---|---|---|
| Créer le dépôt, structure et conventions | — | ✅ |
| Modèle de données + schéma SQLite | US1–US5 | ✅ |
| Critères d'acceptation + Definition of Done | — | ✅ |
| Endpoint création de campagne + validation | US1 | ✅ |
| Ajout participant + génération de jeton | US2, US3 | ✅ |
| Import CSV contrôlé (refus des e-mails) | US2 | ✅ |
| Page de simulation sans collecte d'identifiant | US3 | ✅ |
| Enregistrement d'événements + règle d'unicité | US4 | ✅ |
| Agrégation sans classement nominatif | US5 | ✅ |
| En-têtes de sécurité + garde-fou e-mail | US6 | ✅ |
| Tests unitaires et d'intégration | tous | ✅ |
| Pipeline CI (lint, tests, audit, secrets, build) | US6 | ✅ |
| Dockerfile (compte non privilégié, healthcheck) | US6 | ✅ |
| README + exploitation + architecture + note éthique | tous | ✅ |

---

## 4. Dépendances rendues visibles

```
US1 ──▶ US2 ──▶ US3 ──▶ US4 ──▶ US5
                                  │
US1..US5 ─────────────────────────┴──▶ US6 (CI/CD, sécurité chaîne)
```

- US2 dépend de l'existence d'une campagne (US1).
- US4 et US5 dépendent des jetons produits en US3.
- US6 outille la livraison de l'ensemble.

---

## 5. Traçabilité de la Definition of Done

| Dimension | Condition minimale | Preuve dans le projet |
|---|---|---|
| Fonctionnel | Critères satisfaits + démo avec jeu de données connu | `scripts/seed_demo.py`, tests d'intégration |
| Code | Versionné, relu, sans secret, erreurs gérées | dépôt Git, `.gitignore`, gestion d'erreurs métier |
| Qualité | Tests essentiels + lint réussis en CI | `ruff` + `pytest` dans `.github/workflows/ci.yml` |
| DevOps | Build/déploiement reproductibles, config externalisée, healthcheck | Docker, `docker-compose.yml`, `/health`, `app/config.py` |
| Documentation | README complet | `README.md`, `docs/EXPLOITATION.md`, `docs/ARCHITECTURE.md` |
| Sécurité | Entrées validées, droits minimaux, pas de données réelles | validation, conteneur non root, refus des e-mails |
| Produit | Parcours principal sans manipulation cachée | démonstration directe via l'interface |

---

## 6. Traçabilité de l'usage de l'IA

| Usage | Preuve attendue | Application |
|---|---|---|
| Génération de code | Objectif, référence, tests et corrections humaines | Code généré avec assistance IA, puis validé par les tests et relu/ajusté par l'équipe ; à documenter dans les commits. |
| Conception | Hypothèses proposées puis arbitrage de l'équipe | Choix FastAPI/SQLite proposés, arbitrés selon le délai de 15 h. |
| Tests | Cas générés, limites détectées, résultats exécutés | 22 tests exécutés (`pytest`), couvrant nominal + erreurs. |
| Documentation | Texte relu, adapté, vérifié | Docs relues et adaptées au produit réel. |

> À compléter par l'équipe : pour chaque contribution de l'IA, conserver
> l'objectif visé, un extrait ou une référence de commit, et la correction humaine.

---

## 7. Scénarios de Sprint Review

- **Scénario nominal :** créer une campagne, importer cinq participants via CSV,
  jouer deux parcours (clics + signalement), afficher les résultats agrégés.
- **Scénario d'erreur :** tenter un import contenant une adresse e-mail réelle
  (rejet signalé) ; enregistrer un événement sur un jeton inconnu (HTTP 400).

Les deux scénarios sont couverts par `tests/test_api.py`.

---

## 8. Retour critique (à présenter en revue)

- **Un choix produit :** limiter le MVP au parcours agrégé sans authentification,
  pour garantir un incrément réellement *Done* en 15 h plutôt qu'un périmètre large
  inachevé.
- **Un choix technique :** SQLite plutôt qu'une base serveur, pour la
  reproductibilité et la simplicité de sauvegarde, au prix de la scalabilité.
- **Un usage de l'IA :** accélération de la génération de code et de la
  documentation, systématiquement vérifiée par les tests et la relecture, afin
  d'éviter le code non maîtrisé.
