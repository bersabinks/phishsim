# Gestionnaire de campagnes de sensibilisation au phishing

Application web permettant de **préparer une campagne de sensibilisation**, de
**simuler la participation** et d'**analyser des résultats agrégés**, sans jamais
envoyer de courriel réel ni collecter de mot de passe.

> Mastère ESI — Mini-projet Scrum (Fiche 4). Domaine : cybersécurité / sensibilisation.

---

## 1. Principe de sécurité

Ce produit est **pédagogique et défensif**. Par conception :

- **Aucun envoi réel de courriel.** Un garde-fou bloque le démarrage si l'option
  était activée (elle ne peut pas l'être).
- **Aucune collecte d'identifiant.** La page de simulation ne contient aucun champ
  de mot de passe ; elle affiche un message de sensibilisation.
- **Jetons non sensibles.** Les jetons de participation sont des chaînes aléatoires
  opaques, sans donnée personnelle.
- **Résultats agrégés uniquement.** Aucun classement nominatif n'est exposé.
- **Refus des données réelles.** L'import rejette toute valeur ressemblant à une
  adresse e-mail.

---

## 2. Installation et lancement

### Option A — Docker (recommandé)

Prérequis : Docker et Docker Compose.

```bash
docker compose up --build
```

L'application est disponible sur <http://localhost:8000>.
Le healthcheck du conteneur interroge automatiquement `/health`.

### Option B — Local (sans Docker)

Prérequis : Python 3.12+.

```bash
bash scripts/run_local.sh
```

Ou manuellement :

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python scripts/seed_demo.py        # données de démonstration (optionnel)
uvicorn app.main:app --reload
```

> **Lancement reproductible en moins de cinq minutes.** Cf.
> [`docs/EXPLOITATION.md`](docs/EXPLOITATION.md).

---

## 3. Parcours métier (démonstration)

1. Ouvrir <http://localhost:8000>.
2. **Créer une campagne** (nom, scénario, période, objectif) → statut *Brouillon*.
3. **Ajouter des participants fictifs**, manuellement ou via
   [`docs/participants_exemple.csv`](docs/participants_exemple.csv).
4. Copier un **lien de simulation** généré et l'ouvrir : la page de sensibilisation
   s'affiche, sans aucun champ d'identifiant.
5. Cliquer sur les boutons pour enregistrer des **événements anonymes**.
6. Revenir au tableau de bord et **rafraîchir les indicateurs agrégés**.
7. Cliquer **Exporter PDF** pour télécharger un rapport des indicateurs (sans donnée
   nominative ni jeton) via `GET /api/campaigns/{id}/export`.
8. Ouvrir <http://localhost:8000/compare> pour **comparer deux campagnes** côte à
   côte via `GET /api/compare?campaign_a={id}&campaign_b={id}`.
9. Consulter <http://localhost:8000/conseils> pour la **bibliothèque de bonnes
   pratiques anti-phishing** (contenu statique).

Le scénario complet est couvert par 29 tests d'intégration (`pytest -q`).

---

## 4. Architecture

```
Navigateur
   │  HTML + JS sobre (aucune dépendance externe, CSP stricte)
   ▼
FastAPI (app/main.py)
   ├── Routes API (campagnes, participants, simulation, résultats)
   ├── Middleware d'en-têtes de sécurité
   ├── Garde-fou « pas d'e-mail réel » au démarrage
   ▼
Logique métier (app/services.py)
   ├── Validation des entrées (alias, refus des e-mails)
   ├── Génération de jetons non sensibles
   ├── Import CSV contrôlé
   └── Agrégation sans classement nominatif
   ▼
Persistance SQLite (app/db.py)
   └── campaigns · participants · sim_events
```

Composants : voir [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 5. Comptes et données fictifs

- Aucun compte utilisateur n'est requis pour la démonstration (pas
  d'authentification dans le périmètre).
- Les participants sont des **alias fictifs** (`participant_01`, …).
- Les jetons sont générés aléatoirement (préfixe `sim_`), non sensibles.
- Le script `scripts/seed_demo.py` crée un jeu de données de démonstration complet.

---

## 6. Configuration (variables d'environnement)

| Variable | Défaut | Rôle |
|---|---|---|
| `PHISHSIM_DB_PATH` | `data/phishsim.db` | Emplacement de la base SQLite |
| `PHISHSIM_TOKEN_TTL_HOURS` | `72` | Durée de vie d'un jeton (0 = sans expiration) |
| `PHISHSIM_MAX_IMPORT_ROWS` | `500` | Garde-fou sur l'import CSV |
| `PHISHSIM_DEBUG` | `false` | Mode debug (jamais en production) |

---

## 7. Tests, qualité et CI

```bash
pip install -r requirements-dev.txt
ruff check app tests      # lint
pytest -q                 # 29 tests unitaires + intégration
```

La CI (GitHub Actions, `.github/workflows/ci.yml`) exécute : lint, tests,
analyse de dépendances (`pip-audit` — 0 CVE), recherche de secrets (`gitleaks`) et
build de l'image Docker avec vérification du healthcheck.

---

## 8. Limites connues

- Pas d'authentification ni de gestion multi-utilisateurs (hors périmètre).
- SQLite : adapté à la démonstration, pas à une forte charge concurrente.
- Pas d'envoi de courriel (volontaire et définitif).
- L'expiration automatique des jetons est configurable mais non déclenchée
  automatiquement (pas de tâche de fond dans le périmètre).
- Les extensions post-MVP livrées : page `/conseils`, export PDF agrégé,
  comparaison de campagnes.

---

## 9. Note éthique et sécurité

Voir [`docs/NOTE_ETHIQUE_SECURITE.md`](docs/NOTE_ETHIQUE_SECURITE.md).
