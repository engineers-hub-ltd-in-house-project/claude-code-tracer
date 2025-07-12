# Claude Code Tracer - Multi-stage Dockerfile

# === Base stage ===
FROM python:3.13-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# === Dependencies stage ===
FROM base AS dependencies

# Copy dependency files
COPY requirements.txt requirements-dev.txt ./

# Install production dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# === Development stage ===
FROM dependencies AS development

# Install development dependencies
RUN pip install -r requirements-dev.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data

# Expose ports
EXPOSE 8000 9090

# Set default command for development
CMD ["uvicorn", "claude_code_tracer.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# === Builder stage ===
FROM dependencies AS builder

# Copy application code
COPY . .

# Run any build steps (e.g., compile translations, minify assets)
# RUN python setup.py build

# === Production stage ===
FROM python:3.13-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash claude \
    && mkdir -p /app/logs /app/data \
    && chown -R claude:claude /app

# Set working directory
WORKDIR /app

# Copy dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application from builder stage
COPY --from=builder --chown=claude:claude /app/src ./src
COPY --from=builder --chown=claude:claude /app/scripts ./scripts

# Switch to non-root user
USER claude

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000

# Set production command
CMD ["gunicorn", "claude_code_tracer.api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]