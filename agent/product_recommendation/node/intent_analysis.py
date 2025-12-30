"""Intent analysis node for LangGraph workflow.

This node performs the ONLY LLM call in the workflow to analyze user intent.
The intent is used to enhance search query quality.

Architecture: Single LLM call, no multi-round reasoning.
"""

from databricks_langchain import ChatDatabricks
import structlog

from core.config import config
from agent.product_recommendation.config import agent_config
from agent.product_recommendation.schemas import AgentState, IntentAnalysisOutput
from agent.product_recommendation.infra.prompts import load_prompt_from_registry
from core.exceptions import IntentAnalysisError, LLMServiceError, LLMServiceTimeout

logger = structlog.get_logger(__name__)


def intent_analysis_node(state: AgentState) -> IntentAnalysisOutput:
    """Analyze intent with single LLM call.
    
    This is the ONLY LLM call in the workflow. It analyzes the article and question
    to extract intent, which will be used to enhance search queries.
    
    Args:
        state: Current workflow state
        
    Returns:
        dict with 'intent' key
        
    Raises:
        IntentAnalysisError: If intent analysis fails
        LLMServiceError: If LLM service has issues
        LLMServiceTimeout: If LLM call times out
    """
    trace_id = state.trace_id
    logger.info("intent_analysis_started", trace_id=trace_id)
    
    try:
        # Load system prompt from MLflow (returns PromptContent)
        prompt_content = load_prompt_from_registry()
        system_prompt = prompt_content.text
        logger.debug("intent_prompt_loaded", 
                    trace_id=trace_id, 
                    prompt_length=len(system_prompt),
                    prompt_source=prompt_content.source)
        
        # Initialize LLM
        llm = ChatDatabricks(
            endpoint=agent_config.llm_endpoint,
            temperature=agent_config.llm_temperature,
            max_tokens=300,  # Intent should be concise
        )
        logger.debug("llm_initialized", 
                    endpoint=agent_config.llm_endpoint,
                    trace_id=trace_id)
        
        # Construct user message
        # Truncate article to avoid token limits (keep first 1000 chars)
        article_excerpt = state.article[:1000]
        if len(state.article) > 1000:
            article_excerpt += "..."
            
        user_message = f"""Article: {article_excerpt}

Question: {state.question}

Please analyze the intent and key themes of this article and question. 
What is the user looking for? What are the main topics?
Provide a concise intent summary (2-3 sentences max)."""
        
        logger.info("intent_analysis_invoking_llm",
                   trace_id=trace_id,
                   article_length=len(article_excerpt),
                   question_length=len(state.question))
        
        # Single LLM call
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ])
        
        intent = response.content.strip()
        
        if not intent:
            raise IntentAnalysisError("LLM returned empty intent")
        
        logger.info("intent_analysis_completed", 
                   trace_id=trace_id, 
                   intent_length=len(intent))
        
        # Return validated Pydantic model directly (type-safe)
        return IntentAnalysisOutput(intent=intent)
        
    except TimeoutError as e:
        logger.error("intent_analysis_timeout", 
                    trace_id=trace_id, 
                    error=str(e))
        raise LLMServiceTimeout(f"Intent analysis timed out: {str(e)}") from e
        
    except Exception as e:
        logger.error("intent_analysis_failed", 
                    trace_id=trace_id, 
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True)
        
        # Check if it's an LLM service error
        error_msg = str(e).lower()
        if "endpoint" in error_msg or "service" in error_msg or "connection" in error_msg:
            raise LLMServiceError(f"LLM service error: {str(e)}") from e
        
        raise IntentAnalysisError(f"Intent analysis failed: {str(e)}") from e

