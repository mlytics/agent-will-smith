# Agent Will Smith

Production-grade AI agent platform built with LangGraph, Databricks, and FastAPI.

## Overview

| Component | Purpose |
|-----------|---------|
| **LangGraph** | Stateful multi-agent workflows with explicit state machines |
| **Databricks Vector Search** | Semantic search and retrieval |
| **MLFlow** | Prompt versioning and LLM tracing |
| **FastAPI** | HTTP API with auto-generated docs at `/docs` |

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

### What's Covered

| Section | What You'll Learn |
|---------|-------------------|
| Naming Conventions | File/class naming, import style, package structure |
| Dependency Injection | Container patterns, singleton management, wiring |
| Exception Handling | 7 rules for consistent error handling |
| Configuration | Namespaced env vars, 12-factor compliance |
| LangGraph State | Namespace ownership, Pydantic throughout, dual-purpose DTOs |
| Schema Organization | Where domain models vs DTOs belong |
