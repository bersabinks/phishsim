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
| 7 | US7 | Consulter une page de bonnes pratiques anti-phishing (`/conseils`) | 2 | US1–US6 | ✅ Done |
| 8 | US8 | Exporter un rapport PDF des indicateurs agrégés (sans donnée nominative) | 3 | US5 | ✅ Done |
| 9 | US9 | Comparer deux campagnes côte à côte (`/api/compare`, `/compare`) | 3 | US5 | ✅ Done |

**Justification de l'ordre :** US1→US5 forment le parcours métier minimal qui doit
exister avant tout durcissement. US3 a été découpée implicitement en deux temps
(génération du jeton, puis page de simulation) pour rester démontrable tôt. US6
arrive en fin car elle outille la livraison de ce qui précède. US7–US9 sont des
extensions livrées après le MVP : elles enrichissent la valeur produit sans
compromettre les contraintes éthiques (aucune donnée nominative, aucun jeton dans
les exports et comparaisons).

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
| Tests unitaires et d'intégration (29 tests) | tous | ✅ |
| Pipeline CI (lint, tests, audit, secrets, build) | US6 | ✅ |
| Dockerfile (compte non privilégié, healthcheck) | US6 | ✅ |
| README + exploitation + architecture + note éthique | tous | ✅ |
| Page `/conseils` (template + route + lien header) | US7 | ✅ |
| Mise à jour dépendances vulnérables (14 CVE → 0) | US6 | ✅ |
| Export PDF agrégé `GET /api/campaigns/{id}/export` (fpdf2) | US8 | ✅ |
| Comparaison `GET /api/compare` + page `/compare` | US9 | ✅ |

---

## 4. Dépendances rendues visibles

```
US1 ──▶ US2 ──▶ US3 ──▶ US4 ──▶ US5
                                  │
US1..US5 ─────────────────────────┴──▶ US6 (CI/CD, sécurité chaîne)
                                         │
                              US6 ───────┴──▶ US7 (conseils)
                              US5 ───────────▶ US8 (export PDF)
                              US5 ───────────▶ US9 (comparaison)
```

- US2 dépend de l'existence d'une campagne (US1).
- US4 et US5 dépendent des jetons produits en US3.
- US6 outille la livraison de l'ensemble.
- US7–US9 sont des extensions post-MVP : US7 nécessite l'infrastructure (US6),
  US8 et US9 s'appuient sur l'agrégation (US5) sans introduire de donnée nominative.

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

| Usage | Preuve attendue | Application concrète |
|---|---|---|
| Génération de code | Objectif, référence, tests et corrections humaines | Routes FastAPI, logique métier (`services.py`), templates Jinja2, JS frontend et tests générés par IA (Claude Code) ; chaque livraison vérifiée par `pytest -q` (29 tests) et relecture humaine avant commit. Exemples : endpoint `/api/compare`, génération PDF `fpdf2`, template `compare.html`. |
| Conception | Hypothèses proposées puis arbitrage de l'équipe | Stack FastAPI / SQLite / Docker proposée par l'IA, retenue par l'équipe pour la contrainte de 15 h (zéro configuration, reproductibilité immédiate). Choix de `fpdf2` pour l'export PDF arbitré par l'équipe (licence MIT, API Python native, pas de dépendance système). |
| Tests | Cas générés, limites détectées, résultats exécutés | **29 tests** (`pytest`) générés par IA et exécutés : scénarios nominaux (parcours complet, comparaison valide, export PDF), scénarios d'erreur (jeton inconnu, campagne inexistante, import e-mail réel refusé), assertions de sécurité (absence de jeton `sim_` dans PDF et JSON, en-têtes HTTP, absence de champ mot de passe). |
| Documentation | Texte relu, adapté, vérifié | `README.md`, `ARCHITECTURE.md`, `SCRUM.md`, `NOTE_ETHIQUE_SECURITE.md` rédigés par IA puis relus et adaptés au produit livré réel (noms de fichiers, compteurs de tests, décisions d'arbitrage). |

**Fichiers générés ou co-générés par IA (état final) :**
`app/main.py` · `app/services.py` · `app/db.py` · `app/config.py` ·
`app/templates/dashboard.html` · `app/templates/simulation.html` ·
`app/templates/conseils.html` · `app/templates/compare.html` ·
`app/static/app.js` · `app/static/compare.js` · `app/static/style.css` ·
`tests/test_api.py` · `tests/test_services.py` ·
`scripts/seed_demo.py` · `Dockerfile` · `docker-compose.yml` ·
`.github/workflows/ci.yml` · tous les fichiers `docs/`.

---

## 7. Scénarios de Sprint Review

- **Scénario nominal :** créer une campagne, importer cinq participants via CSV,
  jouer deux parcours (clics + signalement), afficher les résultats agrégés.
- **Scénario d'erreur :** tenter un import contenant une adresse e-mail réelle
  (rejet signalé) ; enregistrer un événement sur un jeton inconnu (HTTP 400).
- **Extension — conseils :** ouvrir `/conseils` depuis le header du tableau de bord,
  vérifier l'affichage des cinq sections de bonnes pratiques.
- **Extension — export PDF :** cliquer « Exporter PDF » dans la section résultats,
  vérifier que le fichier téléchargé contient les indicateurs agrégés et aucun alias.
- **Extension — comparaison :** ouvrir `/compare`, sélectionner deux campagnes
  différentes, vérifier l'affichage côte à côte des indicateurs.

Les scénarios MVP sont couverts par `tests/test_api.py` (29 tests au total).

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
