"""Règles métier et logique applicative.

Points de sécurité clés (Definition of Done / note éthique) :
- Les jetons de participation sont opaques et NON sensibles (pas de PII).
- L'import CSV rejette toute donnée ressemblant à une adresse e-mail réelle.
- Les indicateurs sont AGRÉGÉS : aucun classement nominatif n'est exposé.
- Aucun mot de passe / identifiant n'est jamais collecté ni stocké.
"""
from __future__ import annotations

import csv
import io
import re
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta

from app.config import settings
from app.db import db_cursor

# --- Constantes de validation ---------------------------------------------

VALID_STATUSES = {"Brouillon", "Active", "Terminée"}
VALID_EVENT_TYPES = {"ouverture", "clic", "signalement"}

# Détection grossière d'une adresse e-mail (pour la REFUSER à l'import).
_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

# Un alias fictif accepté : lettres, chiffres, tirets, underscores, espaces.
_ALIAS_RE = re.compile(r"^[\w\- ]{1,60}$", re.UNICODE)


class ValidationError(ValueError):
    """Erreur métier renvoyée au client sous forme de message lisible."""


# --- Jetons -----------------------------------------------------------------

def generate_token() -> str:
    """Génère un jeton opaque, non sensible et non devinable.

    Le jeton ne contient aucune information personnelle : c'est une simple
    chaîne aléatoire en base URL-safe.
    """
    return "sim_" + secrets.token_urlsafe(16)


def _token_expiry() -> str | None:
    """Calcule la date d'expiration du jeton selon la configuration."""
    if settings.token_ttl_hours <= 0:
        return None
    expires = datetime.now(UTC) + timedelta(hours=settings.token_ttl_hours)
    return expires.strftime("%Y-%m-%d %H:%M:%S")


def is_token_expired(expires_at: str | None) -> bool:
    """Indique si un jeton est expiré (False si pas d'expiration définie)."""
    if not expires_at:
        return False
    try:
        expiry = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=UTC
        )
    except ValueError:
        return False
    return datetime.now(UTC) > expiry


# --- Campagnes --------------------------------------------------------------

def create_campaign(
    conn: sqlite3.Connection,
    name: str,
    scenario: str,
    period: str,
    objective: str,
) -> int:
    """Crée une campagne au statut Brouillon. Retourne son identifiant."""
    name = (name or "").strip()
    scenario = (scenario or "").strip()
    period = (period or "").strip()
    objective = (objective or "").strip()

    if not name:
        raise ValidationError("Le nom de la campagne est obligatoire.")
    if len(name) > 120:
        raise ValidationError("Le nom de la campagne est trop long (max 120).")
    if not scenario:
        raise ValidationError("Le scénario est obligatoire.")
    if not period:
        raise ValidationError("La période est obligatoire.")
    if not objective:
        raise ValidationError("L'objectif est obligatoire.")

    with db_cursor(conn) as cur:
        cur.execute(
            "INSERT INTO campaigns (name, scenario, period, objective, status) "
            "VALUES (?, ?, ?, ?, 'Brouillon')",
            (name, scenario, period, objective),
        )
        return int(cur.lastrowid)


def get_campaign(conn: sqlite3.Connection, campaign_id: int) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    return cur.fetchone()


def list_campaigns(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    cur = conn.execute("SELECT * FROM campaigns ORDER BY created_at DESC, id DESC")
    return cur.fetchall()


def set_campaign_status(
    conn: sqlite3.Connection, campaign_id: int, status: str
) -> None:
    if status not in VALID_STATUSES:
        raise ValidationError(f"Statut invalide : {status!r}.")
    if get_campaign(conn, campaign_id) is None:
        raise ValidationError("Campagne introuvable.")
    with db_cursor(conn) as cur:
        cur.execute(
            "UPDATE campaigns SET status = ? WHERE id = ?", (status, campaign_id)
        )


# --- Participants -----------------------------------------------------------

def _validate_alias(alias: str) -> str:
    alias = (alias or "").strip()
    if not alias:
        raise ValidationError("L'alias du participant est vide.")
    if _EMAIL_RE.search(alias):
        raise ValidationError(
            "Donnée refusée : un alias ne doit pas contenir d'adresse e-mail "
            "réelle. Utilisez un identifiant fictif."
        )
    if not _ALIAS_RE.match(alias):
        raise ValidationError(
            f"Alias invalide : {alias!r}. Caractères autorisés : lettres, "
            "chiffres, espaces, tirets."
        )
    return alias


def add_participant(
    conn: sqlite3.Connection, campaign_id: int, alias: str
) -> dict:
    """Ajoute un participant fictif et génère son jeton non sensible."""
    if get_campaign(conn, campaign_id) is None:
        raise ValidationError("Campagne introuvable.")
    alias = _validate_alias(alias)
    token = generate_token()
    expires = _token_expiry()
    with db_cursor(conn) as cur:
        cur.execute(
            "INSERT INTO participants (campaign_id, alias, token, token_expires_at) "
            "VALUES (?, ?, ?, ?)",
            (campaign_id, alias, token, expires),
        )
        pid = int(cur.lastrowid)
    return {"id": pid, "alias": alias, "token": token, "token_expires_at": expires}


def import_participants_csv(
    conn: sqlite3.Connection, campaign_id: int, csv_text: str
) -> dict:
    """Importe des participants depuis un CSV.

    Import contrôlé : chaque ligne est validée, les erreurs sont signalées
    sans interrompre l'import des lignes valides, et aucune donnée réelle
    (e-mail) n'est acceptée.

    Format attendu : une colonne 'alias' (en-tête optionnel).
    """
    if get_campaign(conn, campaign_id) is None:
        raise ValidationError("Campagne introuvable.")

    reader = csv.reader(io.StringIO(csv_text))
    rows = [r for r in reader if any(cell.strip() for cell in r)]

    if not rows:
        raise ValidationError("Le fichier CSV est vide.")
    if len(rows) > settings.max_import_rows:
        raise ValidationError(
            f"Trop de lignes ({len(rows)}). Maximum : {settings.max_import_rows}."
        )

    # Détecte et ignore une éventuelle ligne d'en-tête.
    start = 0
    first_cell = rows[0][0].strip().lower()
    if first_cell in {"alias", "participant", "nom", "name"}:
        start = 1

    imported: list[dict] = []
    errors: list[str] = []
    for idx, row in enumerate(rows[start:], start=start + 1):
        raw_alias = row[0] if row else ""
        try:
            participant = add_participant(conn, campaign_id, raw_alias)
            imported.append(participant)
        except ValidationError as exc:
            errors.append(f"Ligne {idx} : {exc}")

    return {
        "imported_count": len(imported),
        "error_count": len(errors),
        "errors": errors,
        "participants": imported,
    }


def list_participants(
    conn: sqlite3.Connection, campaign_id: int
) -> list[sqlite3.Row]:
    cur = conn.execute(
        "SELECT * FROM participants WHERE campaign_id = ? ORDER BY id",
        (campaign_id,),
    )
    return cur.fetchall()


def get_participant_by_token(
    conn: sqlite3.Connection, token: str
) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM participants WHERE token = ?", (token,))
    return cur.fetchone()


# --- Simulation et événements ----------------------------------------------

def record_event(
    conn: sqlite3.Connection, token: str, event_type: str
) -> dict:
    """Enregistre un événement de simulation pour un jeton.

    Sécurité : aucun identifiant n'est collecté ; seul le jeton (non sensible)
    et le type d'événement sont conservés, horodatés. La règle d'unicité
    empêche le double comptage.
    """
    if event_type not in VALID_EVENT_TYPES:
        raise ValidationError(f"Type d'événement invalide : {event_type!r}.")

    participant = get_participant_by_token(conn, token)
    if participant is None:
        raise ValidationError("Jeton inconnu.")
    if is_token_expired(participant["token_expires_at"]):
        raise ValidationError("Jeton expiré.")

    with db_cursor(conn) as cur:
        try:
            cur.execute(
                "INSERT INTO sim_events (campaign_id, token, event_type) "
                "VALUES (?, ?, ?)",
                (participant["campaign_id"], token, event_type),
            )
            created = True
        except sqlite3.IntegrityError:
            # Événement déjà enregistré (règle unique) : pas une erreur fatale.
            created = False

    return {
        "recorded": created,
        "event_type": event_type,
        "duplicate": not created,
    }


def aggregate_results(conn: sqlite3.Connection, campaign_id: int) -> dict:
    """Calcule les indicateurs AGRÉGÉS d'une campagne.

    Ne renvoie JAMAIS de données nominatives ni de classement individuel :
    uniquement des compteurs et des taux globaux.
    """
    if get_campaign(conn, campaign_id) is None:
        raise ValidationError("Campagne introuvable.")

    total = conn.execute(
        "SELECT COUNT(*) AS n FROM participants WHERE campaign_id = ?",
        (campaign_id,),
    ).fetchone()["n"]

    counts = {etype: 0 for etype in VALID_EVENT_TYPES}
    rows = conn.execute(
        "SELECT event_type, COUNT(DISTINCT token) AS n FROM sim_events "
        "WHERE campaign_id = ? GROUP BY event_type",
        (campaign_id,),
    ).fetchall()
    for row in rows:
        counts[row["event_type"]] = row["n"]

    def rate(numerator: int) -> float:
        return round(100.0 * numerator / total, 1) if total else 0.0

    return {
        "participants_total": total,
        "ouvertures": counts["ouverture"],
        "clics": counts["clic"],
        "signalements": counts["signalement"],
        "taux_ouverture": rate(counts["ouverture"]),
        "taux_clic": rate(counts["clic"]),
        "taux_signalement": rate(counts["signalement"]),
    }
