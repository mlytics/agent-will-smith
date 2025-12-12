"""Product recommendation agent implementation.

Follows guidelines:
- "One controller of flow" - agent runtime decides sequence
- "Keep orchestration out of tools and prompts"
- "Separation of decision roles from content roles"
- Uses LangChain v1 create_agent API for future LangGraph migration
"""

from databricks_langchain import ChatDatabricks
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
import mlflow
import structlog

from app.config import settings
from agent.schemas import AgentContext, AgentResponse
from core.tools.vector_search import search_activities, search_books

logger = structlog.get_logger(__name__)


@mlflow.trace
def recommend_products(
    article: str,
    question: str,
    k: int,
    trace_id: str,
    product_types: list[str] | None = None,
) -> AgentResponse:
    """Product recommendation agent using vector search and LangChain.

    This is the single flow controller for product recommendations.
    Orchestration happens here; tools execute work; prompts guide reasoning.

    Args:
        article: Original article text to analyze
        question: Selected question to guide recommendations
        k: Number of products to recommend (1-10)
        trace_id: Trace ID for observability
        product_types: Optional filter for product types (activities, books)

    Returns:
        Structured agent response with product recommendations
    """
    logger.info(
        "agent_started",
        trace_id=trace_id,
        article_length=len(article),
        question_length=len(question),
        k=k,
        product_types=product_types,
    )

    # Initialize LLM from Databricks
    chat_model = ChatDatabricks(
        endpoint=settings.llm_endpoint,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )

    # Checkpointer for conversation state (InMemorySaver for now)
    checkpointer = InMemorySaver()

    # Determine which tools to provide based on product_types filter
    tools = []
    if product_types is None or "activities" in product_types:
        tools.append(search_activities)
    if product_types is None or "books" in product_types:
        tools.append(search_books)

    if not tools:
        logger.warning("no_tools_available", trace_id=trace_id, product_types=product_types)
        # Return empty response if no tools available
        return AgentResponse(products=[], reasoning="No product types specified", total_searched=0)

    try:
        # Load prompt from MLFlow registry
        # NOTE: Loading after model init enables automatic lineage tracking
        system_prompt = mlflow.genai.load_prompt(settings.prompt_name)

        # Create agent with explicit configuration
        agent = create_agent(
            model=chat_model,
            system_prompt=system_prompt.format(),
            tools=tools,
            context_schema=AgentContext,
            response_format=ToolStrategy(AgentResponse),
            checkpointer=checkpointer,
        )

        # Create agent context (passed to tools via ToolRuntime)
        context = AgentContext(
            trace_id=trace_id,
            article=article,
            question=question,
            max_k=k,
            product_types=product_types,
        )

        # Invoke agent with budget constraints
        config = {
            "configurable": {
                "thread_id": trace_id,  # Use trace_id as thread_id for correlation
            },
            "recursion_limit": settings.max_agent_steps,
        }

        # Construct user message with article + question
        user_message = f"""
Article:
{article}

Question:
{question}

Please recommend {k} products (activities and/or books) that are most relevant to this article and question.
Analyze the article content and question carefully, then use the available search tools to find the best matches.
        """.strip()

        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config=config,
            context=context,
        )

        # Extract structured response
        structured_response: AgentResponse = response["structured_response"]

        logger.info(
            "agent_completed",
            trace_id=trace_id,
            products_count=len(structured_response.products),
            total_searched=structured_response.total_searched,
        )

        return structured_response

    except Exception as e:
        logger.error(
            "agent_failed",
            trace_id=trace_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise  # Re-raise for FastAPI error handling

