"""Couche de persistance (SQLite).

Modélise trois entités : campagnes, participants fictifs et événements de
simulation. Aucune donnée personnelle réelle n'est stockée : les participants
sont des alias fictifs et les jetons ne sont pas sensibles.
"""
from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS campaigns (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    scenario    TEXT    NOT NULL,
    period      TEXT    NOT NULL,
    objective   TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'Brouillon',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS participants (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    alias       TEXT    NOT NULL,
    token       TEXT    NOT NULL UNIQUE,
    token_expires_at TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sim_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    token       TEXT    NOT NULL,
    event_type  TEXT    NOT NULL,   -- 'ouverture' | 'clic' | 'signalement'
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    -- Règle d'unicité : un seul événement d'un type donné par jeton et campagne.
    UNIQUE (campaign_id, token, event_type)
);

CREATE INDEX IF NOT EXISTS idx_participants_campaign ON participants(campaign_id);
CREATE INDEX IF NOT EXISTS idx_events_campaign ON sim_events(campaign_id);
"""


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Ouvre une connexion SQLite avec les contraintes de clés étrangères."""
    path = settings.database_path
    if path != ":memory:":
        _ensure_parent_dir(path)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_cursor(conn: sqlite3.Connection) -> Iterator[sqlite3.Cursor]:
    """Contexte transactionnel : commit en cas de succès, rollback sinon."""
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def init_db(conn: sqlite3.Connection) -> None:
    """Crée le schéma s'il n'existe pas."""
    conn.executescript(SCHEMA)
    conn.commit()
