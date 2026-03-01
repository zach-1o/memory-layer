# =============================================================================
# Memory Layer — Combined Backend + Frontend Production Dockerfile
# =============================================================================
# Single container: serves both API and Dashboard
# =============================================================================

FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# =============================================================================
FROM python:3.12-slim AS backend-builder

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# Create DB directory
RUN mkdir -p /app/db

# =============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

COPY dashboard/package*.json ./
RUN npm ci

COPY dashboard/ ./
RUN npm run build

# =============================================================================
FROM python:3.12-slim AS production

WORKDIR /app

# Install nginx
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy Python from backend-builder
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY --from=backend-builder /app /app

# Copy frontend build
COPY --from=frontend-builder /app/dist /var/www/html

# Copy nginx config
COPY nginx.conf /etc/nginx/sites-available/default
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/ \
    && rm -f /etc/nginx/sites-enabled/default \
    && mkdir -p /run/nginx

# Environment variables
ENV PORT=8000
ENV HOST=0.0.0.0
ENV DB_ROOT=/app/db
ENV PYTHONPATH=/usr/local/lib/python3.12/site-packages:/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Start nginx and Python backend
CMD ["sh", "-c", "nginx & python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 & wait"]
