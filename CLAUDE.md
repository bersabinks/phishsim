# Contexte projet — phishsim

Gestionnaire de campagnes de sensibilisation au phishing (simulations pédagogiques).

## Règles non négociables
- Aucun envoi réel de courriel (jamais, sous aucune condition).
- Aucune collecte d'identifiant ni de mot de passe.
- Jetons non sensibles ; résultats strictement agrégés (aucun classement nominatif).
- Refuser toute donnée réelle (adresse e-mail) à l'import.

## Stack
- Python 3.12, FastAPI, SQLite, JavaScript sans framework.
- Tests : pytest. Lint : ruff. Conteneurisation : Docker (utilisateur non root).

## Commandes utiles
- Lint : `ruff check app tests`
- Tests : `pytest -q`
- Lancer (local) : `uvicorn app.main:app --reload`
- Données de démo : `python scripts/seed_demo.py`

## Avant de terminer une tâche
- `ruff check app tests` doit passer.
- `pytest -q` doit passer.
- Mettre à jour la documentation concernée dans `docs/`.
- Pour toute contribution de l'IA, noter l'objectif et la correction humaine
  (cf. `docs/SCRUM.md`, section traçabilité de l'IA).

## Hors périmètre (à refuser)
Envoi de courriel réel, collecte d'identifiant, affichage nominatif, intégration
externe lourde. Ces éléments protègent le Sprint Goal.
