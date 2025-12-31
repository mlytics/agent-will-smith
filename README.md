# Agent Will Smith

AI Agent Platform built with LangGraph, Databricks vector search, and FastAPI.

## 🎯 Overview

This platform provides a scalable, production-grade foundation for deploying AI agents that leverage:
- **LangGraph** for stateful multi-agent workflows
- **Databricks Vector Search** for semantic search capabilities
- **MLFlow** for prompt versioning and tracing
- **FastAPI** for HTTP API with observability
- **Pydantic** for end-to-end type safety

### Current Agents

**Product Recommendation Agent** - Uses LangGraph StateGraph workflow to analyze articles and questions. The workflow consists of:
1. **Intent Analysis** - Single LLM call to extract user intent
2. **Parallel Search** - Concurrent vector searches across verticals (activities, books, articles) with 5s timeout per vertical
3. **Response Composition** - Deterministic aggregation of results grouped by vertical

**Key Features:**
- Multi-tenant support with `customer_uuid` filtering
- Parallel search execution with timeout handling
- Grouped results by vertical (top K per category)
- Connection pooling for vector search and LLM clients
- Strict dependency injection throughout
- Fail-fast error handling and configuration

## 📁 Project Structure

```
agent-will-smith/
├── app/                              # FastAPI application layer
│   ├── main.py                      # Application entry point & DI setup
│   ├── middleware/                  # Auth & observability
│   │   ├── auth.py                 # Bearer token authentication
│   │   └── observability.py        # Structured logging & metrics
│   └── gateway/                     # API gateway layer (project-based)
│       ├── dto/
│       │   └── schemas.py          # Shared API schemas
│       └── product_recommendation/ # Product recommendation API
│           ├── dto/
│           │   └── schemas.py      # Endpoint-specific schemas
│           └── routes.py           # HTTP endpoints (1 URL ↔ 1 agent)
│
├── agent/                           # Agent implementations
│   └── product_recommendation/     # Product recommendation agent
│       ├── agent.py                # Main agent entry point
│       ├── workflow.py             # LangGraph workflow composition
│       ├── constants.py            # Agent constants & types
│       ├── config/                 # Agent-specific configuration
│       │   └── settings.py        # Pydantic settings
│       ├── infra/                  # Infrastructure layer
│       │   ├── vector_search.py   # Vector search client & pooling
│       │   ├── llm_client.py      # LLM client & pooling
│       │   └── prompts.py         # MLFlow prompt loading & caching
│       ├── node/                   # LangGraph nodes
│       │   ├── intent_analysis.py # Intent extraction (LLM)
│       │   ├── parallel_search.py # Parallel vector search
│       │   ├── query_builder.py   # Search query construction
│       │   └── response_composer.py # Result aggregation
│       └── schemas/                # Type-safe schemas (Pydantic)
│           ├── state.py           # LangGraph state (AgentState)
│           ├── messages.py        # Node messages & outputs
│           └── database.py        # Vector search result DTOs
│
├── core/                            # Framework-agnostic core library
│   ├── config/                     # Configuration management
│   │   ├── common.py              # Common settings (Databricks, etc.)
│   │   └── fastapi.py             # FastAPI-specific settings
│   ├── logger.py                   # Structured logging configuration
│   └── exceptions.py               # Custom exception hierarchy
│
├── Dockerfile                       # Production container configuration
├── docker-compose.yml              # Local development setup
├── pyproject.toml                  # Dependencies & project metadata (PEP 621)
├── uv.lock                         # Dependency lock file (generated)
├── env.example                     # Environment variables template
└── README.md
```

## 🏗️ Architecture Principles

This codebase follows strict architectural guidelines for production-grade AI agents:

### **1. LangGraph Workflow Architecture**
- **StateGraph**: Explicit state machine with typed state (Pydantic)
- **Node-based**: Each step is an isolated, testable node
- **Deterministic flow**: Intent → Parallel Search → Compose
- **No multi-round reasoning**: Single LLM call for intent analysis

### **2. Strict Dependency Injection**
- **Explicit DI**: All dependencies passed as parameters (no hidden singletons)
- **Connection pooling**: Vector search and LLM clients created once at startup
- **Thread-safe singletons**: Double-checked locking for pool initialization
- **functools.partial**: Dependencies baked into LangGraph nodes
- **FastAPI Depends()**: Workflow injected into API routes

### **3. Pydantic Everywhere**
- **AgentState**: LangGraph state is a Pydantic BaseModel
- **Node messages**: All inputs/outputs between nodes are Pydantic models
- **API boundaries**: Request/response schemas validated by Pydantic
- **Database DTOs**: Vector search results parsed with Pydantic
- **Configuration**: All settings use Pydantic Settings

### **4. Fail-Fast Error Handling**
- **Layered exceptions**: Custom exception hierarchy in `core/exceptions.py`
- **Raise from inner layers**: Functions raise specific exceptions with context
- **Catch at outer layer**: Only API layer catches and maps to HTTP status
- **Stack trace preservation**: `raise ... from e` preserves line numbers
- **No silent failures**: Required config fields, no dangerous defaults

### **5. Multi-Tenant Design**
- **customer_uuid filtering**: Vector searches filtered at query time
- **Request-level isolation**: Each request includes customer context
- **No centralized validation**: Simple, performant filtering

### **6. Parallel Execution**
- **Concurrent searches**: All verticals searched in parallel with `asyncio.gather`
- **Timeout per vertical**: 5-second timeout prevents slow searches from blocking
- **Partial results**: Successful searches returned even if some fail
- **Error tracking**: Per-vertical error messages in response

### **Domain Boundaries**
- **`agent/product_recommendation/`**: Self-contained agent module
- **`agent/product_recommendation/infra/`**: Infrastructure (clients, data access)
- **`agent/product_recommendation/node/`**: LangGraph workflow nodes
- **`app/gateway/product_recommendation/`**: API layer for this agent
- **`core/`**: Shared utilities (config, logging, exceptions)

### **Key Design Decisions**

1. **Explicit State Management**
   - LangGraph state is typed Pydantic model
   - All state transitions explicit and traceable
   - No hidden state or globals

2. **Connection Pooling**
   - Vector search client: Singleton pool, thread-safe
   - LLM client: Singleton pool, thread-safe
   - Workflow: Compiled once, cached
   - Prompts: Loaded once, cached with @lru_cache

3. **Type Safety Throughout**
   - Every function input/output: Pydantic or primitive types
   - No untyped dicts crossing boundaries
   - Runtime validation at every layer

4. **Declarative Configuration**
   - All config in `core/config/` and `agent/*/config/`
   - Environment variables for secrets
   - Required fields enforced (fail-fast on missing config)

5. **Project-Based API Structure**
   - Each agent has its own API subdirectory
   - Agent-specific DTOs and routes co-located
   - Shared schemas in `app/gateway/dto/`

## 🚀 Quick Start

### **Prerequisites**
- Python 3.12+
- Databricks workspace with:
  - Vector search endpoint
  - Activities, books, and articles indexes
  - LLM serving endpoint (databricks-gpt-5-nano or similar)
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

**Quick Steps:**
1. Go to Databricks UI → ML → Prompts → Create Prompt
2. Name: `aigc_uat.intent_engine.product_recommendation_prompt`
3. Content: System prompt for intent extraction (refer to existing prompts in your workspace)
4. Save and note the URI: `prompts:/aigc_uat.intent_engine.product_recommendation_prompt/1`

### **3. Configure Environment Variables**

Edit `.env` with your settings:

```bash
# Databricks (REQUIRED - fail-fast if missing)
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-personal-access-token

# MLFlow (REQUIRED)
MLFLOW_EXPERIMENT_ID=your-experiment-id

# Vector Search (REQUIRED - no defaults)
VECTOR_SEARCH_ENDPOINT=your-endpoint-name
ACTIVITIES_INDEX=aigc_prod.intent_engine.content_activity_gold_index
BOOKS_INDEX=aigc_prod.intent_engine.content_book_gold_index
ARTICLES_INDEX=aigc_prod.intent_engine.content_article_gold_index

# Prompt (REQUIRED - no defaults)
PROMPT_NAME=prompts:/aigc_uat.intent_engine.product_recommendation_prompt/1

# LLM Configuration
LLM_ENDPOINT=databricks-gpt-5-nano
LLM_TEMPERATURE=1.0

# Authentication
API_KEY=your-secure-api-key-here
```

**Important:** All indices and prompts are required. The application will fail-fast at startup if any are missing (no dangerous defaults).

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

**Server Startup:**
The application initializes dependencies in order (從小組到大 - small to big):
1. Vector search client pool
2. LLM client pool  
3. Prompt cache
4. Workflow compilation (with dependencies injected)

### **6. Test the API**

```bash
curl -X POST "http://localhost:8000/api/v1/recommend-products" \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "article": "This article discusses sustainable living practices and eco-friendly lifestyle choices for modern families.",
    "question": "What activities or books would help someone learn more about sustainable living?",
    "k": 5,
    "product_types": ["activities", "books", "articles"],
    "customer_uuid": "0b8ecbe2-6097-4ca8-b61b-dfeb1578b011"
  }'
```

## 📡 API Endpoints

### **POST /api/v1/recommend-products**
Recommend products based on article and question using LangGraph workflow.

**Authentication:** Bearer token required

**Request Body:**
```json
{
  "article": "string (min 10 chars)",
  "question": "string (min 5 chars)",
  "k": 1-10,
  "product_types": ["activities", "books", "articles"],  // optional, defaults to all
  "customer_uuid": "uuid-string"  // required for multi-tenant filtering
}
```

**Response (Grouped by Vertical):**
```json
{
  "results_by_vertical": [
    {
      "vertical": "activities",
      "products": [
        {
          "product_id": "string",
          "product_type": "activity",
          "title": "string",
          "description": "string | null",
          "relevance_score": 0.0-1.0,
          "reasoning": "string",
          "metadata": {}
        }
      ],
      "error": null
    }
  ],
  "total_products": 15,
  "status": "complete" | "partial",
  "trace_id": "string",
  "processing_time_ms": 234.56
}
```

**Response Fields:**
- `results_by_vertical`: Array of results grouped by vertical (activities, books, articles)
- `total_products`: Total number of products across all verticals
- `status`: `"complete"` (all searches succeeded) or `"partial"` (some failed)
- `error`: Per-vertical error messages if searches failed

### **GET /health**
Health check endpoint for container orchestration.

### **GET /ready**
Readiness check endpoint.

### **GET /metrics**
System metrics (CPU, memory).

### **GET /docs**
Interactive API documentation (development only).

## 🔄 LangGraph Workflow

The product recommendation agent uses a deterministic LangGraph workflow:

```
┌─────────────────┐
│  HTTP Request   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Intent Analysis │ ← Single LLM call
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Parallel Search │ ← Concurrent vector searches (5s timeout each)
│  ├─ Activities  │
│  ├─ Books       │
│  └─ Articles    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Compose Response│ ← Aggregate & group results
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTTP Response  │ ← Grouped by vertical
└─────────────────┘
```

**Key Characteristics:**
- **Stateful**: Uses Pydantic `AgentState` for type-safe state management
- **Deterministic**: No LLM decides which tools to call (user specifies verticals)
- **Parallel**: All vector searches run concurrently
- **Timeout-protected**: 5-second timeout per vertical prevents hangs
- **Fail-safe**: Returns partial results if some searches fail

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
  "timestamp": "2025-12-31T10:30:00.123Z"
}
```

**Key Log Events:**
- `application_starting` - Server startup
- `vector_search_client_pooled` - Vector client initialized
- `llm_client_pooled` - LLM client initialized
- `workflow_with_dependencies_ready` - Workflow compiled
- `agent_started` - Request received
- `intent_analysis_started` - LLM call starting
- `parallel_search_started` - Vector searches launching
- `vertical_search_completed` - Individual search done
- `agent_completed` - Response ready

### **MLFlow Tracing**
Every agent invocation is traced in MLFlow with:
- LLM calls (model, tokens, latency)
- Vector search calls (index, query, results count)
- Prompt versions used
- Application version
- Full request/response

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

1. **Create agent module**: `agent/your_agent/`
   - `agent.py` - Main entry point
   - `workflow.py` - LangGraph workflow
   - `config/settings.py` - Agent-specific config
   - `node/` - LangGraph nodes
   - `schemas/` - Pydantic models
   - `infra/` - Infrastructure (clients, data access)

2. **Create API module**: `app/gateway/your_agent/`
   - `routes.py` - HTTP endpoints
   - `dto/schemas.py` - API request/response models

3. **Register workflow**: Update `app/main.py` lifespan to initialize your workflow

4. **Create prompt**: Register prompt in MLFlow

5. **Add route**: Include router in `app/main.py`

## 🔐 Security Considerations

- **API Key**: Use strong, random keys in production
- **Environment Variables**: Never commit `.env` to git
- **Container Security**: Non-root user in Docker (appuser:1000)
- **Rate Limiting**: Consider adding rate limiting middleware
- **Input Validation**: Pydantic validates all inputs at every boundary
- **Multi-tenant**: customer_uuid prevents cross-tenant data access

## 📚 Architecture Guidelines

This codebase strictly adheres to these principles:

1. **LangGraph StateGraph**: Explicit state machine with typed state
2. **Strict dependency injection**: All dependencies passed explicitly
3. **Connection pooling**: Expensive resources created once, reused
4. **Pydantic everywhere**: Runtime validation at every boundary
5. **Fail-fast**: Required config, no dangerous defaults
6. **Layered errors**: Raise from inner layers, catch at outer layer
7. **Thread-safe singletons**: Double-checked locking for pools
8. **Project-based structure**: Each agent is self-contained
9. **Type safety**: Explicit types, no untyped dicts
10. **Observability**: Structured logs with trace IDs everywhere

## 🔄 Migration from React Agent

This codebase was refactored from LangChain React Agent to LangGraph:

**What Changed:**
- ❌ React Agent → ✅ LangGraph StateGraph
- ❌ LLM decides tools → ✅ User specifies verticals
- ❌ Multi-round reasoning → ✅ Single LLM call (intent only)
- ❌ Hidden dependencies → ✅ Explicit dependency injection
- ❌ Scattered state → ✅ Pydantic AgentState
- ❌ TypedDict → ✅ Pydantic BaseModel
- ❌ Client per request → ✅ Connection pooling
- ❌ Optional config → ✅ Required config (fail-fast)

**Why LangGraph:**
- More predictable (deterministic flow)
- Better observability (explicit state)
- Higher performance (parallel execution)
- Easier to test (injectable dependencies)
- Production-ready (pooling, timeouts, error handling)

## 🚀 Future Enhancements

- [ ] Add more agents (follow project-based structure)
- [ ] Implement caching layer for vector search results
- [ ] Add rate limiting middleware
- [ ] Enhanced evaluation suite with MLFlow
- [ ] Kubernetes deployment manifests
- [ ] CI/CD pipeline configuration
- [ ] Advanced filtering (date ranges, categories)
- [ ] Retry mechanism for transient errors

## 📄 License

[Your License Here]

## 🤝 Contributing

[Contributing Guidelines]

---

**Built with ❤️ following production-grade practices for LangGraph agents**
