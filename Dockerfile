# ========================================
# Stage 1: Builder
# ========================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install UV package manager (per https://docs.astral.sh/uv/guides/integration/docker/)
RUN pip install --no-cache-dir uv

# Keep the virtual environment path identical across stages
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Copy dependency files (cached if unchanged)
COPY pyproject.toml ./
COPY README.md ./

# Copy application source and tests
COPY src/ ./src/
COPY tests/ ./tests/

# Create venv and install project with dev extras using uv (doc: uv pip install --python <path>)
RUN uv venv "${VIRTUAL_ENV}" && \
    uv pip install --python "${VIRTUAL_ENV}/bin/python" --no-cache -e ".[dev]"

# Run tests and linting in builder stage
RUN pytest tests/ -q && \
    ruff check src/ && \
    black --check src/

# ========================================
# Stage 2: Runtime (Minimal)
# ========================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install curl for health checks (minimal)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy venv from builder (compiled dependencies, no build tools)
COPY --from=builder /app/.venv /app/.venv

# Copy application source (not tests, not tools)
COPY src/ ./src/
COPY pyproject.toml ./
COPY README.md ./

# Environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=info \
    LOG_FORMAT=json \
    PORT=8000

# Security: Run as non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check (allows Docker/k8s to detect failures)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port (documentation only; actual binding in CMD)
EXPOSE 8000

# Run FastAPI app with uvicorn
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
