#!/usr/bin/env bash
# Lancement local rapide (sans Docker).
# Procédure reproductible en moins de cinq minutes.
set -euo pipefail

echo "==> Création de l'environnement virtuel"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installation des dépendances"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "==> (Optionnel) Données de démonstration"
python scripts/seed_demo.py || true

echo "==> Démarrage du serveur sur http://127.0.0.1:8000"
exec uvicorn app.main:app --host 127.0.0.1 --port 8000
