# ── Build stage ──────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0

COPY . .
RUN python manage.py collectstatic --noinput --clear 2>/dev/null || true

# ── Runtime stage ────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 --no-create-home appuser && \
    mkdir -p /app/staticfiles && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
