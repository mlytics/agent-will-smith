# 🔄 Project Handoff Document: Agent Will Smith

**Document Version**: 1.0  
**Date**: December 12, 2025  
**Status**: Phase 1 Complete (Scaffolding) - Ready for Phase 2 (Implementation)  
**Target Audience**: Next LLM Agent / Developer

**Note**: Project renamed from `product-recommendation-agent` to `agent-will-smith`

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Requirements (Functional & Non-Functional)](#requirements)
3. [Code Guidelines & Architecture Principles](#code-guidelines--architecture-principles)
4. [Technology Stack](#technology-stack)
5. [Project Structure & Component Details](#project-structure--component-details)
6. [Database Schemas (Vector Indexes)](#database-schemas-vector-indexes)
7. [Current Implementation Status](#current-implementation-status)
8. [Configuration Guide](#configuration-guide)
9. [What Works vs What Needs Implementation](#what-works-vs-what-needs-implementation)
10. [Next Steps (Phase 2)](#next-steps-phase-2)
11. [Testing Strategy](#testing-strategy)
12. [Deployment Strategy](#deployment-strategy)
13. [Critical Design Decisions](#critical-design-decisions)
14. [Common Pitfalls to Avoid](#common-pitfalls-to-avoid)
15. [Reference Implementation Patterns](#reference-implementation-patterns)

---

## 📊 Project Overview

### **Purpose**
An AI-powered product recommendation system that analyzes articles and questions to recommend relevant products (activities and books) using:
- Databricks Vector Search for semantic search
- LangChain for agent orchestration
- MLFlow for prompt management and tracing
- FastAPI for HTTP API

### **Core Flow**
```
User Request (Article + Question + K)
    ↓
FastAPI API Layer (/api/v1/recommend-products)
    ↓
Agent (product_recommendation_agent.py)
    ↓
Tools (search_activities, search_books)
    ↓
Databricks Vector Search (2 indexes: activities, books)
    ↓
Agent Reasoning (LLM + LangChain)
    ↓
Structured Response (Top K Products)
```

### **Key Constraint**
- **Max K**: 10 products
- **Vector Indexes**: 2 (activities_mock, books_mock)
- **Authentication**: Simple Bearer token (API key)
- **Future Target**: EKS deployment

---

## 🎯 Requirements

### **Functional Requirements**

#### **1. HTTP Endpoint**
**Endpoint**: `POST /api/v1/recommend-products`

**Input Schema**:
```json
{
  "article": "string (min 10 chars)",
  "question": "string (min 5 chars)",
  "k": 1-10,
  "product_types": ["activities", "books"] // optional filter
}
```

**Output Schema**:
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

#### **2. Agent Behavior**
- Analyze article content
- Understand the question context
- Search relevant products using vector search
- Reason about relevance using LLM
- Return top K most relevant products
- Provide reasoning for recommendations

### **Non-Functional Requirements**

#### **Scalability**
- ✅ **Auto-scaling**: Stateless design for horizontal scaling
- ✅ **Containerization**: Docker with multi-stage build
- 🔄 **EKS Ready**: Health/readiness endpoints implemented (deployment manifests pending)

#### **Authentication**
- ✅ **Bearer Token**: Simple API key authentication
- ⚠️ **Note**: Current implementation uses single API key (not production-grade)
- 🔄 **Future**: Consider JWT, OAuth2, or external auth service

#### **Observability**

**Logging**:
- ✅ Structured logs (JSON format)
- ✅ Error logs with exception traces
- ✅ All logs include trace_id for correlation
- ✅ Request/response logging with metrics

**Metrics**:
- ✅ CPU percentage per request
- ✅ Memory usage (MB, delta)
- ✅ Request duration (milliseconds)
- ✅ System metrics endpoint (`/metrics`)

**Tracing**:
- ✅ MLFlow LangChain autolog
- ✅ `@mlflow.trace` decorator on agent
- ✅ Tool call tracking
- ✅ LLM call tracking

---

## 🏗️ Code Guidelines & Architecture Principles

### **Critical Guideline: Architecture Boundaries**

**"Keep bricks separate from wiring"**

1. **Tools** = Bricks (capabilities)
   - Do work (vector search, data retrieval)
   - Return structured data (Pydantic/dicts)
   - No orchestration logic
   - No prompt logic
   - Example: `search_activities()`, `search_books()`

2. **Prompts** = Bricks (reasoning guides)
   - Guide style and heuristics
   - Say "use tools when uncertain", NOT "call A then B then C"
   - No exact sequencing
   - Loaded from MLFlow registry

3. **Orchestration** = Wiring (flow control)
   - Decides sequence of operations
   - Lives in agent runtime
   - Uses tools + prompts
   - Example: `product_recommendation_agent.py`

### **One Controller of Flow**

**MUST FOLLOW**: There should be a single place where the next step is decided.

- ✅ **Current**: Agent runtime in `product_recommendation_agent.py` decides flow
- ❌ **Don't**: Scatter if/else flow logic across modules
- ❌ **Don't**: Make tools decide what to do next
- ❌ **Don't**: Put multi-step sequencing in prompts

**In LangGraph** (future migration):
- Routers/conditional edges control flow
- Nodes are state transformers

### **Explicit State Schema**

**MUST FOLLOW**: Define state models explicitly (no dict sprawl)

- ✅ **Current**: `AgentContext`, `ProductResult`, `AgentResponse` in `agent/schemas.py`
- ✅ Uses dataclasses (LangChain/LangGraph compatible)
- ✅ All boundaries have typed schemas

**Why**: State sprawl is harder to fix later than tool sprawl

### **Typed Outputs at Every Boundary**

**MUST FOLLOW**: Where data crosses components, enforce a schema

```python
# ✅ GOOD: Structured output
@tool
def search_activities(...) -> list[dict]:
    return [{"product_id": "...", "title": "..."}]

# ❌ BAD: String output
@tool
def search_activities(...) -> str:
    return "Found activities: Activity 1, Activity 2..."
```

**Why**: Pure string boundaries push complexity into prompts and post-processing

### **Tool Quality Rules**

#### **1. Deterministic at Interface Level**
```python
# ✅ GOOD: Explicit args, explicit types, no hidden globals
@tool
def search_activities(query: str, runtime: ToolRuntime[AgentContext]) -> list[dict]:
    ...

# ❌ BAD: Hidden dependencies, unclear inputs
def search_activities():
    query = get_query_from_somewhere()  # Hidden dependency!
    ...
```

#### **2. Return Structured Data**
```python
# ✅ GOOD: Returns dict/Pydantic models
return [ProductResult(...) for result in results]

# ❌ BAD: Returns English prose
return "I found 3 activities: Activity A is about X, Activity B is about Y..."
```

#### **3. Small and Single-Purpose**
```python
# ✅ GOOD: Separate tools for separate jobs
search_activities()  # Only searches activities
search_books()       # Only searches books

# ❌ BAD: Mega-tool doing everything
search_and_filter_and_summarize_and_decide()  # Too much!
```

#### **4. Explicit Error Strategy**
```python
# ✅ GOOD: Handle errors, return typed errors or empty results
try:
    results = index.similarity_search(...)
    return results
except Exception as e:
    logger.error("search_failed", error=str(e))
    return []  # Let agent handle missing results

# ❌ BAD: Half-catch, unclear error handling
try:
    results = index.similarity_search(...)
except:
    pass  # What happens now?
```

### **Prompt Rules**

#### **1. Prompts Define Style, Not Algorithms**
```
✅ GOOD: "Use tools when uncertain about product details"
❌ BAD: "First call search_activities, then call search_books, then compare results..."
```

#### **2. One Job Per Prompt**
- Planning prompt = separate
- Answering prompt = separate
- Formatting prompt = separate

**Current**: Single prompt for recommendation (simple enough for now)

#### **3. Keep Business Rules Out of Prompts**
```python
# ✅ GOOD: Business rules in code
if k > settings.max_k_products:
    raise ValueError("Too many products requested")

# ❌ BAD: Business rules in prompt
"Never return more than 10 products because of company policy..."
```

### **Configuration Rules**

**MUST FOLLOW**: All configuration is declarative

- ✅ **Current**: `app/config.py` with Pydantic Settings
- ✅ All settings from environment variables
- ✅ No scattered constants across codebase

```python
# ✅ GOOD: Centralized config
from app.config import settings
endpoint = settings.llm_endpoint

# ❌ BAD: Scattered constants
LLM_ENDPOINT = "databricks-gpt-5-mini"  # In some random file
```

### **Observability Rules**

#### **"Log State, Not Vibes"**

```python
# ✅ GOOD: Structured, measurable state
logger.info(
    "request_completed",
    trace_id=trace_id,
    status_code=200,
    duration_ms=234.56,
    products_count=5
)

# ❌ BAD: Vague vibes
logger.info("Request went well!")
```

#### **Trace Tool Latency/Cost Separately**

- ✅ Tool calls: Log timing, inputs, outputs
- ✅ Model calls: MLFlow tracks tokens, cost, latency
- ✅ Separate metrics for each

### **Versioning Rules**

#### **LangChain v1 APIs**

**MUST USE**: Modern v1 APIs for LangGraph migration readiness

```python
# ✅ GOOD: v1 API (current)
from langchain.agents import create_agent
agent = create_agent(model=chat_model, tools=tools, ...)

# ❌ BAD: Deprecated APIs
from langchain.agents import initialize_agent  # DEPRECATED!
```

#### **Explicit Budgets**

**MUST SET**:
```python
config = {
    "recursion_limit": settings.max_agent_steps,  # Max steps
    # Add: max_tokens, max_wall_time, max_tool_calls
}
```

### **Domain Boundary Rules**

```
agent/               # Each agent = 1 purpose
  ├── product_recommendation_agent.py  # 1 HTTP URL ↔ 1 agent
  └── schemas.py     # Agent-specific state

core/tools/          # Reusable tool library
  └── vector_search.py  # Pure, deterministic tools

app/                 # HTTP wiring, middleware
  ├── api/routes.py  # 1 route per agent
  └── middleware/    # Auth, logging, metrics
```

**NEVER**:
- Put HTTP logic in agent files
- Put agent logic in tool files
- Put tool logic in prompt strings
- Mix boundaries

---

## 🛠️ Technology Stack

### **Core Framework**
| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | >=0.115.0 | HTTP API framework |
| `uvicorn` | >=0.32.0 | ASGI server |
| `python-multipart` | >=0.0.9 | Form data parsing |

### **LangChain & Databricks**
| Package | Version | Purpose |
|---------|---------|---------|
| `langchain` | >=1.1.0 | Agent framework |
| `langgraph` | >=1.0.4 | Future migration (not yet used) |
| `databricks-langchain` | >=0.11.0 | Databricks LLM integration |
| `databricks-sdk` | >=0.73.0 | Databricks API client |
| `databricks-vectorsearch` | >=0.40 | Vector search client |

### **MLFlow**
| Package | Version | Purpose |
|---------|---------|---------|
| `mlflow` | >=3.6.0 | Prompt versioning, tracing, evaluation |

### **Schema & Validation**
| Package | Version | Purpose |
|---------|---------|---------|
| `pydantic` | >=2.12.5 | Data validation |
| `pydantic-settings` | >=2.7.0 | Config management |

### **Auth & Security**
| Package | Version | Purpose |
|---------|---------|---------|
| `python-jose[cryptography]` | >=3.3.0 | JWT handling (for future) |

### **Observability**
| Package | Version | Purpose |
|---------|---------|---------|
| `structlog` | >=24.0.0 | Structured logging |
| `psutil` | >=6.0.0 | CPU/memory metrics |

### **Python Version**
- **Required**: Python 3.12+
- **Reason**: Modern type hints (`str | None`, etc.)

---

## 📁 Project Structure & Component Details

### **Complete Directory Tree**
```
agent-will-smith/
├── agent/                                    # Agent layer (orchestration)
│   ├── __init__.py                          # Exports recommend_products
│   ├── product_recommendation_agent.py      # Main agent (flow controller)
│   ├── schemas.py                           # AgentContext, ProductResult, AgentResponse
│   └── scorers.py                           # MLFlow evaluation scorers
│
├── app/                                      # HTTP/API layer
│   ├── __init__.py
│   ├── main.py                              # FastAPI app, lifespan, exception handlers
│   ├── config.py                            # Pydantic Settings (ALL configuration)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py                        # recommend_products_endpoint
│   │   └── schemas.py                       # Request/Response Pydantic models
│   └── middleware/
│       ├── __init__.py
│       ├── auth.py                          # Bearer token verification
│       └── observability.py                 # ObservabilityMiddleware, metrics
│
├── core/                                     # Reusable tool library
│   ├── __init__.py
│   ├── tools/
│   │   ├── __init__.py                      # Exports search_activities, search_books
│   │   └── vector_search.py                 # Databricks vector search tools
│   ├── memory/
│   │   ├── __init__.py
│   │   └── context_manager.py               # Future: memory funnel, chunking
│   └── prompts/
│       ├── __init__.py
│       └── loader.py                        # MLFlow prompt loading utilities
│
├── tests/
│   ├── __init__.py
│   └── test_api.py                          # FastAPI TestClient tests
│
├── Dockerfile                                # Multi-stage production build
├── .dockerignore                             # Build exclusions
├── .gitignore                                # Git exclusions
├── pyproject.toml                            # Dependencies + project metadata
├── requirements.txt                          # Generated from pyproject.toml
├── env.example                               # Environment variables template
├── README.md                                 # User-facing documentation
├── HANDOFF.md                                # This document
├── run_local.sh                              # Quick start script
└── test_api.sh                               # API testing script
```

### **Key File Deep Dives**

#### **`app/config.py`** (Declarative Configuration)
**Purpose**: Single source of truth for all configuration

**Key Settings**:
```python
class Settings(BaseSettings):
    # Databricks
    databricks_host: str               # Required
    databricks_client_id: str          # Required
    databricks_client_secret: str      # Required
    
    # MLFlow
    mlflow_experiment_id: str          # Required
    
    # Vector Search
    vector_search_endpoint: str        # Required
    activities_index: str              # Default: aigc_sit.default.activities_mock
    books_index: str                   # Default: aigc_sit.default.books_mock
    
    # LLM
    llm_endpoint: str                  # Default: databricks-gpt-5-mini
    llm_temperature: float             # Default: 0.7
    
    # Agent
    max_k_products: int                # Default: 10
    max_agent_steps: int               # Default: 10
    
    # Prompt
    prompt_name: str                   # MLFlow prompt path
```

**Environment Variables**: Loaded from `.env` or OS environment

#### **`agent/product_recommendation_agent.py`** (Flow Controller)
**Purpose**: Single orchestration point for product recommendations

**Pattern** (follows existing `weather_agent.py`):
```python
@mlflow.trace
def recommend_products(article, question, k, trace_id, product_types):
    # 1. Initialize LLM
    chat_model = ChatDatabricks(endpoint=settings.llm_endpoint)
    
    # 2. Initialize checkpointer
    checkpointer = InMemorySaver()
    
    # 3. Load prompt from MLFlow registry
    system_prompt = mlflow.genai.load_prompt(settings.prompt_name)
    
    # 4. Select tools based on product_types filter
    tools = [search_activities, search_books]  # Or filtered
    
    # 5. Create agent
    agent = create_agent(
        model=chat_model,
        system_prompt=system_prompt.format(),
        tools=tools,
        context_schema=AgentContext,
        response_format=ToolStrategy(AgentResponse),
        checkpointer=checkpointer,
    )
    
    # 6. Create context for tools
    context = AgentContext(trace_id, article, question, k, product_types)
    
    # 7. Invoke agent with budget
    config = {
        "configurable": {"thread_id": trace_id},
        "recursion_limit": settings.max_agent_steps
    }
    
    response = agent.invoke(
        {"messages": [{"role": "user", "content": user_message}]},
        config=config,
        context=context
    )
    
    # 8. Return structured response
    return response["structured_response"]
```

**Critical**: This is the ONLY place that decides:
- When to call tools
- Which tools to call
- How to combine results
- When to stop

#### **`core/tools/vector_search.py`** (Deterministic Tools)
**Purpose**: Pure functions for vector search

**Pattern**:
```python
@tool
def search_activities(query: str, runtime: ToolRuntime[AgentContext]) -> list[dict]:
    """Search activities vector index.
    
    Args:
        query: Search query text
        runtime: Tool runtime with context (trace_id, article, question, max_k)
    
    Returns:
        List of dicts (NOT English strings)
    """
    # 1. Create client
    client = VectorSearchClient(disable_notice=True)
    
    # 2. Get context
    context = runtime.context
    
    # 3. Execute search (pure function)
    results = _search_vector_index(
        client=client,
        index_name=settings.activities_index,
        query_text=query,
        num_results=context.max_k,
        product_type="activity"
    )
    
    # 4. Return structured data
    return [result.to_dict() for result in results]
```

**Key Points**:
- No orchestration logic (doesn't decide what to do next)
- Returns structured data (dicts/Pydantic)
- Access to context via `ToolRuntime`
- Error handling returns empty list (agent decides what to do)

#### **`app/api/routes.py`** (HTTP → Agent Mapping)
**Purpose**: 1 URL ↔ 1 agent function

**Pattern**:
```python
@router.post("/recommend-products")
async def recommend_products_endpoint(
    request: Request,
    body: RecommendProductsRequest,
    api_key: Annotated[str, Depends(verify_api_key)]
) -> RecommendProductsResponse:
    """HTTP endpoint wrapping agent invocation."""
    
    # 1. Get trace_id from middleware
    trace_id = request.state.trace_id
    
    # 2. Invoke agent (single call, no HTTP logic in agent)
    agent_response = recommend_products(
        article=body.article,
        question=body.question,
        k=body.k,
        trace_id=trace_id,
        product_types=body.product_types
    )
    
    # 3. Transform agent response → API response
    return RecommendProductsResponse(
        products=[...],
        trace_id=trace_id,
        processing_time_ms=...
    )
```

**Key Points**:
- Dependency injection for auth
- Thin wrapper around agent
- No business logic (that's in agent)
- Transforms schemas (API ↔ Agent)

#### **`app/middleware/observability.py`** (Structured Logging)
**Purpose**: Automatic request/response logging with metrics

**What It Does**:
```python
class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 1. Generate trace_id
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        
        # 2. Capture start metrics
        start_time, start_cpu, start_memory = ...
        
        # 3. Log request start
        logger.info("request_started", trace_id=trace_id, ...)
        
        # 4. Process request
        response = await call_next(request)
        
        # 5. Calculate metrics
        duration_ms, cpu_delta, memory_delta = ...
        
        # 6. Log request completed
        logger.info("request_completed", 
                   trace_id=trace_id,
                   duration_ms=duration_ms,
                   cpu_delta=cpu_delta,
                   ...)
        
        # 7. Add trace_id to response header
        response.headers["X-Trace-ID"] = trace_id
        
        return response
```

**Output Format** (JSON):
```json
{
  "event": "request_completed",
  "trace_id": "abc-123-def",
  "method": "POST",
  "path": "/api/v1/recommend-products",
  "status_code": 200,
  "duration_ms": 234.56,
  "cpu_delta_percent": 5.2,
  "memory_mb": 128.5,
  "memory_delta_mb": 2.3,
  "timestamp": "2025-12-12T10:30:00Z"
}
```

---

## 🗄️ Database Schemas (Vector Indexes)

### **Activities Index** (`aigc_sit.default.activities_mock`)

**Table Structure**:
| Column | Type | Description |
|--------|------|-------------|
| `event_id` | string | **Primary Key** - Unique event identifier from GVM API |
| `title` | string | Activity/event title |
| `description` | string | Full activity/event description (embedded) |
| `category` | string | Activity category (e.g., 實體, 線上) |
| `location_name` | string | Location name where activity takes place |
| `location_address` | string | Location address |
| `organizer` | string | Activity organizer |
| `channel` | string | Channel identifier |
| `start_time` | timestamp | Activity start time |
| `end_time` | timestamp | Activity end time |
| `timezone` | string | Timezone for the activity |
| `cover_image` | string | URL of cover image |
| `permalink` | string | Permanent URL to the activity |
| `last_updated` | timestamp | Last updated time of activity |
| `processed_at` | timestamp | Time when record was processed into silver layer |

**Vector Search Configuration**:
- **Embedding Source**: Compute embeddings from `description` field
- **Embedding Model**: `databricks-gte-large-en`
- **Primary Key**: `event_id`
- **Sync Mode**: Triggered

### **Books Index** (`aigc_sit.default.books_mock`)

**Table Structure**:
| Column | Type | Description |
|--------|------|-------------|
| `item_id` | string | **Primary Key** - Unique book item identifier from GVM API |
| `title_main` | string | Main book title |
| `title_subtitle` | string | Book subtitle |
| `title_original` | string | Original title (if translated) |
| `description` | string | Full book description (embedded) |
| `introduction` | string | Book introduction/preview |
| `excerpt_toc` | string | Table of contents |
| `excerpt_preface` | string | Book preface |
| `excerpt_recommendations` | string | Recommendations and endorsements |
| `author` | array(string) | List of book authors |
| `author_bio` | string | Author biography |
| `translator` | array(string) | List of translators |
| `publisher` | string | Publisher name |
| `cover_image` | string | URL of book cover image |
| `subject` | array(string) | Book subjects/topics |
| `articles` | array(complex) | Related articles (nested structure) |
| `prices` | array(complex) | Book pricing information (nested structure) |
| `permalink` | string | Permanent URL to the book |
| `publish_time` | timestamp | Book publication time |
| `last_updated` | timestamp | Last updated time of book |

**Nested Structures**:

**`articles` Array Items**:
```python
{
    "article_id": "string",
    "title": "string",
    "author": ["string"],
    "publish_time": "string",
    "thumbnail_url": "string",
    "content": "string",
    "permalink": "string",
    "tags": ["string"],
    "last_updated": "string",
    "content_status": "string"
}
```

**`prices` Array Items**:
```python
{
    "format": "string",
    "currency": "string",
    "list_price": bigint,
    "sale_price": bigint,
    "availability": "string"
}
```

**Vector Search Configuration**:
- **Embedding Source**: Compute embeddings from `description` field
- **Embedding Model**: `databricks-gte-large-en`
- **Primary Key**: `item_id`
- **Sync Mode**: Triggered

### **Vector Search Queries**

**Current Implementation** (`core/tools/vector_search.py`):
```python
results = index.similarity_search(
    query_text=query,  # User's combined article + question
    columns=[
        "title",
        "description",
        "category",      # Activities only
        "location_name", # Activities only
        "organizer",     # Activities only
        "author",        # Books only
        "publisher",     # Books only
    ],
    num_results=num_results
)
```

**Result Fields**:
- `score`: Relevance score (0.0-1.0)
- All requested columns
- Additional metadata from index

---

## ✅ Current Implementation Status

### **Phase 1: Scaffolding - COMPLETE** ✅

#### **What's Implemented**

| Component | Status | Details |
|-----------|--------|---------|
| **Directory Structure** | ✅ Complete | All folders created with proper separation |
| **Configuration** | ✅ Complete | Pydantic Settings with all required fields |
| **FastAPI App** | ✅ Complete | Main app, lifespan, exception handling |
| **API Schemas** | ✅ Complete | Request/Response Pydantic models |
| **API Routes** | ✅ Complete | `/api/v1/recommend-products` endpoint |
| **Authentication** | ✅ Complete | Bearer token middleware |
| **Observability** | ✅ Complete | Structured logging, metrics, trace IDs |
| **Agent Structure** | ✅ Complete | Agent function following LangChain v1 pattern |
| **Tools** | ✅ Complete | `search_activities`, `search_books` |
| **Schemas** | ✅ Complete | AgentContext, ProductResult, AgentResponse |
| **Scorers** | ✅ Complete | MLFlow evaluation functions |
| **Docker** | ✅ Complete | Multi-stage Dockerfile, .dockerignore |
| **Documentation** | ✅ Complete | README, HANDOFF, comments |
| **Scripts** | ✅ Complete | run_local.sh, test_api.sh |
| **Tests** | ✅ Partial | Basic API tests (need more coverage) |

#### **Code Quality**
- ✅ All files have docstrings
- ✅ Type hints everywhere
- ✅ Follows all architectural guidelines
- ✅ LangChain v1 APIs used
- ✅ MLFlow integration patterns
- ✅ Structured logging throughout

---

## ⚠️ What Works vs What Needs Implementation

### **What Works (Can Run Locally)**

#### ✅ **HTTP Layer**
- FastAPI server starts successfully
- Health checks (`/health`, `/ready`, `/metrics`)
- API documentation (`/docs`)
- Middleware (auth, observability)
- Exception handling

#### ✅ **Configuration**
- Environment variable loading
- Pydantic validation
- Settings accessed via `settings` singleton

#### ✅ **Code Structure**
- All imports work
- No circular dependencies
- Proper module boundaries

### **What Needs Implementation (Won't Work Yet)**

#### 🔄 **MLFlow Prompt** (REQUIRED)
**Problem**: Prompt doesn't exist in registry yet

**Location**: `agent/product_recommendation_agent.py` line 69
```python
system_prompt = mlflow.genai.load_prompt(settings.prompt_name)
```

**Current Setting**: `prompts:/aigc_sit.intent_engine.product_recommendation_prompt/1`

**Action Required**:
1. Create prompt in MLFlow registry at specified path
2. Or update `settings.prompt_name` to existing prompt
3. Or temporarily comment out and use hardcoded prompt for testing

**Example Prompt Structure** (needs to be created):
```
You are a helpful product recommendation assistant.

Given an article and a question, recommend the most relevant products (activities or books).

Use the available search tools to find products:
- search_activities: Find relevant events and activities
- search_books: Find relevant books and publications

Analyze the article content carefully and match it with the question to provide thoughtful recommendations.

Return your recommendations in the structured format provided.
```

#### 🔄 **Vector Search Indexes** (REQUIRED)
**Problem**: Indexes not yet created in Databricks

**Expected Indexes**:
- `aigc_sit.default.activities_mock`
- `aigc_sit.default.books_mock`

**Action Required**:
1. Create both indexes in Databricks
2. Populate with data (see schemas above)
3. Enable embeddings (compute from `description` field)
4. Deploy to vector search endpoint
5. Update `settings.vector_search_endpoint` with endpoint name

**Without These**: Tools will fail when agent tries to search

#### 🔄 **Vector Search Endpoint** (REQUIRED)
**Problem**: Endpoint doesn't exist yet

**Current Setting**: `VECTOR_SEARCH_ENDPOINT=your-endpoint-name`

**Action Required**:
1. Create vector search endpoint in Databricks
2. Deploy both indexes to endpoint
3. Update `.env` with actual endpoint name

#### 🔄 **Application Version Tracking** (OPTIONAL)
**Pattern from Existing Code** (`main.py` from weather agent):
```python
def enable_version_tracking():
    git_commit = get_git_commit(".")
    git_branch = get_git_branch(".")
    
    if not git_commit or not git_branch:
        raise ValueError("Not in a git repository")
    
    git_commit = git_commit[:8]
    version_name = f"{git_branch}-{git_commit}"
    
    active_model_info = mlflow.set_active_model(name=version_name)
    
    app_params = {"developer": "Your Name", "type": "production"}
    mlflow.log_model_params(model_id=active_model_info.model_id, params=app_params)
```

**Action Required**:
1. Add `enable_version_tracking()` to `app/main.py` lifespan
2. Ensure code is in git repository
3. Configure developer name and type

---

## 🔧 Configuration Guide

### **Required Environment Variables**

**Databricks (REQUIRED)**:
```bash
DATABRICKS_HOST=https://dbc-xxxxx.cloud.databricks.com
DATABRICKS_CLIENT_ID=your-client-id
DATABRICKS_CLIENT_SECRET=your-client-secret
```

**MLFlow (REQUIRED)**:
```bash
MLFLOW_TRACKING_URI=databricks
MLFLOW_REGISTRY_URI=databricks-uc
MLFLOW_EXPERIMENT_ID=your-experiment-id  # Get from Databricks
```

**Vector Search (REQUIRED)**:
```bash
VECTOR_SEARCH_ENDPOINT=your-endpoint-name
ACTIVITIES_INDEX=aigc_sit.default.activities_mock
BOOKS_INDEX=aigc_sit.default.books_mock
```

**Authentication (REQUIRED)**:
```bash
API_KEY=your-secure-random-api-key-here
```

**Prompt Management (REQUIRED)**:
```bash
PROMPT_NAME=prompts:/aigc_sit.intent_engine.product_recommendation_prompt/1
```

### **Optional Configuration**

**LLM Settings**:
```bash
LLM_ENDPOINT=databricks-gpt-5-mini  # Default
LLM_TEMPERATURE=0.7                 # 0.0-2.0
LLM_MAX_TOKENS=                     # None = no limit
```

**Agent Settings**:
```bash
MAX_K_PRODUCTS=10        # Max products to return
MAX_AGENT_STEPS=10       # Max reasoning steps
AGENT_TIMEOUT_SECONDS=60 # Execution timeout
```

**Application Settings**:
```bash
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
HOST=0.0.0.0
PORT=8000
RELOAD=true             # Auto-reload in dev
```

### **Configuration Priority**
1. Environment variables (highest priority)
2. `.env` file
3. Default values in `app/config.py`

---

## 🚀 Next Steps (Phase 2)

### **Priority 1: Make It Runnable** (Critical Path)

#### **1. Create MLFlow Prompt**
**File**: In Databricks MLFlow UI

**Steps**:
1. Navigate to MLFlow Model Registry
2. Create new prompt: `product_recommendation_prompt`
3. Set catalog: `aigc_sit.intent_engine`
4. Add prompt content (see example below)
5. Create version 1
6. Update `.env` if path differs

**Suggested Prompt Content**:
```
You are a product recommendation assistant specializing in activities and books.

Your task is to analyze an article and a question, then recommend the most relevant products.

Available Tools:
- search_activities: Find relevant events, workshops, and activities
- search_books: Find relevant books, publications, and reading materials

Instructions:
1. Carefully read and understand the article content
2. Consider the specific question being asked
3. Use the search tools to find relevant products
4. Select the most relevant products based on:
   - Relevance to article topic
   - Alignment with the question
   - Quality and diversity of recommendations
5. Provide clear reasoning for your selections

Return your recommendations using the structured response format.
Be concise but informative in your reasoning.
```

#### **2. Create Vector Search Indexes**
**Location**: Databricks UI → Catalog → Create Vector Search Index

**For Activities Index**:
```sql
-- 1. Ensure source table exists with schema shown in Database Schemas section
-- 2. Create vector search index
-- UI Configuration:
Index Name: activities_mock
Catalog: aigc_sit
Schema: default
Source Table: activities_mock (must exist)
Primary Key: event_id
Embedding Source Column: description
Embedding Model: databricks-gte-large-en
Sync Mode: Triggered
```

**For Books Index**:
```sql
-- Same process as activities
Index Name: books_mock
Catalog: aigc_sit
Schema: default
Source Table: books_mock (must exist)
Primary Key: item_id
Embedding Source Column: description
Embedding Model: databricks-gte-large-en
Sync Mode: Triggered
```

#### **3. Create/Configure Vector Search Endpoint**
**Location**: Databricks UI → Compute → Vector Search Endpoints

**Steps**:
1. Create new endpoint (or use existing)
2. Name it (e.g., `product-search-endpoint`)
3. Deploy both indexes to this endpoint
4. Wait for deployment (can take 5-10 minutes)
5. Update `.env` with endpoint name

#### **4. Update `.env` and Test**
```bash
# Update these with actual values
DATABRICKS_HOST=https://your-actual-workspace.cloud.databricks.com
DATABRICKS_CLIENT_ID=actual-client-id
DATABRICKS_CLIENT_SECRET=actual-secret
MLFLOW_EXPERIMENT_ID=actual-experiment-id
VECTOR_SEARCH_ENDPOINT=actual-endpoint-name
API_KEY=generate-secure-random-key

# Test locally
./run_local.sh

# In another terminal
./test_api.sh
```

### **Priority 2: Add Version Tracking**

**File**: `app/main.py`

**Add to lifespan function**:
```python
from mlflow.utils.git_utils import get_git_commit, get_git_branch

def enable_version_tracking():
    """Enable MLFlow version tracking with git info."""
    try:
        git_commit = get_git_commit(".")
        git_branch = get_git_branch(".")
        
        if not git_commit or not git_branch:
            logger.warning("not_in_git_repo", msg="Version tracking disabled")
            return
        
        git_commit = git_commit[:8]
        version_name = f"{git_branch}-{git_commit}"
        
        active_model_info = mlflow.set_active_model(name=version_name)
        
        app_params = {
            "developer": "Your Name",  # Update this
            "type": "development",     # Update per environment
            "endpoint": "/api/v1/recommend-products"
        }
        mlflow.log_model_params(
            model_id=active_model_info.model_id,
            params=app_params
        )
        
        logger.info("version_tracking_enabled", 
                   version=version_name,
                   model_id=active_model_info.model_id)
    
    except Exception as e:
        logger.warning("version_tracking_failed", error=str(e))

# In lifespan function:
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("application_starting", ...)
    
    configure_databricks()
    configure_mlflow()
    enable_version_tracking()  # ADD THIS
    
    logger.info("application_ready", ...)
    yield
    # Shutdown
    logger.info("application_shutting_down")
```

### **Priority 3: Enhanced Testing**

#### **Add Tool Tests**
**File**: `tests/test_tools.py` (create new)

```python
"""Tests for vector search tools."""

import pytest
from unittest.mock import Mock, patch
from core.tools.vector_search import search_activities, search_books

def test_search_activities_returns_structured_data():
    """Test that search_activities returns list of dicts."""
    # Mock runtime and context
    mock_runtime = Mock()
    mock_runtime.context.trace_id = "test-123"
    mock_runtime.context.max_k = 5
    
    # Mock vector search client
    with patch('core.tools.vector_search.VectorSearchClient'):
        results = search_activities("test query", mock_runtime)
        
        assert isinstance(results, list)
        if results:  # If not empty
            assert isinstance(results[0], dict)
            assert "product_id" in results[0]
            assert "title" in results[0]

# Add more tests...
```

#### **Add Agent Tests**
**File**: `tests/test_agent.py` (create new)

```python
"""Tests for product recommendation agent."""

import pytest
from unittest.mock import Mock, patch
from agent.product_recommendation_agent import recommend_products

def test_agent_returns_structured_response():
    """Test that agent returns AgentResponse."""
    # Mock dependencies
    with patch('agent.product_recommendation_agent.ChatDatabricks'), \
         patch('agent.product_recommendation_agent.mlflow.genai.load_prompt'), \
         patch('agent.product_recommendation_agent.create_agent'):
        
        response = recommend_products(
            article="Test article",
            question="Test question?",
            k=5,
            trace_id="test-123"
        )
        
        # Should return AgentResponse with structure
        assert hasattr(response, 'products')
        assert hasattr(response, 'reasoning')
        assert hasattr(response, 'total_searched')

# Add more tests...
```

### **Priority 4: Production Readiness**

#### **Add Rate Limiting**
**File**: `app/middleware/rate_limit.py` (create new)

```python
"""Rate limiting middleware."""

from fastapi import Request, HTTPException
from collections import defaultdict
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def __call__(self, request: Request):
        """Check rate limit for client."""
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.now()
        
        # Clean old requests
        cutoff = now - timedelta(minutes=1)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning("rate_limit_exceeded", client_ip=client_ip)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later."
            )
        
        # Add current request
        self.requests[client_ip].append(now)
```

**Add to `app/main.py`**:
```python
from app.middleware.rate_limit import RateLimiter

# Add middleware
app.add_middleware(RateLimiter(requests_per_minute=60))
```

#### **Add Health Check for Dependencies**
**File**: `app/main.py` - update `/ready` endpoint

```python
@app.get("/ready", response_model=HealthCheckResponse)
async def readiness_check():
    """Enhanced readiness check with dependency verification."""
    
    checks = {
        "databricks": False,
        "vector_search": False,
        "mlflow": False
    }
    
    try:
        # Check Databricks connectivity
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        w.current_user.me()  # Simple API call
        checks["databricks"] = True
    except:
        pass
    
    try:
        # Check vector search endpoint
        from databricks.vector_search.client import VectorSearchClient
        client = VectorSearchClient()
        client.get_endpoint(settings.vector_search_endpoint)
        checks["vector_search"] = True
    except:
        pass
    
    try:
        # Check MLFlow
        import mlflow
        mlflow.get_experiment(settings.mlflow_experiment_id)
        checks["mlflow"] = True
    except:
        pass
    
    # Determine overall status
    status = "healthy" if all(checks.values()) else "unhealthy"
    
    if status == "unhealthy":
        logger.warning("readiness_check_failed", checks=checks)
    
    return HealthCheckResponse(
        status=status,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
        # Add checks to response if needed
    )
```

### **Priority 5: EKS Deployment Preparation**

#### **Create Kubernetes Manifests**
**Directory**: `k8s/` (create new)

**File**: `k8s/deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-will-smith
  labels:
    app: agent-will-smith
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-will-smith
  template:
    metadata:
      labels:
        app: agent-will-smith
    spec:
      containers:
      - name: api
        image: your-ecr-repo/agent-will-smith:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABRICKS_HOST
          valueFrom:
            secretKeyRef:
              name: databricks-credentials
              key: host
        - name: DATABRICKS_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: databricks-credentials
              key: client_id
        - name: DATABRICKS_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: databricks-credentials
              key: client_secret
        # Add other env vars from configmap/secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

**File**: `k8s/service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: agent-will-smith
spec:
  selector:
    app: agent-will-smith
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

**File**: `k8s/hpa.yaml`
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-will-smith-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-will-smith
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 🧪 Testing Strategy

### **Test Pyramid**

```
         /\
        /  \  E2E Tests (few)
       /----\
      / Integ\ Integration Tests (some)
     /--------\
    /  Unit    \ Unit Tests (many)
   /------------\
```

### **Unit Tests** (Priority)

**What to Test**:
- Tool functions (`search_activities`, `search_books`)
- Schema validation (Pydantic models)
- Configuration loading
- Utility functions

**Example**:
```python
def test_config_validation():
    """Test that invalid config raises validation error."""
    with pytest.raises(ValidationError):
        Settings(max_k_products=100)  # Exceeds limit
```

### **Integration Tests** (Medium Priority)

**What to Test**:
- API endpoints with mocked agent
- Middleware (auth, observability)
- Error handling

**Example** (already in `tests/test_api.py`):
```python
@patch("app.api.routes.recommend_products")
def test_recommend_products_success(mock_recommend, mock_agent_response):
    mock_recommend.return_value = mock_agent_response
    response = client.post("/api/v1/recommend-products", ...)
    assert response.status_code == 200
```

### **E2E Tests** (Low Priority for Now)

**What to Test**:
- Full flow with real Databricks
- Real vector search
- Real LLM calls
- MLFlow tracing

**Note**: These are expensive and slow. Use sparingly.

### **Test Data**

**Create**: `tests/fixtures.py`
```python
"""Test fixtures and mock data."""

import pytest
from agent.schemas import ProductResult, AgentResponse

@pytest.fixture
def mock_activity():
    """Mock activity product."""
    return ProductResult(
        product_id="activity-123",
        product_type="activity",
        title="Sustainability Workshop",
        description="Learn about eco-friendly living",
        relevance_score=0.95,
        metadata={"location_name": "Green Center"}
    )

@pytest.fixture
def mock_agent_response(mock_activity):
    """Mock agent response."""
    return AgentResponse(
        products=[mock_activity],
        reasoning="Selected based on sustainability topic",
        total_searched=5
    )
```

---

## 🚢 Deployment Strategy

### **Local Development**
```bash
./run_local.sh  # Uses venv, installs deps, runs server
```

### **Docker (Staging)**
```bash
# Build
docker build -t agent-will-smith:v0.1.0 .

# Run
docker run -p 8000:8000 --env-file .env agent-will-smith:v0.1.0

# Test
curl http://localhost:8000/health
```

### **EKS (Production)**

**Steps**:
1. **Push to ECR**:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag agent-will-smith:v0.1.0 <account-id>.dkr.ecr.us-east-1.amazonaws.com/agent-will-smith:v0.1.0
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/agent-will-smith:v0.1.0
```

2. **Create Secrets**:
```bash
kubectl create secret generic databricks-credentials \
  --from-literal=host=https://... \
  --from-literal=client_id=... \
  --from-literal=client_secret=...
```

3. **Deploy**:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml  # If using ingress
```

4. **Monitor**:
```bash
kubectl logs -f deployment/agent-will-smith
kubectl get hpa agent-will-smith-hpa
```

### **CI/CD Pipeline** (Future)

**Suggested Flow**:
```
git push → GitHub Actions
  ↓
Run tests (pytest)
  ↓
Build Docker image
  ↓
Push to ECR
  ↓
Update EKS deployment
  ↓
Run smoke tests
```

---

## 🎯 Critical Design Decisions

### **Decision 1: LangChain v1 (Not v2/LangGraph Yet)**

**Why**: 
- v1 is stable and well-documented
- Easier migration path to LangGraph than v0
- `create_agent()` API is forward-compatible
- Can upgrade to LangGraph when flow becomes complex (branching, loops)

**When to Migrate to LangGraph**:
- Need conditional routing (if/else flow)
- Need loops/cycles in agent flow
- Need human-in-the-loop
- Need complex state management beyond messages

### **Decision 2: InMemorySaver (Not Persistent Checkpointer)**

**Why**:
- Simpler for initial implementation
- No external dependencies (Redis, DB)
- Stateless API (each request independent)

**When to Upgrade**:
- Need conversation history across requests
- Need to resume interrupted agent runs
- Need to replay/debug specific runs

**How to Upgrade**:
```python
# Replace InMemorySaver with:
from langgraph.checkpoint.postgres import PostgresCheckpointer
checkpointer = PostgresCheckpointer(conn_string="...")

# Or Redis:
from langgraph.checkpoint.redis import RedisCheckpointer
checkpointer = RedisCheckpointer(redis_url="...")
```

### **Decision 3: Dataclasses (Not Pydantic for Agent State)**

**Why**:
- Follows existing pattern (`weather_agent.py` uses dataclasses)
- LangChain/LangGraph support both
- Lighter weight than Pydantic
- Still type-safe

**When to Use Pydantic**:
- API boundaries (already done in `app/api/schemas.py`)
- Configuration (already done in `app/config.py`)
- Need validation beyond types

### **Decision 4: Single Prompt (Not Multi-Prompt System)**

**Why**:
- Task is straightforward (analyze + recommend)
- No clear separation needed (planning vs execution)
- Easier to manage/version

**When to Split**:
- Need separate router prompt (which tool to use)
- Need separate safety check prompt
- Need separate formatting prompt

### **Decision 5: Tools Return Dicts (Not Pydantic Models)**

**Why**:
- LLM consumes JSON-serializable data
- Easier for LLM to parse
- Internal use of `ProductResult` for type safety, converted to dict for LLM

**Pattern**:
```python
# Internal: Structured
results = _search_vector_index(...)  # Returns list[ProductResult]

# External (to LLM): Dicts
return [r.to_dict() for r in results]  # Returns list[dict]
```

### **Decision 6: Embedded Vector Search (Not Separate Service)**

**Why**:
- Databricks Vector Search is managed service
- No need to run own vector DB
- Integrated with Databricks ecosystem
- Auto-scaling handled by Databricks

**Alternative Considered**:
- Running own Chroma/Pinecone/Weaviate
- Rejected due to operational overhead

---

## ⚠️ Common Pitfalls to Avoid

### **Pitfall 1: Putting Orchestration in Tools**

**BAD**:
```python
@tool
def search_and_decide(query: str) -> dict:
    activities = search_activities(query)
    books = search_books(query)
    
    # ❌ Tool deciding what to do next
    if len(activities) > len(books):
        return {"type": "use_activities", "data": activities}
    else:
        return {"type": "use_books", "data": books}
```

**GOOD**:
```python
# Tools only do work
@tool
def search_activities(query: str) -> list[dict]:
    return search_results

@tool
def search_books(query: str) -> list[dict]:
    return search_results

# Agent decides what to do
agent = create_agent(tools=[search_activities, search_books])
```

### **Pitfall 2: Hardcoding Config**

**BAD**:
```python
def recommend_products(...):
    chat_model = ChatDatabricks(endpoint="databricks-gpt-5-mini")  # ❌ Hardcoded
```

**GOOD**:
```python
def recommend_products(...):
    chat_model = ChatDatabricks(endpoint=settings.llm_endpoint)  # ✅ Configurable
```

### **Pitfall 3: String-Based Tool Outputs**

**BAD**:
```python
@tool
def search_activities(query: str) -> str:
    return "Found 3 activities: Activity A, Activity B, Activity C"  # ❌ String
```

**GOOD**:
```python
@tool
def search_activities(query: str) -> list[dict]:
    return [
        {"product_id": "a", "title": "Activity A"},
        {"product_id": "b", "title": "Activity B"},
    ]  # ✅ Structured
```

### **Pitfall 4: Mixing HTTP Logic in Agent**

**BAD**:
```python
def recommend_products(request: Request, ...):  # ❌ FastAPI Request in agent
    trace_id = request.state.trace_id
    ...
```

**GOOD**:
```python
# Route extracts trace_id, passes as parameter
def recommend_products(trace_id: str, ...):  # ✅ Clean separation
    ...
```

### **Pitfall 5: Unstructured Logging**

**BAD**:
```python
logger.info(f"Processing request for user {user_id}")  # ❌ Unstructured
```

**GOOD**:
```python
logger.info("processing_request", user_id=user_id)  # ✅ Structured (JSON)
```

### **Pitfall 6: Missing Error Handling in Tools**

**BAD**:
```python
@tool
def search_activities(query: str) -> list[dict]:
    results = index.similarity_search(query)  # ❌ What if this fails?
    return results
```

**GOOD**:
```python
@tool
def search_activities(query: str) -> list[dict]:
    try:
        results = index.similarity_search(query)
        return results
    except Exception as e:
        logger.error("search_failed", error=str(e))
        return []  # ✅ Return empty, let agent decide
```

### **Pitfall 7: Forgetting Budget Constraints**

**BAD**:
```python
agent.invoke(input, config={})  # ❌ No recursion limit
```

**GOOD**:
```python
config = {
    "recursion_limit": settings.max_agent_steps  # ✅ Explicit budget
}
agent.invoke(input, config=config)
```

---

## 📚 Reference Implementation Patterns

### **Pattern 1: Tool Implementation**

**Template**:
```python
from langchain.tools import tool, ToolRuntime
from agent.schemas import AgentContext
import structlog

logger = structlog.get_logger(__name__)

@tool
def your_tool_name(
    arg1: str,  # Explicit args
    arg2: int,
    runtime: ToolRuntime[AgentContext]  # Context from agent
) -> list[dict]:  # Structured output
    """Tool description for LLM.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        runtime: Runtime with AgentContext
    
    Returns:
        List of structured results
    """
    # 1. Get context
    context = runtime.context
    
    # 2. Log start
    logger.info("tool_started", trace_id=context.trace_id, arg1=arg1)
    
    # 3. Do work (pure function)
    try:
        results = do_actual_work(arg1, arg2)
    except Exception as e:
        logger.error("tool_failed", error=str(e), exc_info=True)
        return []  # Return empty on error
    
    # 4. Log completion
    logger.info("tool_completed", results_count=len(results))
    
    # 5. Return structured data
    return [r.to_dict() for r in results]
```

### **Pattern 2: Agent Implementation**

**Template**:
```python
from databricks_langchain import ChatDatabricks
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
import mlflow

from app.config import settings
from agent.schemas import AgentContext, AgentResponse
from core.tools import tool1, tool2

@mlflow.trace
def your_agent_name(
    input_param1: str,
    input_param2: str,
    trace_id: str
) -> AgentResponse:
    """Agent description.
    
    Args:
        input_param1: Description
        input_param2: Description
        trace_id: Trace ID for observability
    
    Returns:
        Structured agent response
    """
    # 1. Initialize LLM
    chat_model = ChatDatabricks(
        endpoint=settings.llm_endpoint,
        temperature=settings.llm_temperature
    )
    
    # 2. Initialize checkpointer
    checkpointer = InMemorySaver()
    
    # 3. Load prompt
    system_prompt = mlflow.genai.load_prompt(settings.prompt_name)
    
    # 4. Create agent
    agent = create_agent(
        model=chat_model,
        system_prompt=system_prompt.format(),
        tools=[tool1, tool2],
        context_schema=AgentContext,
        response_format=ToolStrategy(AgentResponse),
        checkpointer=checkpointer
    )
    
    # 5. Create context
    context = AgentContext(
        trace_id=trace_id,
        param1=input_param1,
        param2=input_param2
    )
    
    # 6. Invoke with budget
    config = {
        "configurable": {"thread_id": trace_id},
        "recursion_limit": settings.max_agent_steps
    }
    
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "..."}]},
        config=config,
        context=context
    )
    
    # 7. Return structured response
    return response["structured_response"]
```

### **Pattern 3: API Route Implementation**

**Template**:
```python
from typing import Annotated
from fastapi import APIRouter, Depends, Request
import structlog

from app.middleware.auth import verify_api_key
from app.api.schemas import YourRequest, YourResponse
from agent.your_agent import your_agent_function

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post(
    "/your-endpoint",
    response_model=YourResponse,
    summary="Short description",
    description="Long description with examples",
    tags=["YourCategory"]
)
async def your_endpoint(
    request: Request,
    body: YourRequest,
    api_key: Annotated[str, Depends(verify_api_key)]
) -> YourResponse:
    """Endpoint docstring."""
    
    # 1. Get trace_id
    trace_id = request.state.trace_id
    
    # 2. Log request
    logger.info("endpoint_request", trace_id=trace_id, ...)
    
    # 3. Invoke agent
    try:
        agent_response = your_agent_function(
            param1=body.param1,
            param2=body.param2,
            trace_id=trace_id
        )
    except Exception as e:
        logger.error("agent_failed", trace_id=trace_id, error=str(e))
        raise
    
    # 4. Transform response
    api_response = YourResponse(
        field1=agent_response.field1,
        trace_id=trace_id,
        ...
    )
    
    # 5. Log success
    logger.info("endpoint_success", trace_id=trace_id)
    
    return api_response
```

---

## 🎓 Key Takeaways for Next Agent

### **Top 10 Things to Remember**

1. **Follow the Guidelines**: They're not suggestions. They prevent technical debt.

2. **One Flow Controller**: Agent decides sequence. Never tools or prompts.

3. **Typed Boundaries**: Every component interface has a schema.

4. **Structured Outputs**: Tools return dicts/models, NOT strings.

5. **Explicit Config**: Everything configurable is in `app/config.py`.

6. **Log State**: Structured logs with trace IDs, metrics, not vibes.

7. **LangChain v1**: Use modern APIs. LangGraph migration ready.

8. **Three Missing Pieces**: MLFlow prompt, vector indexes, endpoint.

9. **Test Before Deploy**: Unit tests → Integration tests → E2E tests.

10. **Observability First**: Logging, tracing, metrics from day 1.

### **First Actions After Handoff**

1. ✅ Read this document thoroughly
2. ✅ Review all code files (understand patterns)
3. ✅ Create MLFlow prompt
4. ✅ Create/configure vector search indexes and endpoint
5. ✅ Update `.env` with real credentials
6. ✅ Run `./run_local.sh` and fix any issues
7. ✅ Test with `./test_api.sh`
8. ✅ Add version tracking
9. ✅ Expand test coverage
10. ✅ Prepare EKS deployment

### **Where to Get Help**

- **LangChain Docs**: https://python.langchain.com/docs/
- **Databricks Docs**: https://docs.databricks.com/
- **MLFlow Docs**: https://mlflow.org/docs/latest/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Existing Code**: `agent/weather_agent.py` - reference implementation

---

## 📞 Contact & Support

If you need clarification on any design decision or implementation detail, refer to:
1. This HANDOFF document
2. Code comments and docstrings
3. README.md for user-facing documentation
4. Original requirements at the top of this document

**Good luck! The scaffolding is solid. Now make it run! 🚀**

---

**End of Handoff Document**

