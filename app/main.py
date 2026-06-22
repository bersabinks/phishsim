"""Application FastAPI : Gestionnaire de campagnes de sensibilisation au phishing.

Parcours métier de bout en bout :
1. Créer une campagne (US1)
2. Ajouter des participants fictifs, manuellement ou par CSV (US2)
3. Générer un jeton de participation non sensible (US3)
4. Page de simulation qui ne collecte aucun identifiant (US3)
5. Enregistrer des événements horodatés (US4)
6. Consulter des indicateurs agrégés, sans classement nominatif (US5)

L'envoi réel de courriel est interdit par conception (cf. config + note éthique).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import services
from app.config import settings
from app.db import get_connection, init_db

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Connexion unique au niveau application (SQLite, accès séquentiel).
_conn = get_connection()
init_db(_conn)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Garde-fou de sécurité au démarrage.

    Matérialise une exigence non négociable du cahier des charges :
    l'application ne doit jamais envoyer de courriel réel.
    """
    if settings.real_email_enabled:  # pragma: no cover - garde-fou
        raise RuntimeError(
            "Envoi réel de courriel interdit par conception. Arrêt immédiat."
        )
    yield


app = FastAPI(
    title="Gestionnaire de campagnes de sensibilisation au phishing",
    description="Simulations pédagogiques sans envoi réel ni collecte d'identifiants.",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def get_db():
    return _conn


# --- En-têtes de sécurité ---------------------------------------------------

_DOCS_PATHS = {"/docs", "/redoc", "/openapi.json"}

# Swagger UI charge ses assets depuis cdn.jsdelivr.net ; CSP permissif pour /docs.
_CSP_DOCS = (
    "default-src 'self' cdn.jsdelivr.net; "
    "script-src 'self' cdn.jsdelivr.net 'unsafe-inline'; "
    "style-src 'self' cdn.jsdelivr.net 'unsafe-inline'; "
    "img-src 'self' data: cdn.jsdelivr.net"
)
_CSP_APP = "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:"


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    csp = _CSP_DOCS if request.url.path in _DOCS_PATHS else _CSP_APP
    response.headers["Content-Security-Policy"] = csp
    return response


# --- Gestion d'erreurs métier ----------------------------------------------

@app.exception_handler(services.ValidationError)
async def _validation_handler(request: Request, exc: services.ValidationError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


# --- Healthcheck ------------------------------------------------------------

@app.get("/health", tags=["système"])
def health(db=Depends(get_db)):
    """Sonde de santé : vérifie l'accès à la base de données."""
    try:
        db.execute("SELECT 1").fetchone()
        return {"status": "ok", "real_email_enabled": settings.real_email_enabled}
    except Exception as exc:  # pragma: no cover - sonde
        raise HTTPException(
            status_code=503, detail=f"DB indisponible : {exc}"
        ) from exc


# --- API : campagnes --------------------------------------------------------

@app.post("/api/campaigns", tags=["campagnes"])
def api_create_campaign(
    name: str = Form(...),
    scenario: str = Form(...),
    period: str = Form(...),
    objective: str = Form(...),
    db=Depends(get_db),
):
    campaign_id = services.create_campaign(db, name, scenario, period, objective)
    return {"id": campaign_id, "status": "Brouillon"}


@app.get("/api/campaigns", tags=["campagnes"])
def api_list_campaigns(db=Depends(get_db)):
    return [dict(row) for row in services.list_campaigns(db)]


@app.get("/api/campaigns/{campaign_id}", tags=["campagnes"])
def api_get_campaign(campaign_id: int, db=Depends(get_db)):
    campaign = services.get_campaign(db, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campagne introuvable.")
    return dict(campaign)


@app.post("/api/campaigns/{campaign_id}/status", tags=["campagnes"])
def api_set_status(campaign_id: int, status: str = Form(...), db=Depends(get_db)):
    services.set_campaign_status(db, campaign_id, status)
    return {"id": campaign_id, "status": status}


# --- API : participants -----------------------------------------------------

@app.post("/api/campaigns/{campaign_id}/participants", tags=["participants"])
def api_add_participant(
    campaign_id: int, alias: str = Form(...), db=Depends(get_db)
):
    return services.add_participant(db, campaign_id, alias)


@app.post("/api/campaigns/{campaign_id}/participants/import", tags=["participants"])
async def api_import_participants(
    campaign_id: int, file: UploadFile, db=Depends(get_db)
):
    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, detail="Le fichier doit être encodé en UTF-8."
        ) from None
    return services.import_participants_csv(db, campaign_id, text)


@app.get("/api/campaigns/{campaign_id}/participants", tags=["participants"])
def api_list_participants(campaign_id: int, db=Depends(get_db)):
    # On expose alias et jeton, mais aucune donnée réelle n'existe par conception.
    return [dict(row) for row in services.list_participants(db, campaign_id)]


# --- API : simulation et résultats -----------------------------------------

@app.post("/api/events", tags=["simulation"])
def api_record_event(
    token: str = Form(...), event_type: str = Form(...), db=Depends(get_db)
):
    return services.record_event(db, token, event_type)


@app.get("/api/campaigns/{campaign_id}/results", tags=["simulation"])
def api_results(campaign_id: int, db=Depends(get_db)):
    """Indicateurs agrégés uniquement (aucun classement nominatif)."""
    return services.aggregate_results(db, campaign_id)


@app.get("/api/compare", tags=["campagnes"])
def api_compare(campaign_a: int, campaign_b: int, db=Depends(get_db)):
    """Indicateurs agrégés de deux campagnes côte à côte.

    Aucune donnée nominative ni jeton n'est inclus dans la réponse.
    """
    camp_a = services.get_campaign(db, campaign_a)
    if camp_a is None:
        raise HTTPException(
            status_code=404, detail=f"Campagne {campaign_a} introuvable."
        )
    camp_b = services.get_campaign(db, campaign_b)
    if camp_b is None:
        raise HTTPException(
            status_code=404, detail=f"Campagne {campaign_b} introuvable."
        )
    results_a = services.aggregate_results(db, campaign_a)
    results_b = services.aggregate_results(db, campaign_b)
    return {
        "campaign_a": {"id": camp_a["id"], "name": camp_a["name"], **results_a},
        "campaign_b": {"id": camp_b["id"], "name": camp_b["name"], **results_b},
    }


@app.get("/api/campaigns/{campaign_id}/export", tags=["simulation"])
def api_export_pdf(campaign_id: int, db=Depends(get_db)):
    """Génère un rapport PDF des indicateurs agrégés.

    Le document ne contient aucune donnée nominative ni aucun jeton.
    """
    campaign = services.get_campaign(db, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campagne introuvable.")
    results = services.aggregate_results(db, campaign_id)
    pdf_bytes = services.generate_pdf_report(dict(campaign), results)
    filename = f"rapport_campagne_{campaign_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Pages HTML -------------------------------------------------------------

@app.get("/compare", response_class=HTMLResponse, tags=["pages"])
def page_compare(request: Request, db=Depends(get_db)):
    campaigns = [dict(row) for row in services.list_campaigns(db)]
    return templates.TemplateResponse(
        request, "compare.html", {"campaigns": campaigns}
    )


@app.get("/conseils", response_class=HTMLResponse, tags=["pages"])
def page_conseils(request: Request):
    """Page statique de bonnes pratiques anti-phishing."""
    return templates.TemplateResponse(request, "conseils.html", {})


@app.get("/", response_class=HTMLResponse, tags=["pages"])
def page_dashboard(request: Request, db=Depends(get_db)):
    campaigns = [dict(row) for row in services.list_campaigns(db)]
    return templates.TemplateResponse(
        request, "dashboard.html", {"campaigns": campaigns}
    )


@app.get("/simulation/{token}", response_class=HTMLResponse, tags=["pages"])
def page_simulation(token: str, request: Request, db=Depends(get_db)):
    """Page de simulation pédagogique.

    IMPORTANT : cette page ne contient AUCUN champ d'identifiant ni de mot de
    passe. Elle présente un message de sensibilisation et enregistre seulement
    des événements anonymes liés au jeton.
    """
    participant = services.get_participant_by_token(db, token)
    if participant is None:
        return templates.TemplateResponse(
            request,
            "simulation.html",
            {"token": token, "valid": False, "expired": False},
            status_code=404,
        )
    expired = services.is_token_expired(participant["token_expires_at"])
    return templates.TemplateResponse(
        request,
        "simulation.html",
        {"token": token, "valid": True, "expired": expired},
    )
