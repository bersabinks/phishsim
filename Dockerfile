# Image légère et reproductible.
FROM python:3.12-slim

# Évite les fichiers .pyc et force la sortie non bufferisée (logs lisibles).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PHISHSIM_DB_PATH=/app/data/phishsim.db

WORKDIR /app

# Installer les dépendances en couche séparée pour profiter du cache.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code applicatif.
COPY app ./app

# Sécurité : créer et utiliser un compte NON privilégié (DoD : droits minimaux).
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Healthcheck natif : interroge la sonde /health.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; \
    sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else sys.exit(1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
