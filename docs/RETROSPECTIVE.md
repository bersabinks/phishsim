# Rétrospective de Sprint

Sprint unique de **15 heures** — équipe de 3 personnes :
- **Dev 1** (backend) : FastAPI, logique métier, tests
- **Dev 2** (frontend/fullstack) : templates HTML, JS, CSS, extensions post-MVP
- **Technicien réseau / DevOps** : Docker, CI GitHub Actions, pip-audit, gitleaks

> Format : Continuer / Arrêter / Difficile / Facile + une amélioration retenue.

---

## 1. Continuer

**Le découpage MVP d'abord, extensions ensuite.**
Livrer US1→US5 avant de toucher aux extensions (conseils, PDF, comparaison) a
garanti un incrément réellement *Done* à mi-sprint. La Sprint Review aurait pu
se tenir avec seulement les six premières stories — les trois extensions étaient
un bonus sans risque sur le Sprint Goal.

**Écrire les tests en même temps que le code.**
Les 29 tests ont détecté des bugs immédiatement, notamment :
- la validation CSV qui acceptait des lignes vides avant correction,
- la règle d'unicité des événements (`UNIQUE` sur `campaign_id, token, event_type`)
  qui n'était pas testée explicitement avant d'être cassée par un refactor,
- l'absence de token `sim_` dans les exports PDF et JSON de comparaison,
  découverte par les assertions de sécurité dans les tests.

**Utiliser Docker dès le début.**
Le Dockerfile (utilisateur non root, healthcheck) a été écrit au même moment que
l'application. Résultat : aucune surprise lors de la dockerisation en fin de sprint,
le build CI passait du premier coup. Le technicien DevOps a pu travailler sur la
CI en parallèle des développements sans attendre un "packaging de dernière minute".

---

## 2. Arrêter

**Discuter de features hors périmètre pendant le sprint.**
L'équipe a passé environ 45 minutes à débattre de l'ajout d'une authentification
(login / session) et d'un vrai envoi de courriel de test. Le PO avait déjà tranché
sur ces deux points dès le Sprint Planning : hors périmètre, pour des raisons
éthiques et de délai. Ce temps aurait pu financer l'extension de comparaison ou
un meilleur coverage de tests.

---

## 3. Ce qui a été difficile

**L'arbitrage de périmètre sous la contrainte de 15 h.**
Décider quoi garder et quoi couper est la décision la plus inconfortable du sprint.
L'expiration automatique des jetons par tâche de fond (APScheduler ou similaire)
a été abandonnée : l'infrastructure était configurable (`PHISHSIM_TOKEN_TTL_HOURS`)
mais le déclenchement automatique aurait demandé ~3 h supplémentaires pour être
testé correctement. La décision a été prise explicitement plutôt que de livrer
une feature à moitié terminée.

**La mise en place du pipeline CI complet.**
`pip-audit` a remonté **14 CVE** à la première exécution (jinja2 3.1.5, python-multipart
0.0.20, starlette 0.41.3). Il a fallu identifier les versions corrigées, mettre à
jour `requirements.txt` (fastapi 0.115.6 → 0.138.0 pour tirer starlette 1.3.1,
jinja2 → 3.1.6, python-multipart → 0.0.31), réinstaller et valider que les 29
tests passaient toujours. Comptez ~1 h non anticipée dans la planification initiale.

**Coordonner trois rôles sur un sprint aussi court.**
Le technicien DevOps devait attendre que l'API soit suffisamment stable pour écrire
un `Dockerfile` qui démarre correctement et un healthcheck fiable. En pratique, la
CI a été branchée après US5 (résultats agrégés), ce qui a créé un goulet d'attente
de 2 à 3 heures en milieu de sprint. Une solution pour la prochaine itération :
écrire le `Dockerfile` dès US1 avec un healthcheck minimaliste, quitte à l'enrichir
plus tard.

---

## 4. Ce qui a été facile

**Le choix de la stack FastAPI + SQLite.**
Zéro configuration, zéro migration à gérer, documentation OpenAPI générée
automatiquement. Le premier parcours vertical (créer une campagne, ajouter un
participant, accéder à la simulation) fonctionnait en moins de 2 heures après le
démarrage du sprint.

**L'ajout des extensions post-MVP.**
Grâce à la séparation claire entre routes (`app/main.py`), logique métier
(`app/services.py`) et templates, chaque extension s'est greffée naturellement :
- `/conseils` : une route + un template, ~30 min.
- export PDF : `generate_pdf_report()` isolée dans `services.py`, aucun effet de
  bord sur le reste, ~1 h incluant la mise en conformité ruff.
- `/compare` : un endpoint + un template + un fichier JS, ~1 h.

La modularité n'a pas été planifiée explicitement — elle est venue du respect des
conventions FastAPI et de la séparation des responsabilités appliquée dès US1.

---

## 5. Amélioration retenue (une seule, mesurable)

| Élément | Détail |
|---|---|
| **Action** | Ajouter la mesure de couverture de code dans la CI (`pytest --cov=app`) |
| **Indicateur** | Pourcentage de couverture affiché à chaque exécution dans les logs CI |
| **Cible** | ≥ 80 % de couverture sur `app/services.py` |
| **Responsable** | Technicien réseau / DevOps |
| **Échéance** | Premier commit du prochain sprint |

**Pourquoi cette action ?** Les 29 tests couvrent tous les chemins nominaux et
les principaux chemins d'erreur, mais sans mesure objective il est impossible de
savoir quelles branches de `services.py` (ex. gestion des tokens expirés, lignes
CSV invalides) ne sont pas exercées. Un seuil de 80 % est atteignable sans effort
disproportionné et fournit un filet de sécurité pour les refactors futurs.

---

## 6. Vérification au prochain sprint

- [ ] L'étape `pytest --cov=app --cov-report=term-missing` est présente dans
      `.github/workflows/ci.yml`.
- [ ] La CI affiche un pourcentage de couverture à chaque push.
- [ ] La couverture de `app/services.py` est ≥ 80 %.
- [ ] L'action a été assignée et réalisée par le technicien DevOps.
