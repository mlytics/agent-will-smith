"""Product recommendation agent using LangChain Agent.

Flow:
    API Request → Agent analyzes → Calls tools → Returns structured response

Agent decides dynamically which tools to call (search_activities, search_books).
Tools receive AgentContext via ToolRuntime for state management.
"""

from databricks_langchain import ChatDatabricks
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import mlflow
import structlog

from core.config import config
from agent.schemas import AgentContext, AgentResponse, ProductResult
from core.tools import search_activities, search_books
from core.prompts.loader import load_prompt_from_registry

logger = structlog.get_logger(__name__)

@mlflow.trace
def recommend_products(
    article: str,
    question: str,
    k: int,
    trace_id: str,
    product_types: list[str] | None = None,
) -> AgentResponse:
    """Product recommendation agent.
    
    Agent analyzes article and question, decides which search tools to call,
    and returns ranked product recommendations.
    
    Args:
        article: Article text to analyze
        question: Question to guide recommendations
        k: Number of products to recommend (1-10)
        trace_id: Trace ID for observability
        product_types: Optional filter (activities, books)
        
    Returns:
        AgentResponse with products, reasoning, and total_searched
    """
    logger.info(
        "agent_started",
        trace_id=trace_id,
        article_length=len(article),
        question_length=len(question),
        k=k,
        product_types=product_types,
    )
    
    # Load system prompt from MLflow
    system_prompt_text = load_prompt_from_registry(prompt_name=config.prompt_name)
    logger.info("prompt_loaded", trace_id=trace_id, prompt_length=len(system_prompt_text))
    
    # Initialize LLM
    chat_model = ChatDatabricks(
        endpoint=config.llm_endpoint,
        temperature=config.llm_temperature,
    )
    logger.info("llm_initialized", endpoint=config.llm_endpoint, trace_id=trace_id)
    
    # Initialize checkpointer (stateless per request)
    checkpointer = InMemorySaver()
    
    # Select tools based on product type filter
    tools = []
    if product_types is None or "activities" in product_types:
        tools.append(search_activities)
        logger.info("tool_added", tool="search_activities", trace_id=trace_id)
    if product_types is None or "books" in product_types:
        tools.append(search_books)
        logger.info("tool_added", tool="search_books", trace_id=trace_id)
    
    if not tools:
        logger.warning("no_tools_available", product_types=product_types, trace_id=trace_id)
        return AgentResponse(
            products=[],
            reasoning="No product types requested for search.",
            total_searched=0
        )
    
    # Create context for tools (passed via ToolRuntime)
    context = AgentContext(
        trace_id=trace_id,
        article=article,
        question=question,
        max_k=k,
        product_types=product_types
    )
    logger.info("context_created", trace_id=trace_id)
    
    # Create agent (decides which tools to call)
    try:
        agent = create_agent(
            model=chat_model,
            system_prompt=system_prompt_text,
            tools=tools,
            context_schema=AgentContext,
            checkpointer=checkpointer,
        )
        logger.info("agent_created", tools_count=len(tools), trace_id=trace_id)
    except Exception as e:
        logger.error("agent_creation_failed", error=str(e), trace_id=trace_id, exc_info=True)
        raise
    
    # Construct user message
    user_message = f"""Article Content:
{article}

Question: {question}

Please analyze this article and question, then recommend the top {k} most relevant products.
Use the available search tools (search_activities and/or search_books) to find relevant products.
Consider the article's main topics and how they relate to the question.

Return your recommendations with clear reasoning."""
    
    # Invoke agent with explicit budget
    config_dict = {
        "configurable": {"thread_id": trace_id},
        "recursion_limit": config.max_agent_steps,
    }
    
    logger.info("agent_invoking", trace_id=trace_id, max_steps=config.max_agent_steps)
    
    try:
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config=config_dict,
            context=context,
        )
        logger.info("agent_completed", trace_id=trace_id)
    except Exception as e:
        logger.error("agent_invocation_failed", error=str(e), trace_id=trace_id, exc_info=True)
        return AgentResponse(
            products=[],
            reasoning=f"Agent failed to complete: {str(e)}",
            total_searched=0
        )
    
    # Parse agent response
    messages = response.get("messages", [])
    logger.info("response_received", messages_count=len(messages), trace_id=trace_id)
    
    # Extract tool call results from messages
    all_products_dict = {}  # Deduplicate by product_id
    total_searched = 0
    
    for msg in messages:
        if hasattr(msg, 'type') and msg.type == 'tool':
            tool_name = getattr(msg, 'name', 'unknown')
            logger.info("processing_tool_message", tool_name=tool_name, trace_id=trace_id)
            
            try:
                import json
                if isinstance(msg.content, str):
                    tool_results = json.loads(msg.content)
                else:
                    tool_results = msg.content
                
                if isinstance(tool_results, list):
                    for product_dict in tool_results:
                        if isinstance(product_dict, dict):
                            product_id = product_dict.get("product_id")
                            if product_id:
                                existing = all_products_dict.get(product_id)
                                if existing is None or product_dict.get("relevance_score", 0) > existing.get("relevance_score", 0):
                                    all_products_dict[product_id] = product_dict
                                    total_searched += 1
                    
                    logger.info("tool_results_parsed",
                               tool_name=tool_name,
                               products_count=len(tool_results),
                               trace_id=trace_id)
            except Exception as e:
                logger.error("tool_result_parse_failed",
                           tool_name=tool_name,
                           error=str(e),
                           trace_id=trace_id,
                           exc_info=True)
    
    all_products = list(all_products_dict.values())
    logger.info("all_products_collected",
               total_products=len(all_products),
               total_searched=total_searched,
               trace_id=trace_id)
    
    # Handle no results
    if not all_products:
        logger.warning("no_products_from_tools", trace_id=trace_id)
        final_message = messages[-1] if messages else None
        agent_reasoning = final_message.content if final_message and hasattr(final_message, 'content') else "No products found matching the criteria."
        return AgentResponse(
            products=[],
            reasoning=agent_reasoning,
            total_searched=total_searched
        )
    
    # Sort by relevance score and select top K
    sorted_products = sorted(
        all_products,
        key=lambda x: x.get("relevance_score", 0.0),
        reverse=True
    )
    logger.info("products_sorted",
               total=len(sorted_products),
               top_3_scores=[p.get("relevance_score") for p in sorted_products[:3]],
               trace_id=trace_id)
    
    top_k_products = sorted_products[:k]
    
    # Convert to ProductResult objects
    products = []
    for prod in top_k_products:
        try:
            products.append(
                ProductResult(
                    product_id=prod.get("product_id", "unknown"),
                    product_type=prod.get("product_type", "activity"),
                    title=prod.get("title", "Unknown"),
                    description=prod.get("description"),
                    relevance_score=prod.get("relevance_score", 0.0),
                    metadata=prod.get("metadata", {})
                )
            )
        except Exception as e:
            logger.error("product_result_creation_failed",
                        error=str(e),
                        product_dict=prod,
                        trace_id=trace_id,
                        exc_info=True)
    
    # Generate reasoning from agent's final message
    final_message = messages[-1] if messages else None
    if final_message and hasattr(final_message, 'content') and final_message.content:
        agent_reasoning = final_message.content
    else:
        product_types_found = set(p.product_type for p in products)
        agent_reasoning = (
            f"Agent searched and found {len(all_products)} relevant products. "
            f"Selected top {len(products)} products based on relevance scores. "
            f"Product types: {', '.join(product_types_found)}."
        )
    
    logger.info(
        "agent_finished",
        trace_id=trace_id,
        products_returned=len(products),
        total_searched=total_searched,
    )
    
    return AgentResponse(
        products=products,
        reasoning=agent_reasoning,
        total_searched=total_searched
    )
