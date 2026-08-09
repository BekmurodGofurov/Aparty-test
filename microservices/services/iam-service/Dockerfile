# ── IAM Service Dockerfile ────────────────────────────────────────────────────
# Uses python:3.11-slim to keep the image small (~200 MB vs ~900 MB for full).
# The .venv directory is NOT copied — pip installs directly into the image's
# system Python, which is the correct pattern for Docker containers.

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Layer cache optimization ──────────────────────────────────────────────────
# Copy requirements first so that this layer is only rebuilt when deps change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
COPY app/ ./app/

# ── Runtime ───────────────────────────────────────────────────────────────────
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
