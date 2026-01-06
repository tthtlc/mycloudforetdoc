# Multi-stage build for Nutanix Collector Plugin

FROM python:3.9-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Build Python wheels
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# Final stage
FROM python:3.9-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 plugin

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels

# Install Python packages from wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY src/ /app/src/
COPY requirements.txt /app/

# Set permissions
RUN chown -R plugin:plugin /app

# Switch to non-root user
USER plugin

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV PLUGIN_PORT=50051

# gRPC port
EXPOSE 50051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:50051 || exit 1

# Start plugin
CMD ["python", "-u", "src/server.py"]
