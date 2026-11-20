# ==============================================================================
# GroundCheck AI — Production Backend Dockerfile
# ==============================================================================
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    STORAGE_DIR=/data/groundcheck/uploads

WORKDIR /app

# Install security updates and minimal build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application source code and canonical benchmark documents
COPY backend /app/backend
COPY Apex_Quartz_Quarry_Test_EIA.pdf /app/Apex_Quartz_Quarry_Test_EIA.pdf

# Create persistent storage directory and dedicated non-root user
RUN mkdir -p /data/groundcheck/uploads && \
    useradd -m -u 1001 groundcheck && \
    chown -R groundcheck:groundcheck /app /data/groundcheck

USER groundcheck

EXPOSE 8000

# Safe container health check (does not leak tokens or paths)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

