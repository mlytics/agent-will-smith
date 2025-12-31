"""LLM client pooling for Databricks LLM endpoint.

Creates LLM client once at startup and reuses across all requests.
Thread-safe with double-checked locking.
"""

import threading
from databricks_langchain import ChatDatabricks
import structlog

from agent.product_recommendation.config import agent_config

logger = structlog.get_logger(__name__)


# Global LLM client pool (singleton pattern) - thread-safe
_llm_client_pool: ChatDatabricks | None = None
_llm_client_lock = threading.Lock()


def get_llm_client() -> ChatDatabricks:
    """Get or create LLM client singleton (connection pooling).
    
    Creates the LLM client once and reuses it across all requests.
    Thread-safe singleton pattern with double-checked locking.
    
    Note: Temperature is fixed at pool creation (agent_config.llm_temperature).
    All requests use the same temperature. This is appropriate for intent analysis
    which always needs the same temperature setting.
    
    Returns:
        Shared ChatDatabricks instance
    """
    global _llm_client_pool
    
    # Fast path: return existing client without lock (performance optimization)
    if _llm_client_pool is not None:
        return _llm_client_pool
    
    # Slow path: acquire lock and create client (thread-safe)
    with _llm_client_lock:
        # Double-check: another thread might have created it while we waited
        if _llm_client_pool is None:
            logger.info("creating_llm_client_pool",
                       endpoint=agent_config.llm_endpoint,
                       temperature=agent_config.llm_temperature)
            
            _llm_client_pool = ChatDatabricks(
                endpoint=agent_config.llm_endpoint,
                temperature=agent_config.llm_temperature,
                max_tokens=300,  # For intent analysis
            )
            
            logger.info("llm_client_pool_created",
                       endpoint=agent_config.llm_endpoint)
        
        return _llm_client_pool

