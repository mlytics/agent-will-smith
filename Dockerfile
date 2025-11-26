FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml ./

# Install Python dependencies using uv
RUN uv pip install --system -e .

# Copy application code
COPY . .

# Create cache directory
RUN mkdir -p /app/cache

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Run the application - use PORT env var or default to 8080
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}

