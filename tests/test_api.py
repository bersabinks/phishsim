"""Tests d'intégration de l'API (scénario de démonstration de bout en bout).

Reproduit le scénario principal exigé en Sprint Review :
créer une campagne, importer des participants, jouer des parcours,
puis afficher uniquement les résultats agrégés.
"""
import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    # Base isolée par test.
    monkeypatch.setenv("PHISHSIM_DB_PATH", str(tmp_path / "test.db"))
    import app.config as config
    importlib.reload(config)
    import app.db as db
    importlib.reload(db)
    import app.main as main
    importlib.reload(main)
    return TestClient(main.app)


def test_healthcheck(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    # Sécurité : l'envoi réel de courriel doit rester désactivé.
    assert body["real_email_enabled"] is False


def test_full_demo_scenario(client):
    # 1. Créer une campagne
    res = client.post(
        "/api/campaigns",
        data={
            "name": "Campagne démo",
            "scenario": "Fausse facture",
            "period": "2026-07",
            "objective": "Sensibiliser",
        },
    )
    assert res.status_code == 200
    cid = res.json()["id"]

    # 2. Importer cinq participants fictifs (via CSV)
    csv_content = "alias\np01\np02\np03\np04\np05\n"
    res = client.post(
        f"/api/campaigns/{cid}/participants/import",
        files={"file": ("participants.csv", csv_content, "text/csv")},
    )
    assert res.status_code == 200
    assert res.json()["imported_count"] == 5

    # Récupérer les jetons
    res = client.get(f"/api/campaigns/{cid}/participants")
    participants = res.json()
    assert len(participants) == 5
    tokens = [p["token"] for p in participants]

    # 3. Jouer deux parcours (deux clics, un signalement)
    client.post("/api/events", data={"token": tokens[0], "event_type": "clic"})
    client.post("/api/events", data={"token": tokens[1], "event_type": "clic"})
    client.post("/api/events", data={"token": tokens[2], "event_type": "signalement"})

    # 4. Afficher uniquement les résultats agrégés
    res = client.get(f"/api/campaigns/{cid}/results")
    assert res.status_code == 200
    r = res.json()
    assert r["participants_total"] == 5
    assert r["clics"] == 2
    assert r["signalements"] == 1
    assert r["taux_clic"] == 40.0
    # Aucun jeton ne doit fuiter dans les résultats agrégés.
    assert "sim_" not in str(r)


def test_error_scenario_unknown_token(client):
    """Scénario d'erreur : événement sur un jeton inexistant."""
    res = client.post(
        "/api/events", data={"token": "sim_faux", "event_type": "clic"}
    )
    assert res.status_code == 400
    assert "inconnu" in res.json()["detail"].lower()


def test_simulation_page_collects_no_credentials(client):
    """La page de simulation ne doit contenir aucun champ d'identifiant."""
    res = client.post(
        "/api/campaigns",
        data={"name": "C", "scenario": "s", "period": "p", "objective": "o"},
    )
    cid = res.json()["id"]
    res = client.post(
        f"/api/campaigns/{cid}/participants", data={"alias": "p1"}
    )
    token = res.json()["token"]

    page = client.get(f"/simulation/{token}")
    assert page.status_code == 200
    html = page.text.lower()
    # Aucun champ de mot de passe / saisie d'identifiant.
    assert 'type="password"' not in html
    assert "mot de passe" not in html or "aucun identifiant" in html


def test_export_pdf(client):
    """Le PDF doit être généré (200, application/pdf) sans aucun jeton."""
    res = client.post(
        "/api/campaigns",
        data={"name": "Camp PDF", "scenario": "s", "period": "p", "objective": "o"},
    )
    cid = res.json()["id"]
    client.post(f"/api/campaigns/{cid}/participants", data={"alias": "p1"})

    res = client.get(f"/api/campaigns/{cid}/export")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    # Aucun jeton ne doit figurer dans le document.
    assert b"sim_" not in res.content


def test_export_pdf_not_found(client):
    """L'export d'une campagne inexistante renvoie 404."""
    res = client.get("/api/campaigns/9999/export")
    assert res.status_code == 404


def test_conseils_page(client):
    """La page /conseils doit être accessible et renvoyer du HTML."""
    res = client.get("/conseils")
    assert res.status_code == 200
    assert "anti-phishing" in res.text.lower()


def test_security_headers_present(client):
    res = client.get("/")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
