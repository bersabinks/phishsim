# Architecture

Architecture **volontairement simple** : une seule application FastAPI, une base
SQLite, un front-end statique sans dépendance externe. Ce choix sert le Sprint
Goal (incrément démontrable et reproductible en 15 heures).

## 1. Vue d'ensemble

```
┌────────────────────────────────────────────────────────┐
│                      Navigateur                         │
│  dashboard.html / simulation.html + JS (fetch API)      │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP (JSON / formulaires)
┌───────────────────────────▼────────────────────────────┐
│                    FastAPI (app/main.py)                │
│  • Routes API et pages HTML                             │
│  • Middleware en-têtes de sécurité (CSP, nosniff…)      │
│  • Garde-fou « pas d'e-mail réel » (lifespan)           │
│  • Gestion d'erreurs métier → HTTP 400 lisible          │
└───────────────────────────┬────────────────────────────┘
                            │ appels de fonctions
┌───────────────────────────▼────────────────────────────┐
│              Logique métier (app/services.py)           │
│  • Validation (alias, refus e-mails réels)              │
│  • Génération de jetons non sensibles (secrets)         │
│  • Import CSV contrôlé (erreurs signalées)              │
│  • Agrégation sans classement nominatif                 │
└───────────────────────────┬────────────────────────────┘
                            │ SQL paramétré
┌───────────────────────────▼────────────────────────────┐
│                Persistance (app/db.py, SQLite)          │
│  campaigns · participants · sim_events                  │
└─────────────────────────────────────────────────────────┘
```

## 2. Modèle de données

### `campaigns`
| Champ | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name, scenario, period, objective | TEXT | obligatoires |
| status | TEXT | `Brouillon` / `Active` / `Terminée` |
| created_at | TEXT | horodatage |

### `participants`
| Champ | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| campaign_id | FK → campaigns | cascade à la suppression |
| alias | TEXT | identifiant fictif |
| token | TEXT UNIQUE | non sensible (`sim_…`) |
| token_expires_at | TEXT NULL | expiration optionnelle |

### `sim_events`
| Champ | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| campaign_id | FK → campaigns | |
| token | TEXT | non sensible |
| event_type | TEXT | `ouverture` / `clic` / `signalement` |
| created_at | TEXT | horodatage |
| | UNIQUE (campaign_id, token, event_type) | empêche le double comptage |

## 3. Parcours vertical (interface → logique → persistance)

Exemple « enregistrer un clic en simulation » :

1. **Interface** : la page `simulation.html` envoie `POST /api/events` avec le
   jeton et le type d'événement (aucun identifiant).
2. **Logique** : `services.record_event` valide le type, vérifie l'existence et
   la non-expiration du jeton, applique la règle d'unicité.
3. **Persistance** : insertion dans `sim_events` (ou détection d'un doublon).

## 4. Choix techniques et justifications

| Choix | Justification |
|---|---|
| FastAPI | Rapide à mettre en place, documentation OpenAPI automatique, validation native. |
| SQLite | Zéro configuration, parfait pour un MVP démontrable ; fichier unique facile à sauvegarder. |
| JS sans framework | Pas de build, CSP stricte possible, surface d'attaque réduite. |
| Jetons `secrets.token_urlsafe` | Aléa cryptographique, non devinable, non sensible. |
| Docker + compte non privilégié | Reproductibilité et droits minimaux (DoD sécurité). |

## 5. Sécurité (résumé)

- En-têtes : `Content-Security-Policy`, `X-Content-Type-Options`,
  `X-Frame-Options`, `Referrer-Policy`.
- Entrées validées et requêtes SQL **paramétrées** (pas d'injection).
- Échappement HTML côté client pour les alias affichés.
- Conteneur en utilisateur non root, configuration externalisée.
- Détail complet dans [`NOTE_ETHIQUE_SECURITE.md`](NOTE_ETHIQUE_SECURITE.md).
