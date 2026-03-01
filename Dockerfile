# =============================================================================
# Memory Layer — Production Dockerfile
# =============================================================================

FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# =============================================================================
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

RUN mkdir -p /app/db

ENV PORT=8000
ENV HOST=0.0.0.0
ENV DB_ROOT=./db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Install Node.js for dashboard build
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*
COPY dashboard/package*.json ./dashboard/
RUN cd dashboard && npm ci
COPY dashboard/ ./dashboard/
RUN cd dashboard && npm run build

CMD ["python", "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
