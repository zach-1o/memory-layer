# =============================================================================
# Memory Layer — Production Dockerfile (Single Container)
# =============================================================================
# Serves both frontend and backend using nginx
# =============================================================================

FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# =============================================================================
FROM python:3.12-slim AS backend

WORKDIR /app

# Copy Python packages
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app source
COPY . .

# Create DB directory
RUN mkdir -p /app/db

ENV DB_ROOT=/app/db
ENV PYTHONPATH=/usr/local/lib/python3.12/site-packages:/app

# =============================================================================
FROM node:20-alpine AS frontend

WORKDIR /app

COPY dashboard/package*.json ./
RUN npm ci

COPY dashboard/ ./
RUN npm run build

# =============================================================================
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx python3 python3-pip curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY --from=backend /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin
COPY --from=backend /app /app

# Copy frontend
COPY --from=frontend /app/dist /var/www/html

# Copy nginx config
COPY nginx.conf /etc/nginx/sites-available/default
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/ \
    && rm -f /etc/nginx/sites-enabled/default \
    && mkdir -p /run/nginx

ENV DB_ROOT=/app/db
ENV PYTHONPATH=/usr/local/lib/python3.12/site-packages:/app
ENV PORT=8001
ENV HOST=0.0.0.0

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Start nginx and backend
CMD sh -c "nginx & python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8001 & wait"
