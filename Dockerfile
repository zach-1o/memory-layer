# =============================================================================
# Memory Layer — Production Dockerfile
# =============================================================================
# Multi-stage build: install deps in builder, copy to slim runtime image.
# Only production dependencies are installed (no test tools).
# =============================================================================

FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools needed for some packages (e.g. chromadb, cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install production requirements first (layer-cached)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# =============================================================================
FROM python:3.12-slim AS runtime
# =============================================================================

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# Create persistent data directory
RUN mkdir -p /app/db

# The port the application listens on (CreateOS routes to this)
ENV PORT=8000
ENV HOST=0.0.0.0

# Expose the port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Start the FastAPI server via uvicorn
CMD ["python", "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
