"""Product recommendation agent using LangChain.

Flow (3 steps, only Step 1 uses LLM):
    API Request (article, question, k)
      ↓
    STEP 1: Intent Analysis [LLM: databricks-gpt-5-mini]
      ├─ Load system prompt from MLflow (versioned, strict governance)
      ├─ LLM extracts user intent from question + article context
      └─ Output: Intent text (1-2 sentences)
      ↓
    STEP 2: Vector Search [No LLM - Managed by Databricks]
      ├─ Query: intent + article → Databricks embeds query (gte-large-en)
      ├─ Search activities index (k results by cosine similarity)
      ├─ Search books index (k results by cosine similarity)
      └─ Output: 2k products with relevance scores
      ↓
    STEP 3: Ranking [No LLM - Pure Python]
      ├─ Sort combined products by relevance_score (descending)
      ├─ Select top k from 2k candidates
      └─ Output: AgentResponse with top k products
      ↓
    API Response

Few things that needs to be considered or improved:
1. we probably only need one system prompt for now, with dynamic insertion of selected run time input. 
2. we only use LLM for intent analysis, actual product recommendation was based on vector search and simple score ranking
3. talk about the embedding storage could potentially grow inifnitely

Architecture: LangGraph-ready (typed schemas, pure tools, explicit state)
but keeps it simple until branching/loops needed.
"""

from databricks_langchain import ChatDatabricks
from langchain_core.messages import HumanMessage, SystemMessage
import mlflow
import structlog

from core.config import config
from agent.schemas import AgentResponse, ProductResult
from core.tools.vector_search import search_activities_direct, search_books_direct
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
    """Product recommendation agent - sequential flow.
    
    Flow:
    1. Analyze question → extract user intent
    2. Search vector indexes (activities + books) using intent + article
    3. Combine results → select top K by relevance
    4. Return structured response
    
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
    
    # CRITICAL: Load system prompt from MLflow (strict - no fallback)
    # If this fails, API returns 500 (proper governance - prompt MUST exist)
    # NOTE: Can consider fallback later, just not now cuz we're testing things
    system_prompt = load_prompt_from_registry(prompt_name=config.prompt_name)
    
    # Initialize LLM
    chat_model = ChatDatabricks(
        endpoint=config.llm_endpoint,
        temperature=1.0,  # Required for databricks-gpt-5-mini
    )
    
    # === STEP 1: Analyze Question for User Intent ===
    logger.info("step_1_analyzing_intent", trace_id=trace_id)
    
    intent_analysis_request = f"""Analyze this question to understand what the user is looking for:

Question: {question}

Article context: {article[:200]}...

Extract the key intent and topics the user is interested in. Be concise.
Respond with 1-2 sentences describing what the user wants."""
    
    try:
        intent_response = chat_model.invoke([
            SystemMessage(content=system_prompt),  # Use loaded prompt as system context
            HumanMessage(content=intent_analysis_request)
        ])
        user_intent = intent_response.content.strip()
        logger.info("intent_extracted", intent=user_intent, trace_id=trace_id)
    except Exception as e:
        logger.warning("intent_extraction_failed", error=str(e), trace_id=trace_id)
        user_intent = question  # Fallback to original question
    
    # === STEP 2: Search Vector Indexes ===
    logger.info("step_2_searching_indexes", trace_id=trace_id)
    
    # Combine intent + article for search query
    search_query = f"{user_intent}\n\n{article}"
    
    # Search strategy: Get k results from EACH index (activities + books)
    # Then select top k from the combined pool (2k total)
    # Example: k=3 → search 3 activities + 3 books → select top 3 from 6 total
    # This ensures we see both types before final ranking
    max_results_per_index = min(k, config.max_k_products)
    
    all_products = []
    activities_count = 0
    books_count = 0
    
    # Search activities (if not filtered out)
    if product_types is None or "activities" in product_types:
        try:
            activities_results = search_activities_direct(
                query=search_query,
                trace_id=trace_id,
                max_results=max_results_per_index
            )
            activities_count = len(activities_results)
            logger.info("activities_search_completed", 
                       count=activities_count,
                       trace_id=trace_id,
                       sample_titles=[r.get("title") for r in activities_results[:2]])
            all_products.extend(activities_results)
        except Exception as e:
            logger.error("activities_search_failed", error=str(e), trace_id=trace_id, exc_info=True)
    
    # Search books (if not filtered out)
    if product_types is None or "books" in product_types:
        try:
            books_results = search_books_direct(
                query=search_query,
                trace_id=trace_id,
                max_results=max_results_per_index
            )
            books_count = len(books_results)
            logger.info("books_search_completed", 
                       count=books_count,
                       trace_id=trace_id,
                       sample_titles=[r.get("title") for r in books_results[:2]])
            all_products.extend(books_results)
        except Exception as e:
            logger.error("books_search_failed", error=str(e), trace_id=trace_id, exc_info=True)
    
    total_searched = len(all_products)
    logger.info("total_products_found", 
               total=total_searched,
               activities=activities_count,
               books=books_count,
               trace_id=trace_id)
    
    # === STEP 3: Select Top K from Combined Results ===
    logger.info("step_3_selecting_top_k", total_products=total_searched, k=k, trace_id=trace_id)
    
    if not all_products:
        logger.warning("no_products_found", trace_id=trace_id)
        return AgentResponse(
            products=[],
            reasoning="No relevant products found in the search results.",
            total_searched=0
        )
    
    # Sort by relevance score (highest first)
    sorted_products = sorted(
        all_products,
        key=lambda x: x.get("relevance_score", 0.0),
        reverse=True
    )
    
    # Log sorting results
    top_5_preview = sorted_products[:5]
    logger.info("products_sorted",
               total=len(sorted_products),
               top_scores=[p.get("relevance_score") for p in top_5_preview],
               top_types=[p.get("product_type") for p in top_5_preview],
               trace_id=trace_id)
    
    # Take top K
    top_k_products = sorted_products[:k]
    logger.debug("selected_top_k",
                k=k,
                product_types=[p.get('product_type') for p in top_k_products],
                trace_id=trace_id)
    
    # Convert to ProductResult objects
    products = []
    for prod in top_k_products:
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
    
    # Generate reasoning
    product_types_str = ", ".join([p.product_type for p in products])
    reasoning = (
        f"Selected {len(products)} products based on semantic similarity to the article "
        f"and alignment with user intent: '{user_intent[:100]}...'. "
        f"Results include {product_types_str}."
    )
    
    logger.info(
        "agent_completed",
        trace_id=trace_id,
        products_count=len(products),
        total_searched=total_searched,
    )
    
    return AgentResponse(
        products=products,
        reasoning=reasoning,
        total_searched=total_searched
    )
