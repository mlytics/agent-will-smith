# Agent Will Smith

AI Agent Platform built with Databricks vector search, LangChain, and FastAPI.

## 🎯 Overview

This platform provides a scalable foundation for deploying AI agents that leverage:
- **Databricks Vector Search** for semantic search capabilities
- **LangChain** for agent orchestration (v1 API, LangGraph-ready)
- **MLFlow** for prompt versioning and tracing
- **FastAPI** for HTTP API with observability

### Current Agents

**Product Recommendation Agent** - Analyzes articles and questions to recommend relevant products (activities and books) using semantic search and intent analysis.

## 📁 Project Structure

```
agent-will-smith/
├── app/                           # FastAPI application layer
│   ├── main.py                   # Application entry point
│   ├── middleware/               # Auth & observability
│   │   ├── auth.py              # Bearer token authentication
│   │   └── observability.py     # Structured logging & metrics
│   └── api/
│       ├── schemas.py           # API request/response models
│       └── routes.py            # HTTP endpoints (1 URL ↔ 1 agent)
│
├── agent/                        # Agent implementation
│   ├── product_recommendation_agent.py  # Main agent (flow controller)
│   ├── schemas.py               # Agent state & response schemas
│   └── scorers.py               # MLFlow evaluation scorers
│
├── core/                         # Framework-agnostic core library
│   ├── config.py                # Declarative configuration (Pydantic)
│   ├── logger.py                # Structured logging configuration
│   ├── tools/
│   │   └── vector_search.py    # Databricks vector search tools
│   ├── memory/
│   │   └── context_manager.py  # Memory funnel (single entry point)
│   └── prompts/
│       └── loader.py           # MLFlow prompt loading utilities
│
├── tests/                        # Test suite
│   ├── test_agent.py
│   ├── test_tools.py
│   └── test_api.py
│
├── Dockerfile                    # Production container configuration
├── docker-compose.yml           # Local development setup
├── pyproject.toml               # Dependencies & project metadata (PEP 621)
├── uv.lock                      # Dependency lock file (generated)
├── env.example                  # Environment variables template
└── README.md
```

## 🏗️ Architecture Principles

This codebase follows strict architectural guidelines for maintainability and future migration to LangGraph:

### **Domain Boundaries**
- **`agent/`**: Each agent is self-contained (1 HTTP URL ↔ 1 agent)
- **`core/tools/`**: Reusable, deterministic, single-purpose tools
- **`app/`**: HTTP layer, middleware, orchestration wiring

### **Key Design Decisions**

1. **Separation of Concerns**
   - Tools do work (vector search, data retrieval)
   - Prompts guide reasoning (loaded from MLFlow)
   - Orchestration decides sequence (agent runtime)

2. **Single Flow Controller**
   - Agent runtime in `product_recommendation_agent.py` decides next steps
   - No scattered if/else flow across modules
   - LangGraph-ready design for future migration

3. **Explicit State Schema**
   - All boundaries use typed schemas (Pydantic/dataclasses)
   - Tools return structured data, not English strings
   - No string boundaries pushing complexity into prompts

4. **Declarative Configuration**
   - All config in `app/config.py` (Pydantic Settings)
   - Environment variables for secrets/deployment-specific values
   - No scattered constants across codebase

## 🚀 Quick Start

### **Prerequisites**
- Python 3.12+
- Databricks workspace with:
  - Vector search endpoint
  - Activities and books indexes
  - LLM serving endpoint
  - MLFlow experiment

### **1. Clone & Setup**

```bash
cd agent-will-smith

# Copy environment template
cp env.example .env

# Edit .env with your Databricks credentials and endpoints
```

### **2. Create System Prompt in Databricks**

The agent requires a system prompt for intent analysis:

📖 **Full Guide:** See [`docs/PROMPT_SETUP.md`](docs/PROMPT_SETUP.md)

**Quick Steps:**
1. Go to Databricks UI → ML → Prompts → Create Prompt
2. Name: `aigc_uat.intent_engine.product_recommendation_prompt`
3. Copy content from the guide
4. Save and note the URI: `prompts://aigc_uat.intent_engine.product_recommendation_prompt/1`

### **3. Configure Environment Variables**

Edit `.env` with your settings:

```bash
# Databricks (REQUIRED)
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-personal-access-token  # For dev

# MLFlow (REQUIRED)
MLFLOW_EXPERIMENT_ID=your-experiment-id

# Vector Search (REQUIRED)
VECTOR_SEARCH_ENDPOINT=your-endpoint-name
ACTIVITIES_INDEX=aigc_uat.intent_engine.content_activity_gold_index
BOOKS_INDEX=aigc_uat.intent_engine.content_book_gold_index

# Prompt (REQUIRED - from step 2)
PROMPT_NAME=prompts:/aigc_uat.intent_engine.product_recommendation_prompt/1

# Authentication
API_KEY=your-secure-api-key-here
```

**Test the prompt loading:**
```bash
python -m scripts.test_prompt
```

### **4. Install Dependencies**

```bash
# Using uv (recommended - faster and more reliable)
uv sync

# Or using pip
pip install -e .
```

### **5. Run Locally**

```bash
# Using docker-compose (recommended)
docker-compose up

# Or run directly with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with uv
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **6. Test the API**

```bash
curl -X POST "http://localhost:8000/api/v1/recommend-products" \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "article": "This article discusses sustainable living practices and eco-friendly lifestyle choices for modern families.",
    "question": "What activities or books would help someone learn more about sustainable living?",
    "k": 5
  }'
```

## 📡 API Endpoints

### **POST /api/v1/recommend-products**
Recommend products based on article and question.

**Authentication:** Bearer token required

**Request Body:**
```json
{
  "article": "string (min 10 chars)",
  "question": "string (min 5 chars)",
  "k": 1-10,
  "product_types": ["activities", "books"] // optional filter
}
```

**Response:**
```json
{
  "products": [
    {
      "product_id": "string",
      "product_type": "activity" | "book",
      "title": "string",
      "description": "string | null",
      "relevance_score": 0.0-1.0,
      "reasoning": "string",
      "metadata": {}
    }
  ],
  "trace_id": "string",
  "processing_time_ms": 123.45
}
```

### **GET /health**
Health check endpoint for container orchestration.

### **GET /ready**
Readiness check endpoint.

### **GET /metrics**
System metrics (CPU, memory).

### **GET /docs**
Interactive API documentation (development only).

## 🐳 Docker Deployment

### **Local Development with Docker Compose**
```bash
# Start the application
docker-compose up

# Rebuild after dependency changes
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### **Production Docker Build**
```bash
# Build image
docker build -t agent-will-smith:latest .

# Run container
docker run -p 8000:8000 \
  --env-file .env \
  agent-will-smith:latest
```

### **For EKS Deployment**

See deployment manifests (to be added):
- `k8s/deployment.yaml` - Kubernetes deployment
- `k8s/service.yaml` - Service configuration
- `k8s/hpa.yaml` - Horizontal Pod Autoscaler
- `k8s/ingress.yaml` - Ingress configuration

## 🔍 Observability

### **Structured Logging**
All logs are JSON-formatted with trace IDs:

```json
{
  "event": "request_completed",
  "trace_id": "uuid",
  "method": "POST",
  "path": "/api/v1/recommend-products",
  "status_code": 200,
  "duration_ms": 234.56,
  "cpu_delta_percent": 5.2,
  "memory_mb": 128.5,
  "timestamp": "2025-12-12T10:30:00.123Z"
}
```

### **MLFlow Tracing**
Every agent invocation is traced in MLFlow with:
- LLM calls (model, tokens, latency)
- Tool calls (inputs, outputs, timing)
- Prompt versions used
- Application version (git commit)

### **Metrics Collection**
System metrics exposed at `/metrics`:
- CPU usage percentage
- Memory usage (MB and %)
- Per-request resource deltas

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov=agent --cov=core
```

## 📝 Adding New Agents

To add a new agent following the same patterns:

1. **Create agent module**: `agent/your_agent.py`
2. **Define schemas**: `agent/schemas.py` (add new state/response)
3. **Create tools** (if needed): `core/tools/your_tools.py`
4. **Add route**: `app/api/routes.py` (1 URL ↔ 1 agent)
5. **Register in MLFlow**: Create prompt in MLFlow registry

## 🔐 Security Considerations

- **API Key**: Use strong, random keys in production
- **Environment Variables**: Never commit `.env` to git
- **Container Security**: Non-root user in Docker (appuser:1000)
- **Rate Limiting**: Consider adding rate limiting middleware
- **Input Validation**: Pydantic validates all inputs

## 📚 Key Guidelines Followed

This codebase strictly adheres to these principles:

1. **Architecture boundaries**: Tools, orchestration, and prompts are separate
2. **Single flow controller**: Agent decides sequence, not tools/prompts
3. **Explicit state**: TypedDict/Pydantic models for all state
4. **Typed boundaries**: Schemas at every component boundary
5. **Small tools**: Single-purpose, deterministic tools
6. **Declarative config**: All configuration in one place
7. **Structured outputs**: Tools return dicts/models, not strings
8. **Explicit errors**: Clear error handling strategy
9. **Observability**: Log state, not vibes - structured logs everywhere
10. **LangChain v1**: Modern APIs for smooth LangGraph migration

## 🔄 Future Enhancements

- [ ] Add LangGraph support for complex workflows
- [ ] Implement caching layer for vector search
- [ ] Add rate limiting middleware
- [ ] Enhanced evaluation suite with MLFlow
- [ ] Kubernetes deployment manifests
- [ ] CI/CD pipeline configuration
- [ ] Advanced filtering (date ranges, categories)
- [ ] User preference persistence

## 📄 License

[Your License Here]

## 🤝 Contributing

[Contributing Guidelines]

---

**Built with ❤️ following best practices for production AI agents**

