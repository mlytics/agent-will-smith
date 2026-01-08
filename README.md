# Agent Will Smith

AI agent platform built with LangGraph, Databricks, and FastAPI. This platform provides a production-grade foundation for deploying stateful AI agents with semantic search capabilities.

## Overview

This platform combines:
- **LangGraph** - Stateful multi-agent workflows with explicit state machines
- **Databricks Vector Search** - Semantic search and retrieval
- **MLFlow** - Prompt versioning and tracing
- **FastAPI** - HTTP API with auto-generated documentation

For API documentation, run the application and visit `/docs` for interactive Swagger UI.

For detailed feature documentation, see the `docs/` directory.

## Architecture

The codebase follows these principles:

- **LangGraph StateGraph**: Explicit state machines with Pydantic-typed state
- **Strict Dependency Injection**: All dependencies passed explicitly (no hidden singletons)
- **Connection Pooling**: Expensive resources (LLM clients, vector search) created once at startup
- **Pydantic Everywhere**: Runtime validation at every boundary (state, API, database)
- **Fail-Fast Configuration**: Required config fields with no dangerous defaults

## Project Structure

```
agent-will-smith/
├── src/agent_will_smith/
│   ├── agent/              # Agent implementations
│   │   └── product_recommendation/
│   │       ├── agent.py
│   │       ├── config.py
│   │       ├── container.py
│   │       ├── model/      # Pydantic models
│   │       ├── node/       # LangGraph nodes
│   │       ├── repo/       # Data access layer
│   │       └── state.py
│   ├── app/                # FastAPI application
│   │   ├── api/            # API routers
│   │   └── middleware/
│   ├── core/               # Shared utilities
│   │   ├── config/
│   │   ├── logger.py
│   │   └── exceptions.py
│   └── infra/              # Infrastructure clients
│       ├── llm_client.py
│       ├── prompt_client.py
│       └── vector_search_client.py
├── docs/                   # Feature documentation
├── pyproject.toml
├── uv.lock
├── Dockerfile
└── docker-compose.yml
```

## Quick Start

### Prerequisites

**Required:**
- Python 3.14+
- [uv](https://github.com/astral-sh/uv) package manager (required - do not use pip)
- Databricks workspace with:
  - OAuth Service Principal (client ID + secret) or CLI profile configured
  - Vector search endpoint with configured indexes
  - LLM serving endpoint (Databricks Foundation Models or external)
  - MLFlow experiment for tracing
  - Prompt registered in MLFlow prompt registry

**Optional:**
- Docker & Docker Compose for containerized deployment

### 1. Setup

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup environment
cd agent-will-smith
cp .env.example .env
```

### 2. Configure

Edit `.env` with your Databricks credentials and endpoints. All variables use namespaced prefixes:
- `CORE_*` - Shared configuration (Databricks, MLFlow, FastAPI, logging)
- `AGENT_*` - Agent-specific configuration (prompts, LLM, vector search indexes)

**Critical environment variables to configure:**

**Databricks Authentication:**
```bash
CORE_DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
CORE_DATABRICKS_CLIENT_ID=your-oauth-client-id
CORE_DATABRICKS_CLIENT_SECRET=your-oauth-client-secret
```

**FastAPI:**
```bash
CORE_FASTAPI_VERSION=0.1.0
CORE_FASTAPI_API_KEY=your-secure-api-key
CORE_FASTAPI_ENABLE_DOCS=true  # Set to true to enable /docs endpoint
```

**MLFlow:**
```bash
CORE_MLFLOW_EXPERIMENT_ID=your-experiment-id
CORE_MLFLOW_ENABLE_TRACING=true
```

See `.env.example` for the complete list of required variables including agent-specific prompts, LLM endpoints, and vector search indexes.

### 3. Run

```bash
# Install dependencies
uv sync

# Run the application
uv run uvicorn agent_will_smith.main:app --reload --host 0.0.0.0 --port 8000

# Or using Docker
docker-compose up
```

Visit `http://localhost:8000/docs` for interactive API documentation (requires `CORE_FASTAPI_ENABLE_DOCS=true` in `.env`).

## Development

### Install Dependencies

```bash
# Using uv (required)
uv sync
```

### Docker

```bash
# Build
docker build -t agent-will-smith:latest .

# Run
docker run -p 8000:8000 --env-file .env agent-will-smith:latest
```

## Code Reviews

Before submitting pull requests, review your code against the guidelines in [`CODE_REVIEWS.md`](CODE_REVIEWS.md).

This document contains:
- Naming conventions and architectural patterns for this repository
- Best practices for dependency injection, error handling, and type safety
- Common pitfalls and edge cases to avoid

Use `CODE_REVIEWS.md` as a reference when:
- Writing new code or features
- Having AI assistants review your code
- Reviewing team members' pull requests

## Observability

All logs are JSON-formatted with trace IDs for request tracking. Enable MLFlow tracing with `CORE_MLFLOW_ENABLE_TRACING=true` to capture all LLM calls, vector searches, and prompt versions.
