#!/usr/bin/env python3
"""Initialise des données de démonstration.

Crée une campagne d'exemple, importe cinq participants fictifs et joue
quelques événements, afin de pouvoir démontrer le produit immédiatement.

Usage : python scripts/seed_demo.py
"""
import os
import sys

# Permet d'exécuter le script depuis la racine du projet.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import services  # noqa: E402
from app.db import get_connection, init_db  # noqa: E402


def main() -> None:
    conn = get_connection()
    init_db(conn)

    cid = services.create_campaign(
        conn,
        name="Campagne de démonstration",
        scenario="Fausse facture fournisseur urgente",
        period="2026-07-01 → 2026-07-15",
        objective="Mesurer le taux de signalement",
    )
    services.set_campaign_status(conn, cid, "Active")

    csv_text = "alias\n" + "\n".join(f"participant_{i:02d}" for i in range(1, 6))
    result = services.import_participants_csv(conn, cid, csv_text)

    participants = services.list_participants(conn, cid)
    tokens = [p["token"] for p in participants]

    # Jouer deux parcours : deux clics et un signalement.
    services.record_event(conn, tokens[0], "clic")
    services.record_event(conn, tokens[1], "clic")
    services.record_event(conn, tokens[2], "signalement")

    agg = services.aggregate_results(conn, cid)
    conn.close()

    print(f"Campagne #{cid} créée et activée.")
    print(f"Participants importés : {result['imported_count']}")
    print(f"Indicateurs agrégés : {agg}")
    print("\nLiens de simulation :")
    for p in participants:
        print(f"  - {p['alias']} : /simulation/{p['token']}")


if __name__ == "__main__":
    main()
