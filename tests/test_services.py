"""Tests unitaires de la logique métier.

Couvre le scénario nominal et les scénarios d'erreur / sécurité :
- création et validation de campagnes
- ajout de participants + refus des données réelles (e-mails)
- import CSV contrôlé avec signalement d'erreurs
- jetons non sensibles + expiration
- règle d'unicité des événements
- agrégation sans classement nominatif
"""
import sqlite3

import pytest

from app import services
from app.db import init_db


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    init_db(c)
    yield c
    c.close()


@pytest.fixture()
def campaign_id(conn):
    return services.create_campaign(
        conn, "Test", "Faux colis", "2026-07", "Mesurer signalements"
    )


# --- Campagnes --------------------------------------------------------------

def test_create_campaign_ok(conn):
    cid = services.create_campaign(conn, "C1", "Scénario", "2026", "Obj")
    row = services.get_campaign(conn, cid)
    assert row["status"] == "Brouillon"
    assert row["name"] == "C1"


def test_create_campaign_empty_name_rejected(conn):
    with pytest.raises(services.ValidationError):
        services.create_campaign(conn, "  ", "s", "p", "o")


def test_set_status_invalid_rejected(conn, campaign_id):
    with pytest.raises(services.ValidationError):
        services.set_campaign_status(conn, campaign_id, "Inexistant")


def test_set_status_ok(conn, campaign_id):
    services.set_campaign_status(conn, campaign_id, "Active")
    assert services.get_campaign(conn, campaign_id)["status"] == "Active"


# --- Participants & sécurité ------------------------------------------------

def test_add_participant_generates_token(conn, campaign_id):
    p = services.add_participant(conn, campaign_id, "alice_fictive")
    assert p["token"].startswith("sim_")
    assert len(p["token"]) > 10


def test_token_is_not_sensitive(conn, campaign_id):
    """Le jeton ne doit contenir aucune donnée personnelle, juste de l'aléa."""
    p = services.add_participant(conn, campaign_id, "bob_fictif")
    assert "bob" not in p["token"].lower()


def test_email_rejected_on_add(conn, campaign_id):
    """Sécurité : une adresse e-mail réelle doit être refusée."""
    with pytest.raises(services.ValidationError):
        services.add_participant(conn, campaign_id, "vrai.nom@entreprise.com")


def test_alias_invalid_chars_rejected(conn, campaign_id):
    with pytest.raises(services.ValidationError):
        services.add_participant(conn, campaign_id, "bad<script>")


# --- Import CSV -------------------------------------------------------------

def test_csv_import_nominal(conn, campaign_id):
    csv_text = "alias\nparticipant_01\nparticipant_02\nparticipant_03\n"
    result = services.import_participants_csv(conn, campaign_id, csv_text)
    assert result["imported_count"] == 3
    assert result["error_count"] == 0


def test_csv_import_reports_errors_without_aborting(conn, campaign_id):
    """Import contrôlé : lignes valides importées, erreurs signalées."""
    csv_text = "participant_ok\nmail.reel@test.fr\nautre_ok\n"
    result = services.import_participants_csv(conn, campaign_id, csv_text)
    assert result["imported_count"] == 2
    assert result["error_count"] == 1
    assert "Ligne" in result["errors"][0]


def test_csv_empty_rejected(conn, campaign_id):
    with pytest.raises(services.ValidationError):
        services.import_participants_csv(conn, campaign_id, "\n\n")


# --- Événements et unicité --------------------------------------------------

def test_record_event_nominal(conn, campaign_id):
    p = services.add_participant(conn, campaign_id, "p1")
    res = services.record_event(conn, p["token"], "clic")
    assert res["recorded"] is True


def test_record_event_unique_rule(conn, campaign_id):
    """Un même type d'événement n'est compté qu'une fois par jeton."""
    p = services.add_participant(conn, campaign_id, "p1")
    services.record_event(conn, p["token"], "clic")
    second = services.record_event(conn, p["token"], "clic")
    assert second["duplicate"] is True


def test_record_event_unknown_token_rejected(conn):
    with pytest.raises(services.ValidationError):
        services.record_event(conn, "sim_inexistant", "clic")


def test_record_event_invalid_type_rejected(conn, campaign_id):
    p = services.add_participant(conn, campaign_id, "p1")
    with pytest.raises(services.ValidationError):
        services.record_event(conn, p["token"], "telechargement")


# --- Agrégation -------------------------------------------------------------

def test_aggregate_no_nominative_data(conn, campaign_id):
    """Les résultats agrégés ne doivent exposer aucun alias ni jeton."""
    p1 = services.add_participant(conn, campaign_id, "p1")
    services.add_participant(conn, campaign_id, "p2")
    services.record_event(conn, p1["token"], "clic")
    results = services.aggregate_results(conn, campaign_id)
    flat = str(results)
    assert "p1" not in flat and "p2" not in flat
    assert "sim_" not in flat
    assert results["participants_total"] == 2
    assert results["clics"] == 1
    assert results["taux_clic"] == 50.0


def test_aggregate_rates_zero_when_empty(conn, campaign_id):
    results = services.aggregate_results(conn, campaign_id)
    assert results["taux_clic"] == 0.0
    assert results["participants_total"] == 0
