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

WORKDIR /build

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

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
FROM ubuntu:22.04 AS production

WORKDIR /app

# Install nginx and Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY --from=backend-builder /app /app

# Copy frontend build
COPY --from=frontend-builder /app/dist /var/www/html

# Copy nginx config (serves both frontend and proxies API)
COPY nginx.conf /etc/nginx/sites-available/default

# Create symlink for nginx
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/ \
    && rm -f /etc/nginx/sites-enabled/default \
    && mkdir -p /run/nginx

# Environment
ENV PORT=8000
ENV HOST=0.0.0.0
ENV PYTHONPATH=/app

EXPOSE 8000 37777

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Start nginx (handles both frontend + API proxy)
CMD ["sh", "-c", "nginx & python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8000 & wait"]
