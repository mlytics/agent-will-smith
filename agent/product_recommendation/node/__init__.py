"""LangGraph nodes for product recommendation workflow.

Nodes are injectable classes following the joke_agent pattern:
- IntentAnalysisNode: Single LLM call to analyze intent
- ParallelSearchNode: Parallel vector search across all verticals
- ComposeResponseNode: Format grouped results (top K per vertical)

Also exports:
- build_search_query: Deterministic query construction (no LLM)
"""

from agent.product_recommendation.node.intent_analysis_node import IntentAnalysisNode
from agent.product_recommendation.node.parallel_search_node import ParallelSearchNode
from agent.product_recommendation.node.compose_response_node import ComposeResponseNode
from agent.product_recommendation.node.query_builder import build_search_query

__all__ = [
    "IntentAnalysisNode",
    "ParallelSearchNode",
    "ComposeResponseNode",
    "build_search_query",
]
