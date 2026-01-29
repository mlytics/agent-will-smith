# Multi-stage Docker build for agent-will-smith
# Optimized for production deployment with uv

# Stage 1: Builder
FROM python:3.14-slim AS builder

WORKDIR /build

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and source code
COPY pyproject.toml uv.lock* README.md ./
COPY src/ ./src/

# Install dependencies using uv
# Note: uv.lock is optional - if not present, uv will resolve from pyproject.toml
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.14-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /build/.venv /app/.venv

# Copy application code
COPY src/ ./src/

# Copy prompts for fallback
COPY prompts/ ./prompts/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Run with uvicorn (using python -m to use the installed module)
CMD ["python", "-m", "uvicorn", "agent_will_smith.main:app", "--host", "0.0.0.0", "--port", "8000"]

