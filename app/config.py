"""Configuration de l'application, externalisée via variables d'environnement.

Aucune valeur sensible n'est codée en dur. La configuration est lue au
démarrage afin de respecter la Definition of Done (configuration externalisée).
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Paramètres applicatifs, immuables après chargement."""

    # Emplacement de la base SQLite. ":memory:" est utilisé par les tests.
    database_path: str = os.getenv("PHISHSIM_DB_PATH", "data/phishsim.db")

    # Sécurité : l'envoi réel de courriel est interdit par conception.
    # Ce drapeau ne peut JAMAIS être activé ; il est présent pour rendre
    # explicite l'interdiction et la rendre testable.
    real_email_enabled: bool = False

    # Durée de vie d'un jeton de participation, en heures. 0 = pas d'expiration.
    token_ttl_hours: int = _get_int("PHISHSIM_TOKEN_TTL_HOURS", 72)

    # Nombre maximal de participants importables en une fois (garde-fou).
    max_import_rows: int = _get_int("PHISHSIM_MAX_IMPORT_ROWS", 500)

    # Mode debug (désactivé par défaut, jamais en production).
    debug: bool = _get_bool("PHISHSIM_DEBUG", False)


settings = Settings()
