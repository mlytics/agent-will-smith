# Agent Will Smith

Production-grade AI agent platform built with LangGraph, Databricks, and FastAPI.

## Overview

| Component | Purpose |
|-----------|---------|
| **LangGraph** | Stateful multi-agent workflows with explicit state machines |
| **Databricks Vector Search** | Semantic search and retrieval |
| **MLFlow** | Prompt versioning and LLM tracing |
| **FastAPI** | HTTP API with auto-generated docs at `/docs` |


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

**Minimum required configuration:**

```bash
# Databricks Authentication (choose one method)
CORE_DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
CORE_DATABRICKS_CLIENT_ID=your-oauth-client-id          # Production (OAuth)
CORE_DATABRICKS_CLIENT_SECRET=your-oauth-client-secret  # Production (OAuth)
# OR
CORE_DATABRICKS_CONFIG_PROFILE=default                  # Development (CLI)

# FastAPI
CORE_FASTAPI_VERSION=0.1.0
CORE_FASTAPI_API_KEY=your-secure-api-key                # Generate: openssl rand -hex 32
CORE_FASTAPI_ENABLE_DOCS=true                           # Enable /docs endpoint

# MLFlow
CORE_MLFLOW_TRACKING_URI=databricks
CORE_MLFLOW_EXPERIMENT_ID=your-experiment-id
CORE_MLFLOW_ENABLE_TRACING=true

# Agent Configuration (example for product_recommendation)
AGENT_PRODUCT_RECOMMENDATION_AGENT_NAME=product_recommendation
AGENT_PRODUCT_RECOMMENDATION_AGENT_VERSION=1.0.0
AGENT_PRODUCT_RECOMMENDATION_LLM_ENDPOINT=databricks-gpt-4o-mini
AGENT_PRODUCT_RECOMMENDATION_PROMPT_NAME=prompts:/your_catalog.schema.prompt_name/1
# ... (see .env.example for complete agent configuration)
```

**Need detailed setup instructions?** See the [Configuration](#configuration) section below for:
- How to obtain Databricks OAuth credentials or set up CLI profile
- Creating MLflow experiments and registering prompts
- Setting up LLM serving endpoints and vector search indexes
- Complete environment variable reference with validation rules

### 3. Run

```bash
# Install dependencies
uv sync

# Run the application
docker-compose up

# Or uv
uv run uvicorn agent_will_smith.main:app --reload --host 0.0.0.0 --port 8000


```

Visit `http://localhost:8000/docs` for interactive API documentation (requires `CORE_FASTAPI_ENABLE_DOCS=true` in `.env`).



## Architecture

The main architectural problem this codebase solves is not scale, but change:

• Adding new agents without breaking existing ones
• Swapping LLM providers without touching 10 files
• Testing without hitting real APIs (or waiting 30 seconds per test)
• Debugging production issues without becoming a log archaeologist

To make change cheap and safe, we enforce boundaries that prevent hidden coupling between agents and layers.

---

### 1. Three-Tier Dependency Injection

**The failure scenario:**

You add a new agent that needs a different LLM provider. You modify the shared config to support both. Suddenly, existing agents start failing in production. Why? Your config change accidentally affected the endpoint URL for Agent A. Or you added conditional logic: `if agent_name == "new_agent" use_claude() else use_gpt()`. Now every agent knows about every other agent. Six months later, someone deletes "new_agent" but forgets to update the conditionals. Silent failures everywhere.

**How this repo prevents it:**

**Structure:**
```
Core Container → shared infrastructure (auth, MLflow, logging)
  ↓
Infra Container → shared clients (LLM, vector search, prompt)
  ↓
Agent Container → agent-specific wiring (per-agent config, endpoints)
```

**Example:**
```python
# Agent A container
class ProductRecommendationContainer(DeclarativeContainer):
    core = providers.Container(CoreContainer)
    infra = providers.Container(InfraContainer, core_container=core)

    agent_config = providers.Singleton(ProductRecommendationConfig)
    llm_client = providers.Singleton(
        infra.llm_client,
        endpoint=agent_config.provided.llm_endpoint  # "databricks-gpt-4"
    )

# Agent B uses different config, same infrastructure
class ContentModerationContainer(DeclarativeContainer):
    # Inherits same Core/Infra, but llm_endpoint = "databricks-claude"
```

**What this prevents:**
- Global config changes affecting multiple agents (each agent container has isolated config)
- Conditional logic based on agent name (agents don't know about each other)
- Coupling between agent implementations (no shared mutable state)
- Expensive test setup (override container providers to inject mocks)

**Extending:** Copy `agent/product_recommendation/` directory, modify `config.py` for your agent's endpoints/indexes, create `container.py` inheriting from Core/Infra, wire in `main.py`. No changes to shared code.

---

### 2. Single Global Exception Handler — Stop Debugging Blindfolded

**The failure scenario:**

Production incident at 2 AM. User reports: "API returned 500." You check logs:
```
ERROR: Something went wrong
ERROR: Failed to process request
ERROR: Database error
```

Which error is theirs? You add more logs to narrow it down. Deploy. Wait for it to happen again. Repeat 3 times. It's now 4 AM and you still don't know if it's your code, Databricks, or the LLM.

This happens because try-catch blocks are scattered across the codebase, each logging differently:
```python
try:
    result = llm.invoke(prompt)
except Exception as e:
    logger.error("LLM failed")  # Lost the original exception type
    return None  # Silent failure
```

**How this repo prevents it:**

**One exception hierarchy in `core/exceptions.py`. One global handler in `main.py`. No try-catch in business logic.**

Infrastructure layer translates external errors to domain exceptions:
```python
try:
    return databricks_client.search(query)
except DatabricksTimeout as e:
    raise UpstreamTimeoutError(
        "Vector search timed out",
        details={
            "provider": "databricks_vector_search",
            "operation": "similarity_search",
            "timeout_seconds": 30
        }
    ) from e  # Preserves original stack trace
```

Global handler catches everything, logs with trace ID, returns consistent JSON:
```json
{
    "error": "UpstreamTimeoutError",
    "message": "Vector search timed out",
    "trace_id": "550e8400-...",
    "details": {"provider": "databricks_vector_search", ...}
}
```

Now at 2 AM, you see `UpstreamTimeoutError` → external service, not your code. Check `details` → `databricks_vector_search`. Grep logs by `trace_id` → see the full request. Done in 5 minutes.

*(Principle: Single Responsibility — error handling happens at one layer, not scattered throughout)*

**Next step:** Raise exceptions from `core/exceptions.py`, never write try-catch in business logic

---

### 3. Namespace-Based State — Stop Developers From Stepping on Each Other

**The failure scenario:**

Developer A adds a node that writes to `state.results`:
```python
state.results = search_books(query)
```

Developer B (working in parallel) adds a different node that also writes to `state.results`:
```python
state.results = search_activities(query)
```

Both PRs pass tests. Code merges cleanly — no merge conflict. But in production, they silently overwrite each other's data. Books sometimes work, activities sometimes work, depending on execution order. The bug is intermittent and takes two days to track down because you need to reproduce the exact node execution sequence.

**How this repo prevents it:**

Each node owns a namespace. Read from any namespace, write only to your own:

```python
class AgentState(BaseModel):
    input: AgentInput
    intent_node: Optional[IntentNodeNamespace]     # Only IntentAnalysisNode writes here
    search_node: Optional[SearchNodeNamespace]     # Only ParallelSearchNode writes here
    output: Optional[AgentOutput]                  # Only OutputNode writes here
```

```python
class IntentAnalysisNode:
    def __call__(self, state: AgentState) -> dict:
        article = state.input.article  # ✅ Read from input namespace
        return {"intent_node": IntentNodeNamespace(intent=result)}  # ✅ Write to own namespace
```

Now the overwrite bug is **structurally impossible**. If Developer A's node tries to write to `search_node` namespace, it won't compile.

Code reviews become trivial: reviewing `IntentAnalysisNode`? Only check the `intent_node` namespace. You don't need to understand the entire state machine to know if this change is safe.

*(Principle: Single Writer — each piece of data has exactly one writer, preventing accidental overwrites)*

**Next step:** When adding a node, create its namespace in `model/namespaces.py`, add to `state.py`, node writes only there

---

### 4. Pydantic Everywhere — Catch Typos Before Production

**The failure scenario:**

You deploy to production. Config looks fine locally. But prod crashes on startup:
```
KeyError: 'databrics_host'
```

You typo'd `databricks` as `databrics` in the .env file. But the error only surfaced after deployment because Python's dynamic typing let it through.

Or worse: LLM returns `productId` but your code expects `product_id`. No error, just silently broken results in production that users report a week later.

**How this repo prevents it:**

Pydantic models at **every boundary**: API input, agent state, configs, database DTOs, LLM responses.

```python
class DatabricksConfig(BaseSettings):
    host: str = Field(..., description="Databricks workspace URL")
    # Typo in env var? Fails at startup, not in production
```

LLM returns wrong field name?
```python
class ProductDTO(BaseModel):
    product_id: str  # If LLM returns productId, Pydantic rejects it immediately
```

IDE autocomplete works everywhere because everything has types. Typo in field name? Red squiggle before you even run the code.

*(Principle: Fail-Fast — errors at boundaries, not deep in business logic)*

**Next step:** Define Pydantic models for any external data (API, LLM, DB), validate immediately at boundary

---

### 5. MLflow Tracing — Measure What You Can't See

**The failure scenario:**

You have two prompt versions. V1 feels "better" but you're not sure. V2 is shorter (cheaper) but might lose quality. You deploy V2, users complain a week later. You roll back to V1. Did it actually get better? You're flying blind.

**How this repo prevents it:**

Every agent invocation logs to MLflow: LLM call, prompt version, tokens used, vector search results, outputs.

**Offline eval (development):**
Run 100 test cases with V1, 100 with V2. Compare accuracy, hallucination rate, cost. Make data-driven decisions.

**Online eval (production):**
Agent quality degrading? Query MLflow for last 10K runs. Aggregate: relevance scores by customer segment, token costs per request, failure rates. Which prompts underperform on which inputs? Now you know what to fix.

**Debugging:**
User reports bad output. Search MLflow by customer_uuid. See: exact prompt sent, LLM's raw response, vector search results, final output. Reproduce locally without guessing.

*(Principle: Observability — you cannot improve what you cannot measure)*

**Next step:** Use MLflow UI to compare prompt versions, query traces for aggregate metrics

---

### 6. Prompt Versioning — Change Prompts Without Deploying Code

**The failure scenario:**

Prompt causing hallucinations. Fixing it requires: edit code → commit → PR review → CI/CD → deploy. Takes 2 hours. Meanwhile users get bad outputs.

Or: prompt engineer wants to A/B test prompts. But they need a developer to gate the change with feature flags, deploy, monitor. Iteration speed: 1 change/day.

**How this repo prevents it:**

Prompts live in MLflow registry, not code. Reference by name in config:
```python
prompt_name: str = "product_recommendation_v2"
```

Prompt engineer: modify in MLflow UI → tag as "staging" → test → tag as "production". Zero deployments. Agent fetches latest on next request.

Rollback? Change tag from "production" to "archived" in MLflow. Instant.

A/B test? Deploy two agent instances with different `prompt_name` configs. Route 50% traffic to each.

*(Principle: Immutability — prompts are versioned artifacts with full audit trail)*

**Next step:** Register prompts in MLflow, reference by name in agent config, iterate without code changes

---

### 7. Trace IDs — Grep Your Way Out of Production Fires

**The failure scenario:**

User: "My request failed." You check logs, see 10,000 entries from the last minute. Which ones are theirs? You don't know. You ask for timestamp. They give you "around 2:30 PM". You grep logs around that time, find 50 possible requests. Which one?

**How this repo prevents it:**

Every request gets a UUID trace ID. Middleware binds it to `contextvars`. Every log line includes it automatically:

```json
{"message": "Processing article", "trace_id": "550e8400-...", "method": "POST"}
```

User reports issue? API response includes trace ID. Grep logs:
```bash
grep "550e8400" logs.json
```

See every log line from that request: input, LLM calls, vector searches, output, timing. Full context in 30 seconds.

For developers: no manual passing. Just `logger.info()` — context propagates automatically.

*(Principle: Distributed Tracing — correlate logs across layers with unique identifiers)*

**Next step:** Return trace IDs in API responses, use them in support tickets, grep logs by trace ID

---

### 8. Configuration Management — Agent Isolation Through Namespacing

**The failure scenario:**

You add Agent B that needs different LLM settings. You modify the shared `config.py` to add a `use_claude` flag. Agent A starts failing because it reads the same config. You add `if agent_name == "B"` conditionals. Now every agent knows about every other agent. Six months later, someone removes Agent B but forgets to update the conditionals. Prod breaks silently.

Or worse: you typo `databrics_host` in the `.env` file. Python's dynamic typing lets it through locally. The error only surfaces in production after deployment, crashing on startup.

**How this repo prevents it:**

Two-tier **namespaced environment variables** with Pydantic validation at startup:

```python
# Agent A reads only AGENT_PRODUCT_RECOMMENDATION_* variables
class ProductRecommendationConfig(BaseAgentConfig):
    model_config = SettingsConfigDict(env_prefix="AGENT_PRODUCT_RECOMMENDATION_")
    llm_endpoint: str  # Reads AGENT_PRODUCT_RECOMMENDATION_LLM_ENDPOINT
    
# Agent B reads only AGENT_CONTENT_MODERATION_* variables  
class ContentModerationConfig(BaseAgentConfig):
    model_config = SettingsConfigDict(env_prefix="AGENT_CONTENT_MODERATION_")
    llm_endpoint: str  # Reads AGENT_CONTENT_MODERATION_LLM_ENDPOINT
```

**Namespace layers:**
- `CORE_*` → Shared infrastructure (Databricks auth, MLflow, FastAPI, logging)
- `AGENT_<NAME>_*` → Agent-specific (prompts, LLM endpoints, indexes, behavior)

**What this prevents:**
- Configuration drift between agents (each has isolated namespace in `.env`)
- Cross-agent pollution (Agent A physically cannot read Agent B's variables)
- Runtime typos (`databrics_host` → Pydantic fails at startup with clear error)
- Conditional logic (`if agent_name ==` becomes structurally impossible)

**Extending:** Copy `agent/product_recommendation/` → `agent/new_agent/`, change `env_prefix` in `config.py`, add `AGENT_NEW_AGENT_*` variables to `.env`. Zero shared config changes. Zero risk to existing agents.

*(Principle: Namespace Isolation — configuration boundaries prevent hidden coupling between agents)*

**Next step:** When adding an agent, inherit from `BaseAgentConfig`, set unique `env_prefix`, add namespaced variables to `.env`

---

## If You Are...

**Adding a new agent:**
1. Copy `agent/product_recommendation/` → `agent/your_agent/` (don't modify the original)
2. **Don't touch shared code:** Edit only `your_agent/config.py` (set your LLM endpoint, vector indexes, prompt name)
3. **Keep it isolated:** Edit `your_agent/container.py` - inherit from Core/Infra, add only your agent's specific wiring
4. **Wire at the edge:** Add your container to `main.py` - no changes to other agents' wiring
5. **Pro tip:** Test your agent before wiring it in - run it standalone first

**Debugging production:**
1. Get trace ID from API response or user report
2. **First:** Check exception type in logs - `UpstreamTimeoutError` = external service, `ValidationError` = bad input, `InternalError` = your code
3. **Then:** Grep full trace: `grep "550e8400" logs.json | jq '.message'` to see the request flow
4. **Finally:** Open MLflow UI, search by trace ID, see exact prompts/LLM responses that caused the issue
5. **Pro tip:** Never start with "let me check the logs" - start with MLflow traces for context

**Writing tests:**
1. **Never patch imports:** Don't do `mock.patch('agent_will_smith.infra.llm_client.LLMClient')` - it creates coupling
2. **Instead:** Override container providers: `container.llm_client.override(FakeLLM())` in test fixtures
3. **Never set env vars in tests:** Use container overrides, not `os.environ['OPENAI_API_KEY'] = 'fake'`
4. **Fast feedback:** Tests run in seconds? Good. 30+ seconds? You're hitting real APIs - fix immediately
5. **Pro tip:** If you need to test error handling, override the client to raise exceptions, don't mock at the import level

**Iterating on prompts:**
1. Modify in MLflow UI (not code)
2. Tag versions: "staging" → test → "production"
3. Compare versions in MLflow: accuracy, cost, failure rates
4. Rollback by changing tags, no code deploy needed

**Adding a new node:**
1. Create namespace model in `model/namespaces.py`
2. Add to `AgentState` in `state.py`
3. Node writes only to its namespace, reads from any
4. Review focuses only on your namespace — no need to understand full state machine

**Adding a new product vertical:**
1. Add vertical to `Vertical` enum in `model/types.py`
2. Create `ProductDTO` in `repo/dto.py` with `to_product_result()` method
3. Create `ProductMetadata` in `model/product.py` and add to union type
4. Add to registry mappings in `product_registry.py`
5. Add index config field in `config.py` (e.g., `podcasts_index: str`)
6. Add index value to `.env`: `AGENT_PRODUCT_RECOMMENDATION_PODCASTS_INDEX=...`
7. **Total scope: ~40 lines across 6 files** - no changes to workflow, nodes, or API
8. **Pro tip:** The typed metadata classes enforce explicit field definitions - this is intentional friction to ensure proper product modeling

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

## Code Guidelines

**[`CODE_REVIEWS.md`](CODE_REVIEWS.md)** is the single source of truth for coding standards in this repo.

### Using with AI Coding Assistants

When using Claude, Cursor, Copilot, or other AI coding tools:

1. **Feed the guidelines**: Include `CODE_REVIEWS.md` in your AI context or system prompt
2. **AI-assisted reviews**: Ask AI to review your code against `CODE_REVIEWS.md` before submitting PRs
3. **Generate compliant code**: Reference specific sections when asking AI to write new features

```
Example prompt: "Review this code against CODE_REVIEWS.md, specifically the
Exception Handling and LangGraph State Schema sections"
```


## Configuration

Complete reference for all configuration options. All settings are managed through environment variables in `.env` with Pydantic validation at startup.

> **Quick Start**: If you haven't set up your `.env` file yet, start with the [Quick Start](#quick-start) section above.

**Configuration structure:**
- `CORE_*` prefix → Shared infrastructure (Databricks, MLflow, FastAPI, logging)
- `AGENT_<NAME>_*` prefix → Agent-specific settings (isolated per agent)

---

### 1. Databricks Configuration

**Environment Variable Prefix**: `CORE_DATABRICKS_*`  
**Configuration Class**: [`DatabricksConfig`](src/agent_will_smith/core/config/databricks_config.py)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORE_DATABRICKS_HOST` | ✅ | - | Workspace URL (e.g., `https://your-workspace.cloud.databricks.com`) |
| `CORE_DATABRICKS_CLIENT_ID` | ⚠️ | - | OAuth client ID (production authentication) |
| `CORE_DATABRICKS_CLIENT_SECRET` | ⚠️ | - | OAuth client secret (production authentication) |
| `CORE_DATABRICKS_CONFIG_PROFILE` | ⚠️ | - | CLI profile name (development authentication) |

⚠️ = Must provide **EITHER** (client_id + client_secret) **OR** config_profile

**Authentication Options:**

**Option A: OAuth Service Principal (Recommended for Production)**

1. Open Databricks Console → **Settings** → **Identity and Access**
2. Navigate to **Service Principals** → **Add service principal**
3. Create service principal and copy the **Client ID** → Set as `CORE_DATABRICKS_CLIENT_ID`
4. Click **Generate secret** → Copy the secret → Set as `CORE_DATABRICKS_CLIENT_SECRET`
5. Grant necessary workspace permissions to the service principal

📚 [Databricks OAuth M2M Authentication Guide](https://docs.databricks.com/en/dev-tools/auth/oauth-m2m.html)

**Option B: Config Profile (For Local Development)**

1. Install Databricks CLI: `pip install databricks-cli`
2. Run authentication command:
   ```bash
   databricks configure --profile my-profile
   ```
3. Follow prompts to enter workspace URL and credentials
4. Set environment variable:
   ```bash
   CORE_DATABRICKS_CONFIG_PROFILE=my-profile
   ```

📚 [Databricks CLI Authentication Guide](https://docs.databricks.com/en/dev-tools/cli/authentication.html)

**Validation:**
- Configuration fails at startup if neither authentication method is provided
- Automatically sets `DATABRICKS_*` environment variables for SDK compatibility

---

### 2. MLflow Configuration

**Environment Variable Prefix**: `CORE_MLFLOW_*`  
**Configuration Class**: [`MLFlowConfig`](src/agent_will_smith/core/config/mlflow_config.py)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORE_MLFLOW_TRACKING_URI` | ⚠️ | - | MLflow tracking server URI (typically `databricks`) |
| `CORE_MLFLOW_REGISTRY_URI` | ⚠️ | - | Model registry URI (typically `databricks-uc` for Unity Catalog) |
| `CORE_MLFLOW_EXPERIMENT_ID` | ⚠️ | - | Experiment ID for tracing (e.g., `/Users/yourname/experiments`) |
| `CORE_MLFLOW_ENABLE_TRACING` | ❌ | `false` | Enable MLflow tracing for LLM calls and agent execution |

⚠️ = Required if `CORE_MLFLOW_ENABLE_TRACING=true`

**Setup Instructions:**

**Step 1: Set Databricks URIs** (standard values when using Databricks)
```bash
CORE_MLFLOW_TRACKING_URI=databricks
CORE_MLFLOW_REGISTRY_URI=databricks-uc
```

**Step 2: Create MLflow Experiment**

1. Open Databricks Console → **Machine Learning** → **Experiments**
2. Click **Create Experiment**
3. Enter experiment name (e.g., `agent-will-smith-production`)
4. Copy the **Experiment ID** from the URL or experiment details
5. Set as environment variable:
   ```bash
   CORE_MLFLOW_EXPERIMENT_ID=/Users/yourname/agent-experiments
   ```

📚 [MLflow Tracking Guide](https://docs.databricks.com/en/mlflow/tracking.html)

**Step 3: Register Prompts in MLflow**

1. Open Databricks Console → **Machine Learning** → **Prompt Engineering**
2. Click **Create Prompt**
3. Write your prompt template using variables (e.g., `{user_query}`, `{context}`, `{examples}`)
4. Test the prompt with sample inputs
5. Click **Save** and version the prompt
6. Copy the prompt path in format: `prompts:/<catalog>.<schema>.<prompt_name>/<version>`
7. Use this path in agent configuration (see [Agent Configuration](#6-agent-configuration))

Example prompt path:
```bash
prompts:/aigc_prod.intent_engine.product_recommendation_prompt/1
```

📚 [MLflow Prompt Engineering Guide](https://docs.databricks.com/en/mlflow/prompt-engineering.html)

**Step 4: Enable Tracing**
```bash
CORE_MLFLOW_ENABLE_TRACING=true
```

When enabled, every agent invocation logs to MLflow with LLM calls, token usage, prompts, and outputs for debugging and evaluation.

---

### 3. FastAPI Configuration

**Environment Variable Prefix**: `CORE_FASTAPI_*`  
**Configuration Class**: [`FastAPIConfig`](src/agent_will_smith/core/config/fastapi_config.py)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORE_FASTAPI_APP_NAME` | ❌ | `agent-will-smith` | Application name displayed in API docs |
| `CORE_FASTAPI_VERSION` | ✅ | - | Application version (must be semantic version, e.g., `0.1.0`) |
| `CORE_FASTAPI_ENABLE_DOCS` | ❌ | `false` | Enable `/docs` and `/redoc` endpoints |
| `CORE_FASTAPI_PORT` | ❌ | `8000` | Server port number |
| `CORE_FASTAPI_API_KEY` | ✅ | - | Bearer token for API authentication |

**Setup Instructions:**

**Step 1: Set Application Version**

Must be a valid semantic version (validated with `semver` library):
```bash
CORE_FASTAPI_VERSION=0.1.0
```

**Step 2: Generate Secure API Key**

Generate a cryptographically secure API key:
```bash
openssl rand -hex 32
```

Copy the output and set as:
```bash
CORE_FASTAPI_API_KEY=your-generated-key-here
```

**Step 3: Configure Documentation**

```bash
# Development - Enable interactive API docs
CORE_FASTAPI_ENABLE_DOCS=true

# Production - Disable for security
CORE_FASTAPI_ENABLE_DOCS=false
```

**Using the API:**

All API requests must include the authentication header:
```bash
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/api/v1/...
```

API documentation available at:
- Swagger UI: `http://localhost:8000/docs` (when `ENABLE_DOCS=true`)
- ReDoc: `http://localhost:8000/redoc` (when `ENABLE_DOCS=true`)

**Security Note:** The API key is validated by [`auth_middleware.py`](src/agent_will_smith/app/middleware/auth_middleware.py) on every request. Always disable `/docs` in production environments.

---

### 4. Logging Configuration

**Environment Variable Prefix**: `CORE_LOG_*`  
**Configuration Class**: [`LogConfig`](src/agent_will_smith/core/config/log_config.py)

| Variable | Required | Default | Description | Options |
|----------|----------|---------|-------------|---------|
| `CORE_LOG_LEVEL` | ❌ | `info` | Application log level | `debug`, `info`, `warning`, `error`, `fatal` |
| `CORE_LOG_FORMAT` | ❌ | `json` | Log output format | `json` (production), `pretty` (development) |
| `CORE_LOG_THIRD_PARTY_LEVEL` | ❌ | `warning` | Minimum log level for 3rd party libraries | `debug`, `info`, `warning`, `error`, `fatal` |

**Recommended Settings by Environment:**

**Development:**
```bash
CORE_LOG_LEVEL=debug
CORE_LOG_FORMAT=pretty           # Colored, human-readable output
CORE_LOG_THIRD_PARTY_LEVEL=warning
```

**Production:**
```bash
CORE_LOG_LEVEL=info
CORE_LOG_FORMAT=json             # Structured logs for log aggregation
CORE_LOG_THIRD_PARTY_LEVEL=warning
```

**Log Level Guidelines:**
- `debug`: Verbose logging for troubleshooting (generates large log volumes)
- `info`: General operational messages (recommended for production)
- `warning`: Unexpected but handled conditions
- `error`: Error events that might still allow the application to continue
- `fatal`: Severe errors causing application termination

**Third-Party Libraries:**

The `CORE_LOG_THIRD_PARTY_LEVEL` setting controls log verbosity for:
- `mlflow` - MLflow tracking and model operations
- `databricks` - Databricks SDK operations
- `langgraph` - LangGraph agent execution
- `uvicorn` - ASGI server logs

Setting this to `warning` reduces noise while keeping important error messages.

---

### 5. Agent Configuration

**Environment Variable Prefix**: `AGENT_<AGENT_NAME>_*`  
**Base Class**: [`BaseAgentConfig`](src/agent_will_smith/core/config/base_agent_config.py)

Each agent has **isolated configuration** with its own namespace. Agents inherit common metadata from `BaseAgentConfig` and define their own specific fields based on their functionality.

> **Important**: Each agent defines its own configuration fields. The examples below show the Product Recommendation agent, but your agent may have completely different fields depending on its requirements.

**Common Configuration (All Agents):**

These fields are inherited from [`BaseAgentConfig`](src/agent_will_smith/core/config/base_agent_config.py) and **required for all agents**:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENT_<NAME>_AGENT_NAME` | ✅ | - | Agent identifier (e.g., `product_recommendation`, `content_moderation`) |
| `AGENT_<NAME>_AGENT_VERSION` | ✅ | - | Agent version (semantic version format, e.g., `1.0.0`) |
| `AGENT_<NAME>_PROMPT_CACHE_TTL` | ✅ | - | Prompt cache TTL in seconds (e.g., `3600`) |

**Agent-Specific Configuration (Varies by Agent):**

Each agent defines additional fields in its own `config.py`. Below are **examples from the Product Recommendation agent** ([`ProductRecommendationConfig`](src/agent_will_smith/agent/product_recommendation/config.py)):

**Example: LLM Configuration**

| Variable | Description |
|----------|-------------|
| `AGENT_PRODUCT_RECOMMENDATION_LLM_ENDPOINT` | Databricks serving endpoint name |
| `AGENT_PRODUCT_RECOMMENDATION_LLM_TEMPERATURE` | Sampling temperature (0.0-2.0) |
| `AGENT_PRODUCT_RECOMMENDATION_LLM_MAX_TOKENS` | Maximum tokens in LLM response |

**Example: Vector Search Configuration**

| Variable | Description |
|----------|-------------|
| `AGENT_PRODUCT_RECOMMENDATION_VECTOR_SEARCH_ENDPOINT` | Databricks vector search endpoint name |
| `AGENT_PRODUCT_RECOMMENDATION_ACTIVITIES_INDEX` | Vector search index for activities vertical |
| `AGENT_PRODUCT_RECOMMENDATION_BOOKS_INDEX` | Vector search index for books vertical |
| `AGENT_PRODUCT_RECOMMENDATION_ARTICLES_INDEX` | Vector search index for articles vertical |

**Example: Agent Behavior**

| Variable | Description |
|----------|-------------|
| `AGENT_PRODUCT_RECOMMENDATION_MAX_K_PRODUCTS` | Maximum number of products to return |
| `AGENT_PRODUCT_RECOMMENDATION_MAX_AGENT_STEPS` | Maximum reasoning steps |
| `AGENT_PRODUCT_RECOMMENDATION_AGENT_TIMEOUT_SECONDS` | Agent execution timeout |

**Example: Prompt Management**

| Variable | Description |
|----------|-------------|
| `AGENT_PRODUCT_RECOMMENDATION_PROMPT_NAME` | MLflow prompt registry path (format: `prompts:/<catalog>.<schema>.<name>/<version>`) |

> **Note**: Your agent might need different fields entirely. For example:
> - A content moderation agent might have `MODERATION_THRESHOLDS`, `BLOCKED_CATEGORIES`
> - A summarization agent might only need `LLM_ENDPOINT`, `MAX_SUMMARY_LENGTH`, `PROMPT_NAME`
> - Define only the fields your agent requires in its `config.py`

**Common Setup Steps (Applicable to Most Agents):**

> **Note**: These are common setup patterns. Your specific agent may require different resources or additional configuration.

**Configuring LLM Endpoints** (if your agent uses LLMs)

**Option A: Use Databricks Foundation Models** (Recommended - No setup required)

Databricks provides pre-deployed Foundation Model endpoints ready to use:

```bash
# Examples of pre-deployed endpoints
AGENT_YOUR_AGENT_LLM_ENDPOINT=databricks-meta-llama-3-1-70b-instruct
AGENT_YOUR_AGENT_LLM_ENDPOINT=databricks-dbrx-instruct
AGENT_YOUR_AGENT_LLM_ENDPOINT=databricks-mixtral-8x7b-instruct
```

📚 [Available Foundation Models](https://docs.databricks.com/en/machine-learning/foundation-models/index.html)

**Option B: Create Custom Serving Endpoint** (For fine-tuned models)

1. Databricks Console → **Serving** → **Create serving endpoint**
2. Deploy your custom fine-tuned model
3. Copy endpoint name → Set as `AGENT_<NAME>_LLM_ENDPOINT`

📚 [Databricks Model Serving Guide](https://docs.databricks.com/en/machine-learning/model-serving/index.html)

**Creating Vector Search Resources** (if your agent uses vector search)

1. **Create Endpoint**: Databricks Console → Compute → Vector Search → Create endpoint
2. **Prepare Data**: Delta table with vector embeddings column (array of floats)
3. **Create Indexes**: Vector Search → Create index → Select endpoint and source table
4. Set index names as agent-specific variables (e.g., `AGENT_<NAME>_<INDEX_NAME>_INDEX`)

📚 [Databricks Vector Search Guide](https://docs.databricks.com/en/generative-ai/vector-search.html)

**Registering Prompts** (if your agent uses prompts)

1. Databricks Console → Machine Learning → Prompt Engineering → Create Prompt
2. Register prompt with variables (e.g., `{user_query}`, `{context}`)
3. Copy path format: `prompts:/<catalog>.<schema>.<prompt_name>/<version>`
4. Set as agent-specific variable (e.g., `AGENT_<NAME>_PROMPT_NAME`)

📚 [MLflow Prompt Engineering](https://docs.databricks.com/en/mlflow/prompt-engineering.html)

---

**Example: Product Recommendation Agent Configuration**

```bash
# Common Metadata (Required for all agents)
AGENT_PRODUCT_RECOMMENDATION_AGENT_NAME=product_recommendation
AGENT_PRODUCT_RECOMMENDATION_AGENT_VERSION=1.0.0
AGENT_PRODUCT_RECOMMENDATION_PROMPT_CACHE_TTL=3600

# Agent-Specific Configuration (unique to this agent)
AGENT_PRODUCT_RECOMMENDATION_LLM_ENDPOINT=databricks-gpt-4o-mini
AGENT_PRODUCT_RECOMMENDATION_LLM_TEMPERATURE=0.7
AGENT_PRODUCT_RECOMMENDATION_LLM_MAX_TOKENS=2048

AGENT_PRODUCT_RECOMMENDATION_VECTOR_SEARCH_ENDPOINT=vs-endpoint-production
AGENT_PRODUCT_RECOMMENDATION_ACTIVITIES_INDEX=main.catalog.activities_index
AGENT_PRODUCT_RECOMMENDATION_BOOKS_INDEX=main.catalog.books_index
AGENT_PRODUCT_RECOMMENDATION_ARTICLES_INDEX=main.catalog.articles_index

AGENT_PRODUCT_RECOMMENDATION_MAX_K_PRODUCTS=10
AGENT_PRODUCT_RECOMMENDATION_PROMPT_NAME=prompts:/aigc_prod.intent_engine.product_recommendation_prompt/1
```

---

**Adding Your Own Agent:**

1. Create config class in `agent/<your_agent>/config.py`:
   ```python
   from src.agent_will_smith.core.config.base_agent_config import BaseAgentConfig
   from pydantic_settings import SettingsConfigDict
   
   class Config(BaseAgentConfig):
       model_config = SettingsConfigDict(
           env_prefix="AGENT_YOUR_AGENT_",
           env_file=".env",
       )
       
       # Define your agent-specific fields here
       your_custom_field: str
       another_field: int = 100  # with default
   ```

2. Add variables to `.env`:
   ```bash
   # Common metadata (required)
   AGENT_YOUR_AGENT_AGENT_NAME=your_agent
   AGENT_YOUR_AGENT_AGENT_VERSION=1.0.0
   AGENT_YOUR_AGENT_PROMPT_CACHE_TTL=3600
   
   # Your agent-specific fields
   AGENT_YOUR_AGENT_YOUR_CUSTOM_FIELD=value
   AGENT_YOUR_AGENT_ANOTHER_FIELD=200
   ```

3. Configuration is automatically loaded and validated at startup
