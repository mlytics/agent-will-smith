# Code Guidelines & Review Rules

Pretend you're a senior software architect doing a code review and you HATE this implementation.

The following is a list of rules specifically for this repo to follow strictly.

Besides the rules
- what would you criticize? Refer to the best practices and software engineering principles.
- what edge cases are missing?

**Don't just insepct if the code follows the rules.**
**Also criticize the code based on the best practices and software engineering principles.**

## Naming Conventions

### File and Class Naming
**Rule:** Folder names are business-specific. File names and class names are generic. Import paths provide context.

```
# ✅ CORRECT - Generic names, business context from path
src/agent/product_recommendation/
├── agent.py              # class Agent
├── container.py          # class Container
└── node/
    ├── intent_analysis_node.py
    └── parallel_search_node.py

# Import provides full context
from src.agent.product_recommendation.agent import Agent
from src.core.container import Container

# ❌ INCORRECT - Redundant prefixes
src/agent/product_recommendation/
├── product_recommendation_agent.py     # class ProductRecommendationAgent
└── product_recommendation_container.py # class ProductRecommendationContainer
```

**Why this matters:**
- **Searchability**: Find by path (`agent/product_recommendation/`) or component type (`agent.py`, `router.py`)
- **No Redundancy**: Avoid "ProductRecommendationAgent" disease
- **Scalability**: Easy to add new features without name collisions
- **Clean Imports**: `from product_recommendation.agent import Agent` is self-documenting

**Naming Rules by Layer:**
- **Folders**: Business feature slugs (`product_recommendation`, `risk_scoring`, `user_auth`)
- **Top-level files**: Generic component names (`agent.py`, `router.py`, `container.py`)
- **Classes**: Generic but role-specific (`Agent`, `Container`, `Router`)
- **Sub-components**: Can be more specific if needed (`intent_analysis_node.py`)

**When to Be More Specific:**

Sub-components like nodes, tools, or utilities can have descriptive names when:
- Multiple instances exist in same folder (`intent_analysis_node.py`, `parallel_search_node.py`)
- Component is not the primary entry point
- Specificity aids discovery within the module

```python
# ✅ CORRECT - Specific names for multiple similar components
src/agent/product_recommendation/node/
├── intent_analysis_node.py    # class IntentAnalysisNode
├── parallel_search_node.py    # class ParallelSearchNode
└── compose_response_node.py   # class ComposeResponseNode

# ✅ CORRECT - Generic names for primary components
src/agent/product_recommendation/
├── agent.py        # Main entry point - generic name
└── container.py    # DI container - generic name
```

**Handling Import Collisions:**

When importing multiple similar classes, use aliases with the feature prefix:

```python
# ✅ CORRECT - Clear aliases when needed
from src.agent.product_recommendation.agent import Agent as ProductAgent
from src.agent.risk_scoring.agent import Agent as RiskAgent
from src.core.container import Container as CoreContainer

# ⚠️ AVOID - Only use aliases when there's actual collision
from src.agent.product_recommendation.agent import Agent as ProductAgent
# Not needed if you're only importing one Agent in this file

# ❌ INCORRECT - Using aliases everywhere unnecessarily
from src.agent.product_recommendation.router import router as product_router
# Just import as 'router' if no collision exists
```

**Folder Naming Anti-Patterns:**

```
# ❌ BAD - Technical suffixes instead of business names
src/agent/
├── recommendation_agent/      # Remove '_agent' suffix
├── scoring_service/           # Remove '_service' suffix
└── user_handler/              # Remove '_handler' suffix

# ✅ GOOD - Pure business domain names
src/agent/
├── product_recommendation/    # Business feature
├── risk_scoring/              # Business feature
└── user_authentication/       # Business feature

# ❌ BAD - Generic/vague folder names
src/agent/
├── core/          # Too generic - core of what?
├── utils/         # Junk drawer - utils for what?
└── helpers/       # Meaningless - help with what?

# ✅ GOOD - Specific business domains
src/agent/
├── content_moderation/   # Clear business purpose
├── sentiment_analysis/   # Clear business purpose
└── fraud_detection/      # Clear business purpose

# ❌ BAD - Abbreviations and acronyms
src/agent/
├── prod_rec/      # Unclear abbreviation
├── usr_mgmt/      # Hard to search
└── auth_n_z/      # Cryptic

# ✅ GOOD - Full, searchable names
src/agent/
├── product_recommendation/
├── user_management/
└── authentication/
```

### Package Initialization

**Rule:** All `__init__.py` files MUST be empty. Use explicit imports from module files.

```python
# ✅ CORRECT - Empty __init__.py
# (file is empty or contains only a newline)

# ✅ CORRECT - Explicit imports
from agent_will_smith.agent.product_recommendation.agent import Agent
from agent_will_smith.core.container import Container as CoreContainer

# ❌ INCORRECT - Convenience re-exports in __init__.py
# In src/agent/__init__.py:
from agent_will_smith.agent.product_recommendation.agent import Agent
from agent_will_smith.agent.product_recommendation.container import Container
__all__ = ["Agent", "Container"]

# ❌ INCORRECT - Using convenience imports
from agent_will_smith.agent import Agent  # Relies on __init__.py exports
```

**Why this matters:**
- **Explicit is better than implicit**: Import paths show exactly where code comes from
- **No hidden dependencies**: Readers can trace imports directly to source files
- **Prevents circular imports**: Empty `__init__.py` files eliminate a common source of import cycles
- **IDE support**: Auto-complete and go-to-definition work better with explicit imports

## Dependency Injection

### Singleton Management
**Rule:** Only `src/main.py` can have global singletons. All other modules MUST use dependency injection.

```python
# ✅ CORRECT - In DI Container
class Container(containers.DeclarativeContainer):
    agent_config: providers.Provider[AgentConfig] = providers.Singleton(
        AgentConfig
    )

# ❌ INCORRECT - Raw global
agent_config = AgentConfig()  # FORBIDDEN outside main.py
```

### Logger Injection
**Rule:** Use `structlog.get_logger(__name__)` directly in class `__init__`. Don't use dependency injection for loggers. Don't use global module-level loggers.

```python
# ✅ CORRECT - Direct instantiation in __init__
class MyClass:
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        # rest of init

# ✅ CORRECT - In route handlers
async def endpoint():
    logger = structlog.get_logger(__name__)
    # rest of function

# ⚠️ ACCEPTABLE - Only in src/main.py for one-off functions
logger = structlog.get_logger(__name__)

# ❌ INCORRECT - Global module-level logger
logger = structlog.get_logger(__name__)  # At module level

# ❌ INCORRECT - DI injection
class MyClass:
    def __init__(self, logger: structlog.BoundLogger):  # Don't inject
        self.logger = logger
```

### Container Provider Patterns
**Rule:** Use correct provider types for different use cases

```python
# Singleton - Shared instance (configs, clients)
config: providers.Provider[Config] = providers.Singleton(Config)

# Factory - New instance each time (stateful objects)
service: providers.Provider[Service] = providers.Factory(create_service)
```

## API Route Organization

### Route Structure
**Rule:** Each feature/agent gets its own module under `src/app/api/`

```
src/app/api/
├── system/              # System-level routes (health, metrics)
│   ├── router.py        # FastAPI router with endpoints
│   └── dto/schemas.py   # Request/response models
└── product_recommendation/  # Feature-specific routes
    ├── router.py        # FastAPI router with endpoints
    └── dto/schemas.py   # Request/response models
```

## Exception Handling

### Core Philosophy

**All exceptions MUST bubble to the global exception handler in `src/main.py`.**

This architecture provides a single source of truth for:
- HTTP status code mapping
- Error response formatting
- Centralized logging with trace IDs
- Consistent error context for debugging

Benefits:
- **Consistency**: All API errors follow the same structure
- **Debuggability**: Full stack traces and structured details in one place
- **Maintainability**: Change error handling logic in one location
- **No Silent Failures**: All errors are visible and logged

### Rule 1: Use Only Predefined Exceptions

**Rule:** All code MUST use exceptions from `src/core/exceptions.py`. Never create custom exceptions or use generic Python exceptions.

```python
from src.core.exceptions import BadRequestError, UpstreamError, UpstreamTimeoutError

# ✅ CORRECT - Use predefined exceptions
def search(query: str):
    if not query:
        raise BadRequestError("Query cannot be empty")

    try:
        return third_party_api.search(query)
    except ThirdPartyTimeout as e:
        raise UpstreamTimeoutError(
            "Search timed out",
            details={"provider": "third_party", "operation": "search"}
        ) from e

# ❌ INCORRECT - Custom or generic exceptions
def search(query: str):
    if not query:
        raise ValueError("Query empty")  # NO! Use BadRequestError

    try:
        return third_party_api.search(query)
    except ThirdPartyTimeout:
        raise Exception("Timeout")  # NO! Use UpstreamTimeoutError
```

### Rule 2: Try-Catch Only at Boundaries

**Rule:** Try-catch blocks are ONLY allowed in these three specific cases:

#### Case 1: Infrastructure Boundary Translation (Most Common)

Convert 3rd party exceptions to domain exceptions at the infrastructure layer.

```python
# ✅ CORRECT - Infrastructure layer (infra/vector_search.py)
class VectorSearchClient:
    def search(self, query: str):
        try:
            return self._databricks_client.similarity_search(query)
        except DatabricksTimeout as e:
            raise UpstreamTimeoutError(
                "Vector search timed out",
                details={
                    "provider": "databricks_vector_search",
                    "operation": "similarity_search",
                }
            ) from e
        except DatabricksException as e:
            raise UpstreamError(
                "Vector search failed",
                details={
                    "provider": "databricks_vector_search",
                    "operation": "similarity_search",
                    "error": str(e),
                }
            ) from e

# ❌ INCORRECT - Try-catch in business logic
async def recommend_products(article: str):
    try:
        return await agent.invoke(article)  # NO! Let it bubble
    except Exception:
        return []  # FORBIDDEN! Silent failure
```

#### Case 2: Explicit Partial Failure (Rare - Requires Justification)

When business requirements explicitly allow partial success.

```python
# ✅ CORRECT - With business justification and error tracking
async def search_all_verticals(verticals: list[str]):
    """Search multiple verticals. Partial failure is acceptable per requirements."""
    tasks = [search_vertical(v) for v in verticals]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    errors = {}
    products = {}

    for i, result in enumerate(results):
        vertical = verticals[i]
        if isinstance(result, Exception):
            # MUST log failure
            logger.error("vertical_search_failed", vertical=vertical, error=result)
            # MUST include in response
            errors[vertical] = f"{type(result).__name__}: {str(result)}"
            products[vertical] = []
        else:
            products[vertical] = result

    return {"products": products, "errors": errors}
```

**Requirements for partial failure handling:**
- MUST log all failures with full context
- MUST include error details in API response
- MUST document business justification in code comments
- MUST be approved in code review

#### Case 3: Resource Cleanup Only

```python
# ✅ CORRECT - Cleanup with automatic re-raise
async def process_with_connection():
    connection = await create_connection()
    try:
        return await process(connection)
    finally:
        await connection.close()  # Cleanup always runs
        # Exception automatically propagates

# ❌ INCORRECT - Cleanup with swallow
try:
    connection = await create_connection()
    return await process(connection)
except Exception:
    await connection.close()
    return None  # FORBIDDEN! Silent failure
```

### Rule 3: No Silent Catches

**Rule:** Never catch exceptions without re-raising or proper handling. Silent catches hide production issues and make debugging impossible.

```python
# ❌ FORBIDDEN Pattern 1: Empty except block
try:
    critical_operation()
except Exception:
    pass  # FORBIDDEN! Hides all errors

# ❌ FORBIDDEN Pattern 2: Catch and return default
try:
    return fetch_user_data(user_id)
except Exception:
    return None  # FORBIDDEN! Caller doesn't know about failure

# ❌ FORBIDDEN Pattern 3: Log and swallow
try:
    send_notification(message)
except Exception as e:
    logger.error("notification_failed", error=e)
    # FORBIDDEN! Logged but not propagated, user thinks it succeeded

# ✅ CORRECT - Let it bubble
def fetch_user_data(user_id: str):
    return database.get_user(user_id)  # No try-catch, exceptions bubble

# ✅ CORRECT - Convert at boundary
def fetch_user_data(user_id: str):
    try:
        return database.get_user(user_id)
    except DatabaseTimeout as e:
        raise UpstreamTimeoutError(
            "Database query timed out",
            details={"operation": "get_user", "user_id": user_id}
        ) from e  # Convert and re-raise
```

### Rule 4: Exception Chaining Mandatory

**Rule:** Always use `raise ... from e` when converting exceptions. This preserves the original stack trace for debugging.

```python
# ✅ CORRECT - Preserves full stack trace
try:
    result = third_party_api.call()
except ThirdPartyError as e:
    raise UpstreamError(
        "API call failed",
        details={"provider": "third_party", "operation": "call"}
    ) from e  # 'from e' preserves original exception

# ❌ INCORRECT - Loses original stack trace
try:
    result = third_party_api.call()
except ThirdPartyError as e:
    raise UpstreamError("API call failed", details={...})  # Missing 'from e'
    # Stack trace only shows this line, not the original error location
```

**Why this matters:**
- Debugging: See the full chain of what went wrong
- Root cause analysis: Understand where the problem originated
- Stack traces: Get complete context from 3rd party libraries

### Rule 5: Retry Logic at Infrastructure Only

**Rule:** Retry logic ONLY belongs at infrastructure boundaries. Never retry in business logic or route handlers.

```python
# ✅ CORRECT - Infrastructure layer handles retries
class VectorSearchClient:
    def search(self, query: str, max_retries: int = 3) -> list:
        """Search with automatic retry for transient failures."""
        for attempt in range(max_retries):
            try:
                return self._databricks_client.search(query)
            except TransientError as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise UpstreamError(
                        "Vector search failed after retries",
                        details={
                            "provider": "databricks_vector_search",
                            "operation": "search",
                            "attempts": max_retries,
                        }
                    ) from e
                # Exponential backoff
                time.sleep(2 ** attempt)

# ❌ INCORRECT - Retry in business logic
async def recommend_products(article: str):
    for attempt in range(3):  # NO! Business logic shouldn't retry
        try:
            return await agent.invoke(article)
        except Exception:
            if attempt == 2:
                raise
            continue  # FORBIDDEN! Retrying at wrong layer

# ❌ INCORRECT - Retry in route handler
@router.post("/recommend")
async def endpoint(body: Request):
    for attempt in range(3):  # NO! Route handlers shouldn't retry
        try:
            return await agent.invoke(body.article)
        except Exception:
            continue
```

**Why infrastructure layer owns retries:**
- **Domain knowledge**: Infrastructure knows which errors are transient
- **Configuration**: Retry policy (attempts, backoff) per service
- **Consistent behavior**: All callers benefit from retry logic
- **Monitoring**: Centralized metrics on retry attempts

### Rule 6: Use Correct Exception Types

**Rule:** Use the exception type that matches the failure category. Misusing types breaks HTTP semantics and confuses clients.

#### Decision Tree for Choosing Exception Type

1. **Is it user input issue?** (Wrong request, missing field, invalid format)
   → Use **Client Error (4xx)**: `BadRequestError`, `DomainValidationError`, `UnauthorizedError`, `ForbiddenError`, `NotFoundError`

2. **Is it external service failure?** (Databricks, LLM, MLflow down/timeout)
   → Use **Upstream Error (5xx)**: `UpstreamError`, `UpstreamTimeoutError`, `UpstreamRateLimitError`

3. **Is it internal agent logic issue?** (State error, tool failure, timeout)
   → Use **Agent/Runtime Error**: `AgentStateError`, `ToolExecutionError`, `AgentTimeoutError`

4. **Unsure?** → Ask in code review

#### Common Misuse Patterns

```python
# ❌ INCORRECT - Misusing exception types
def search(query: str):
    # User input validation - should be 4xx
    if not query:
        raise UpstreamError("Query empty")  # NO! This is BadRequestError (4xx)

    # External service failure - should be 5xx
    try:
        return databricks.search(query)
    except DatabricksError as e:
        raise BadRequestError("Search failed")  # NO! This is UpstreamError (5xx)

# ✅ CORRECT - Proper exception types
def search(query: str):
    # User input validation → Client error (4xx)
    if not query:
        raise BadRequestError(
            "Query cannot be empty",
            details={"field": "query", "constraint": "non_empty"}
        )

    # External service failure → Upstream error (5xx)
    try:
        return databricks.search(query)
    except DatabricksError as e:
        raise UpstreamError(
            "Vector search service failed",
            details={
                "provider": "databricks_vector_search",
                "operation": "search",
                "error": str(e),
            }
        ) from e
```

#### Exception Type Examples

**Client Errors (4xx) - User Can Fix:**
```python
# Missing required field
raise BadRequestError("Article cannot be empty")

# Domain constraint violated
raise DomainValidationError(
    "Prompt exceeds maximum length",
    details={"max_length": 10000, "actual_length": 15000}
)

# Not authenticated
raise UnauthorizedError("Invalid or expired token")

# No permission
raise ForbiddenError("User lacks permission for this resource")

# Resource doesn't exist
raise NotFoundError("User not found", details={"user_id": user_id})
```

**Upstream Errors (5xx) - External Service Issues:**
```python
# External service failed
raise UpstreamError(
    "Databricks vector search failed",
    details={"provider": "databricks", "operation": "search"}
)

# External service timeout
raise UpstreamTimeoutError(
    "LLM request timed out",
    details={"provider": "databricks_llm", "timeout_seconds": 30}
)

# External rate limited
raise UpstreamRateLimitError(
    "MLflow rate limit exceeded",
    details={"provider": "mlflow", "retry_after": 60}
)
```

**Agent/Runtime Errors - Internal Logic:**
```python
# Invalid state transition
raise AgentStateError(
    "Cannot execute workflow in current state",
    details={"current_state": "paused", "expected_state": "running"},
    conflict=False  # Programming error, not user-resolvable
)

# Tool execution failed
raise ToolExecutionError(
    "Intent analysis tool failed",
    details={"tool_name": "intent_analysis", "is_external": False}
)
```

### Rule 7: Include Structured Details

**Rule:** All exceptions MUST include structured debugging context in the `details` dictionary.

```python
# ✅ CORRECT - Rich structured details
raise UpstreamError(
    "Vector search failed",
    details={
        "provider": "databricks_vector_search",
        "operation": "similarity_search",
        "index_name": "products_index",
        "query_length": len(query),
        "timeout_seconds": 30,
        "error": str(original_error),
    }
)

# ❌ INCORRECT - No details
raise UpstreamError("Search failed")  # Too vague for debugging!

# ❌ INCORRECT - Details as string instead of dict
raise UpstreamError(
    "Search failed",
    details="provider=databricks"  # NO! Must be dict
)
```

**Required details by exception type:**

| Exception Type | Required Details |
|---------------|------------------|
| `UpstreamError` / `UpstreamTimeoutError` | `provider`, `operation` |
| `ToolExecutionError` | `tool_name`, `is_external` |
| `DomainValidationError` | Validation constraint info |
| `NotFoundError` | Resource type, identifier |
| `RateLimitedError` | `retry_after` (if available) |

### Exception Hierarchy Quick Reference

| Exception | Status | Use When | Required Details |
|-----------|--------|----------|------------------|
| **Client Errors (4xx)** | | | |
| `BadRequestError` | 400 | Request semantically invalid | Context of validation failure |
| `UnauthorizedError` | 401 | Authentication failed | - |
| `ForbiddenError` | 403 | Authorization failed | Resource, action attempted |
| `NotFoundError` | 404 | Resource doesn't exist | Resource type, identifier |
| `AgentCancelledError` | 408 | User cancelled operation | - |
| `ConflictError` | 409 | Concurrency/idempotency conflict | Conflicting operation |
| `DomainValidationError` | 422 | Domain constraint violated | Constraint, actual value |
| `RateLimitedError` | 429 | App rate limit exceeded | `retry_after` (optional) |
| **Agent/Runtime Errors** | | | |
| `AgentStateError` | 409/500 | Invalid state transition | Current state, expected state |
| `ToolExecutionError` | 502/500 | Tool execution failed | `tool_name`, `is_external` |
| `AgentTimeoutError` | 504 | Agent execution timed out | `timeout_seconds` |
| **Upstream Errors (5xx)** | | | |
| `UpstreamError` | 502 | External service failed | `provider`, `operation` |
| `UpstreamTimeoutError` | 504 | External service timeout | `provider`, `operation`, `timeout_seconds` |
| `UpstreamRateLimitError` | 429 | External service rate limited | `provider`, `retry_after` (optional) |

## Configuration Management

### Core Philosophy

**All configuration MUST follow 12-factor app principles with namespace isolation for multi-agent systems.**

This architecture provides:
- **Namespace isolation**: Multiple agents can have identical config names without conflicts
- **Clear ownership**: `CORE_*` vs `AGENT_*` prefixes make ownership obvious
- **Consistency**: All configs use same patterns across the codebase
- **12-Factor compliance**: Granular, orthogonal environment variables
- **Scalability**: Easy to add new agents following established patterns

Benefits:
- **No Conflicts**: Agent A and Agent B can both have `LLM_ENDPOINT` without collision
- **Discoverability**: Operators can reason about which config belongs to which component
- **Environment Parity**: Same config structure across dev/staging/prod
- **Type Safety**: Pydantic BaseSettings provides validation at startup

### Rule 1: Use env_prefix for All Configs

**Rule:** All Pydantic config classes MUST use `env_prefix` to namespace environment variables.

#### Naming Convention: Three-Tier Namespacing

```
[SCOPE]_[COMPONENT]_[SETTING]

Where:
- SCOPE: CORE | AGENT
- COMPONENT: Feature/service name (uppercase snake_case)
- SETTING: Specific configuration field
```

**Core Infrastructure Prefixes:**
```python
CORE_DATABRICKS_*    # Databricks workspace & auth
CORE_MLFLOW_*        # MLFlow tracking & registry
CORE_FASTAPI_*       # API server settings
CORE_LOG_*           # Logging configuration
```

**Agent-Specific Prefixes:**
```python
AGENT_<NAME>_*       # Per-agent configuration

Examples:
AGENT_PRODUCT_RECOMMENDATION_*
AGENT_CONTENT_MODERATION_*
AGENT_SENTIMENT_ANALYSIS_*
```

#### Configuration Class Pattern

```python
# ✅ CORRECT - Core infrastructure config
class DatabricksConfig(BaseSettings):
    """Databricks workspace configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CORE_DATABRICKS_",     # Required
        case_sensitive=False,               # Required
    )

    # Field names WITHOUT prefix (Pydantic strips it automatically)
    host: str = Field(..., description="Databricks workspace URL")
    client_id: Optional[str] = Field(None, description="OAuth client ID")
    client_secret: Optional[str] = Field(None, description="OAuth client secret")

# ✅ CORRECT - Agent-specific config
class ProductRecommendationAgentConfig(BaseSettings):
    """Configuration for product recommendation agent."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AGENT_PRODUCT_RECOMMENDATION_",  # Required
        case_sensitive=False,                         # Required
        extra="ignore",                               # Required for agents
    )

    # LLM Configuration
    llm_endpoint: str = Field(..., description="Databricks LLM endpoint name")
    llm_temperature: float = Field(default=1.0, description="LLM temperature", ge=0.0, le=2.0)
    llm_max_tokens: int = Field(..., description="Max tokens for LLM response")

# ❌ INCORRECT - No env_prefix
class BadConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Missing env_prefix - will cause conflicts!
    )

    llm_endpoint: str  # Collides with other agents

# ❌ INCORRECT - Inconsistent settings
class InconsistentConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AGENT_FOO_",
        # Missing case_sensitive=False - inconsistent with other configs
    )
```

### Rule 2: Environment Variable Mapping

**Rule:** Environment variables map to config fields automatically. Field names are WITHOUT the prefix.

```python
# Config class
class ProductRecommendationAgentConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGENT_PRODUCT_RECOMMENDATION_",
    )

    llm_endpoint: str      # Field name (no prefix)
    llm_temperature: float

# .env file
AGENT_PRODUCT_RECOMMENDATION_LLM_ENDPOINT=databricks-gpt-5-mini
AGENT_PRODUCT_RECOMMENDATION_LLM_TEMPERATURE=1.0

# ✅ Pydantic automatically strips prefix:
# llm_endpoint = "databricks-gpt-5-mini"
# llm_temperature = 1.0

# ❌ INCORRECT - Including prefix in field name
class BadConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGENT_FOO_",
    )

    agent_foo_llm_endpoint: str  # NO! Field should be just 'llm_endpoint'
```


### Rule 3: Shared vs Agent-Specific Configuration

**Rule:** Infrastructure shared by ALL agents goes in `CORE_*`. Per-agent settings go in `AGENT_<NAME>_*`.

#### Decision Tree

1. **Is it used by multiple agents?** (Databricks auth, MLFlow tracking, API server)
   → Use **`CORE_*`** prefix

2. **Is it specific to one agent?** (LLM endpoint, vector indices, prompts, agent behavior)
   → Use **`AGENT_<NAME>_`** prefix

3. **Unsure?** → Default to agent-specific. It's easier to share later than to split.

#### Examples

```bash
# ✅ CORE - Shared infrastructure
CORE_DATABRICKS_HOST=https://workspace.databricks.com      # Used by all agents
CORE_DATABRICKS_CLIENT_ID=client-id                        # Shared auth
CORE_MLFLOW_TRACKING_URI=databricks                        # Shared tracking
CORE_FASTAPI_PORT=8000                                     # One API server

# ✅ AGENT-SPECIFIC - Per-agent settings
AGENT_PRODUCT_RECOMMENDATION_LLM_ENDPOINT=gpt-4           # May differ per agent
AGENT_PRODUCT_RECOMMENDATION_VECTOR_SEARCH_ENDPOINT=...   # Agent-specific index
AGENT_PRODUCT_RECOMMENDATION_PROMPT_NAME=...              # Agent-specific prompt

AGENT_CONTENT_MODERATION_LLM_ENDPOINT=claude-3            # Different model
AGENT_CONTENT_MODERATION_VECTOR_SEARCH_ENDPOINT=...       # Different index

# ❌ INCORRECT - Agent-specific in CORE
CORE_LLM_ENDPOINT=gpt-4  # NO! Different agents may need different models

# ❌ INCORRECT - Shared in AGENT
AGENT_PRODUCT_RECOMMENDATION_DATABRICKS_HOST=...  # NO! Should be CORE_DATABRICKS_HOST
```

### Rule 4: Agent Configs Must Inherit BaseAgentConfig

**Rule:** All agent-specific config classes MUST inherit from `BaseAgentConfig` instead of `BaseSettings`.

```python
# ✅ CORRECT - Inherit from BaseAgentConfig
from src.agent_will_smith.core.config.base_agent_config import BaseAgentConfig

class ProductRecommendationAgentConfig(BaseAgentConfig):
    """Configuration for product recommendation agent."""

    model_config = SettingsConfigDict(
        env_prefix="AGENT_PRODUCT_RECOMMENDATION_",
        # ... other settings
    )

    # Agent-specific fields only
    llm_endpoint: str
    prompt_name: str

# ❌ INCORRECT - Direct BaseSettings inheritance
from pydantic_settings import BaseSettings

class ProductRecommendationAgentConfig(BaseSettings):
    # Missing: agent_name, agent_version, prompt_cache_ttl
```

**Why this matters:**
- **Consistency**: All agents have standard identity fields
- **Version tracking**: Enforces semver format for agent versions
- **Prompt caching**: Unified cache configuration across all agents

## MLflow Tracing

### Rule 1: All Agents Must Set MLflow Trace Tags

**Rule:** Every agent's `invoke()` method MUST call `mlflow.update_current_trace()` with `agent_name` and `agent_version` tags from `BaseAgentConfig`.

This ensures all MLflow traces are properly tagged for:
- **Trace identification**: Know which agent generated each trace
- **Version tracking**: Correlate traces with specific agent versions
- **Debugging**: Filter traces by agent name and version in MLflow UI

```python
# ✅ CORRECT - Set MLflow tags in invoke()
class Agent:
    def __init__(self, ..., agent_config: ProductRecommendationAgentConfig):
        self.agent_config = agent_config

    @mlflow.trace(name="product_recommendation_agent")
    async def invoke(self, ...) -> AgentOutput:
        # Add agent metadata to MLflow trace
        mlflow.update_current_trace(
            tags={
                "agent_name": self.agent_config.agent_name,
                "agent_version": self.agent_config.agent_version,
            }
        )
        # ... rest of invoke

# ❌ INCORRECT - No MLflow tags
class Agent:
    @mlflow.trace(name="product_recommendation_agent")
    async def invoke(self, ...) -> AgentOutput:
        # Missing mlflow.update_current_trace() - cannot identify which agent/version
        # ... rest of invoke
```

**Why this matters:**
- **Observability**: Filter traces by agent name in MLflow UI
- **Version debugging**: Identify which agent version produced specific behavior
- **Performance analysis**: Compare performance across agent versions
- **Production debugging**: Quickly find traces from specific agent deployments

**Required tags:**
| Tag | Source | Description |
|-----|--------|-------------|
| `agent_name` | `agent_config.agent_name` | Agent identifier from BaseAgentConfig |
| `agent_version` | `agent_config.agent_version` | Semver version from BaseAgentConfig |

## LangGraph State Schema Conventions

### Core Philosophy

**All LangGraph agents MUST use namespace-based state architecture for clear ownership and type safety.**

This architecture provides:
- **Clear ownership**: Each node owns its namespace - no accidental mutations
- **Type safety**: Pydantic objects throughout workflow, dicts only at API boundary
- **Scalability**: Dynamic keys (dict) for extensible collections
- **Explicit dependencies**: Fail-fast validation when namespaces are missing

### Rule 1: Node-Based Namespacing

**Rule:** Every node gets its own sub-model namespace in `AgentState`.

```python
# ✅ CORRECT - Namespaced state structure
class AgentState(BaseModel):
    input: AgentInput                            # API input DTO (dual purpose!)
    intent_node: Optional[IntentNodeNamespace] = None
    search_node: Optional[SearchNodeNamespace] = None
    output: Optional[AgentOutput] = None         # API output DTO (dual purpose!)

# ❌ INCORRECT - Flat state (unclear ownership)
class AgentState(BaseModel):
    article: str
    question: str
    intent: str | None = None           # Who writes this?
    activities: list[dict] = []         # Which node owns this?
    grouped_results: dict = {}          # When is this set?
```

**Namespace model structure:**
```python
class SearchNodeNamespace(BaseModel):
    """
    Namespace: search_node
    Owner: ParallelSearchNode
    Lifecycle: Written once by parallel_search_node
    """
    results: dict[VERTICALS, list[ProductResult]]
    status: Literal["complete", "partial"] = "complete"
    errors: dict[str, str] = Field(default_factory=dict)
```

### Rule 2: Write Ownership

**Rule:** Nodes can only WRITE to their own namespace. Nodes can READ from any namespace.

```python
# ✅ CORRECT - Node writes to own namespace
class IntentAnalysisNode:
    def __call__(self, state: AgentState) -> dict:
        # Read from any namespace
        article = state.input.article

        # Write ONLY to own namespace
        return {
            "intent_node": IntentNodeNamespace(intent=result)
        }

# ❌ INCORRECT - Writing to another node's namespace
class IntentAnalysisNode:
    def __call__(self, state: AgentState) -> dict:
        return {
            "search_node": SearchNodeNamespace(...)  # FORBIDDEN!
        }
```

**Convention:** Node name matches namespace name:
- `IntentAnalysisNode` → `intent_node` namespace
- `ParallelSearchNode` → `search_node` namespace

### Rule 3: Pydantic Throughout

**Rule:** Keep Pydantic models throughout the workflow. Only convert to dict at API boundary.

```python
# ✅ CORRECT - Pydantic objects in state
class SearchNodeNamespace(BaseModel):
    results: dict[VERTICALS, list[ProductResult]]  # Type-safe!

# Access with type safety
for product in state.search_node.results["activities"]:
    score = product.relevance_score  # ✅ IDE autocomplete works

# ❌ INCORRECT - Convert to dict in state
class SearchNodeNamespace(BaseModel):
    results: dict[VERTICALS, list[dict]]  # Lost type safety!

# Access with string keys (error-prone)
score = product["relevance_score"]  # ❌ No autocomplete, typo risk
```

**API boundary conversion:**
```python
# ✅ CORRECT - Convert to dict only in OutputNode
class OutputNode:
    def __call__(self, state: AgentState) -> dict:
        # State has Pydantic objects throughout workflow
        search_results = state.search_node.results  # dict[VERTICALS, list[ProductResult]]

        # Convert ProductResult → dict (ONLY place in codebase!)
        grouped_dicts = {
            vertical: [p.model_dump() for p in products]
            for vertical, products in search_results.items()
        }

        # Write AgentOutput DTO with dict results
        return {"output": AgentOutput(grouped_results=grouped_dicts)}

# Agent invoke() returns the DTO directly
async def invoke(input_dto: AgentInput) -> AgentOutput:
    output_dict = await self.graph.ainvoke(AgentState(input=input_dto))
    return AgentOutputState(**output_dict).output  # Returns AgentOutput DTO
```

### Rule 4: Namespace Naming Convention

**Rule:** Follow consistent naming patterns for namespaces.

| Namespace | Format | Example | Owner | Notes |
|-----------|--------|---------|-------|-------|
| Input DTO | `input` | `input: AgentInput` | Agent (from API) | Dual-purpose: DTO + namespace |
| Output DTO | `output` | `output: Optional[AgentOutput]` | OutputNode | Dual-purpose: DTO + namespace |
| Node output | `{node_name}_node` | `intent_node: Optional[IntentNodeNamespace]` | Specific node | Internal namespace only |

```python
# ✅ CORRECT - Consistent naming
class AgentState(BaseModel):
    input: AgentInput                            # Singular! Dual-purpose DTO
    intent_node: Optional[IntentNodeNamespace]   # {node_name}_node
    search_node: Optional[SearchNodeNamespace]
    output: Optional[AgentOutput]                # Singular! Dual-purpose DTO

# ❌ INCORRECT - Inconsistent naming
class AgentState(BaseModel):
    inputs: InputsNamespace            # Should be 'input' (singular)
    input_data: AgentInput             # Should be 'input'
    intent: IntentNamespace            # Missing '_node' suffix
    search_results: SearchNamespace    # Should be 'search_node'
    outputs: AgentOutput               # Should be 'output' (singular)
```

### Rule 5: Dual-Purpose DTOs for Input/Output

**Rule:** `AgentInput` and `AgentOutput` serve two distinct purposes:
1. **API boundary DTOs**: Type annotations for `agent.invoke(input_dto) -> AgentOutput`
2. **State namespace models**: Live directly in `state.input` and `state.output`

This eliminates conversion overhead and simplifies the architecture.

```python
# ✅ CORRECT - Dual-purpose DTOs
class AgentInput(BaseModel):
    """Input DTO AND namespace model (dual purpose).

    Used for:
    1. agent.invoke() parameter type (API boundary)
    2. state.input namespace (internal state)
    """
    article: str
    question: str
    k: int
    verticals: list[VERTICALS]

class AgentOutput(BaseModel):
    """Output DTO AND namespace model (dual purpose).

    Used for:
    1. agent.invoke() return type (API boundary)
    2. state.output namespace (internal state)
    """
    grouped_results: dict[str, list[dict]]
    total_products: int
    status: Literal["complete", "partial"]

# Agent usage - no conversion needed!
async def invoke(self, input_dto: AgentInput) -> AgentOutput:
    # Create state directly with DTO (dual purpose!)
    initial_state = AgentState(input=input_dto)

    # Run graph
    output_dict = await self.graph.ainvoke(initial_state)

    # Return DTO directly from state
    return AgentOutputState(**output_dict).output

# ❌ INCORRECT - Separate DTO and namespace models
class AgentInput(BaseModel):
    """API DTO only"""
    article: str

class InputsNamespace(BaseModel):
    """Separate internal model"""
    article: str

async def invoke(self, input_dto: AgentInput) -> AgentOutput:
    # FORBIDDEN! Unnecessary conversion
    initial_state = AgentState(
        inputs=InputsNamespace(**input_dto.model_dump())
    )
```

**Benefits:**
- **No conversion overhead**: DTOs flow directly into state
- **Single source of truth**: One model for both API and state
- **Simplified code**: No InputsNamespace ↔ AgentInput mappings
- **Type safety**: Same validation at API and state level

### Rule 6: LangGraph Input/Output State Schemas

**Rule:** LangGraph StateGraph requires `input_schema` and `output_schema` to validate and filter state fields. Create thin wrapper schemas that reference the dual-purpose DTOs.

```python
# ✅ CORRECT - Thin state schemas for LangGraph
class AgentInputState(BaseModel):
    """Input schema for LangGraph - declares which fields are inputs."""
    input: AgentInput  # References the dual-purpose DTO

class AgentOutputState(BaseModel):
    """Output schema for LangGraph - declares which fields are outputs."""
    output: AgentOutput  # References the dual-purpose DTO

# Configure StateGraph
workflow = StateGraph(
    AgentState,
    input_schema=AgentInputState,   # Validates input field exists
    output_schema=AgentOutputState,  # Returns only output field
)

# ❌ INCORRECT - Flattening fields to top-level
class AgentInputState(BaseModel):
    """Don't flatten - breaks namespace architecture!"""
    article: str
    question: str
    k: int
```

**Why separate schemas:**
- **Namespace preservation**: Keep namespaced architecture intact
- **LangGraph validation**: Framework validates input/output fields exist
- **Filtered output**: LangGraph returns only output field (via output_schema)
- **Clear contracts**: Explicit declaration of what flows in/out

**Schema relationship:**
```
AgentState (full state)
├── input: AgentInput          ← Declared in AgentInputState
├── intent_node: ...           ← Internal, not in input/output schemas
├── search_node: ...           ← Internal, not in input/output schemas
└── output: AgentOutput        ← Declared in AgentOutputState
```

### Rule 7: Output Node is Special

**Rule:** The OutputNode is unique - it's the ONLY node that writes a DTO (not an internal namespace model) to state.

```python
# ✅ CORRECT - OutputNode writes AgentOutput DTO directly
class OutputNode:
    """Output node that writes AgentOutput DTO to state.output."""

    def __call__(self, state: AgentState) -> dict:
        # Read from internal namespaces
        verticals = state.input.verticals  # Singular!
        search_results = state.search_node.results

        # Compose and transform data
        grouped_results_pydantic: dict[VERTICALS, list[ProductResult]] = {}
        for vertical in verticals:
            products = search_results.get(vertical, [])
            sorted_products = sorted(products, key=lambda p: p.relevance_score, reverse=True)
            grouped_results_pydantic[vertical] = sorted_products[:state.input.k]

        # Convert ProductResult → dict (ONLY place in codebase!)
        grouped_results_dict = {
            vertical: [p.model_dump() for p in products]
            for vertical, products in grouped_results_pydantic.items()
        }

        # Write AgentOutput DTO to output namespace (SPECIAL!)
        return {
            "output": AgentOutput(
                grouped_results=grouped_results_dict,
                total_products=sum(len(p) for p in grouped_results_pydantic.values()),
                status=state.search_node.status,
            )
        }

# ❌ INCORRECT - Writing internal namespace model
class OutputNode:
    def __call__(self, state: AgentState) -> dict:
        return {
            "output_node": OutputNodeNamespace(...)  # NO! Should write DTO
        }
```

**Why OutputNode is special:**
- **API boundary**: Bridges internal state to API response
- **Single transformation point**: Only place where Pydantic → dict conversion happens
- **DTO writer**: Unlike other nodes, writes DTO directly to state
- **No intermediate namespace**: Skips OutputNodeNamespace pattern

**Pattern comparison:**

| Node Type | Writes To | Model Type | Purpose |
|-----------|-----------|------------|---------|
| IntentAnalysisNode | `intent_node` | `IntentNodeNamespace` | Internal processing |
| ParallelSearchNode | `search_node` | `SearchNodeNamespace` | Internal processing |
| **OutputNode** | **`output`** | **`AgentOutput` (DTO!)** | **API boundary** |
