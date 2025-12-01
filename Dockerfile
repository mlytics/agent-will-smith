FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files needed for dependency installation
COPY pyproject.toml ./
# Create minimal README.md (needed for pyproject.toml, will be overwritten if actual README.md exists)
RUN echo "# Agent-Will-Smith API Server" > README.md

# Install Python dependencies using uv
RUN uv pip install --system -e .

# Copy application code (this will overwrite README.md with actual one if it exists)
COPY . .

# Create cache directory
RUN mkdir -p /app/cache

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8888

# Run the application - use PORT env var or default to 8888
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8888}

