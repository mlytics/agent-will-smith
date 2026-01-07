# Code Guidelines & Review Rules

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

## Docker & Deployment

### Graceful Shutdown
**Rule:** All applications MUST handle SIGTERM/SIGINT for zero-downtime deployments

```python
def setup_signal_handlers(app: FastAPI) -> None:
    def signal_handler(sig, frame):
        logger.info("shutdown_signal_received", signal=signal.Signals(sig).name)
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
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

### Common Patterns

#### Pattern 1: Validation (Raise Directly)
```python
# ✅ CORRECT - No try-catch needed
def validate_input(prompt: str):
    if len(prompt) > MAX_LENGTH:
        raise DomainValidationError(
            "Prompt exceeds maximum length",
            details={"max": MAX_LENGTH, "actual": len(prompt)}
        )
    if not prompt.strip():
        raise BadRequestError("Prompt cannot be empty")
```

#### Pattern 2: Infrastructure Boundary with Retry
```python
# ✅ CORRECT - Retry at infrastructure layer
class LLMClient:
    def invoke(self, messages: list, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                return self._llm.invoke(messages)
            except LLMTimeout as e:
                if attempt == max_retries - 1:
                    raise UpstreamTimeoutError(
                        "LLM request timed out after retries",
                        details={
                            "provider": "databricks_llm",
                            "operation": "invoke",
                            "attempts": max_retries,
                        }
                    ) from e
                time.sleep(2 ** attempt)
            except LLMError as e:
                raise UpstreamError(
                    "LLM service error",
                    details={"provider": "databricks_llm", "error": str(e)}
                ) from e
```

#### Pattern 3: Resource Cleanup
```python
# ✅ CORRECT - Finally block with re-raise
async def process_batch(items: list):
    connection = await db.connect()
    try:
        results = []
        for item in items:
            results.append(await connection.process(item))
        return results
    finally:
        await connection.close()  # Always cleanup
        # Exception propagates automatically
```

### Common Mistakes to Avoid

❌ **Mistake 1: Misusing Exception Types**
```python
# Wrong: User input error as upstream error
if not query:
    raise UpstreamError("No query")  # Should be BadRequestError

# Wrong: External failure as client error
except DatabricksError:
    raise BadRequestError("Failed")  # Should be UpstreamError
```

❌ **Mistake 2: Silent Catches**
```python
try:
    send_email(user)
except:
    pass  # Email failure hidden from user!
```

❌ **Mistake 3: Missing Exception Chaining**
```python
except ThirdPartyError as e:
    raise UpstreamError("Failed")  # Missing 'from e' - loses stack trace
```

❌ **Mistake 4: Retry in Wrong Layer**
```python
# Route handler
async def endpoint():
    for i in range(3):  # Should be in infrastructure layer
        try:
            return await service.call()
        except:
            continue
```

❌ **Mistake 5: No Structured Details**
```python
raise UpstreamError("Search failed")  # No details for debugging
```

