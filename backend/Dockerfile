# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Non-root user (Week 15 requirement)
RUN useradd -m -u 1000 appuser

WORKDIR /app
ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/backend/database/prices.db

COPY --from=builder /install /usr/local
COPY . ./backend/

RUN mkdir -p /app/backend/logs /app/backend/database \
    && chown -R appuser:appuser /app

USER appuser

# Seed the database at build time
RUN python backend/database/seed_prices.py

EXPOSE 8000

# Health check (Week 15 requirement) — must not call the LLM
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
