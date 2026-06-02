# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Non-root user (Week 15 requirement)
RUN useradd -m -u 1000 appuser
WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

# Create required directories
RUN mkdir -p /app/logs /app/database && chown -R appuser:appuser /app

USER appuser

# Seed the database
RUN python database/seed_prices.py

EXPOSE 8000

# Health check (Week 15 requirement)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
