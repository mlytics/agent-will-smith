"""Product recommendation agent using LangGraph workflow.

Graph-based agent following the joke_agent pattern.
"""

from typing import Optional
import uuid
import structlog
from langgraph.graph import StateGraph, START, END

from agent_will_smith.agent.product_recommendation.schemas import AgentState, AgentOutput
from agent_will_smith.agent.product_recommendation.node.intent_analysis_node import IntentAnalysisNode
from agent_will_smith.agent.product_recommendation.node.parallel_search_node import ParallelSearchNode
from agent_will_smith.agent.product_recommendation.node.compose_response_node import ComposeResponseNode


class Agent:
    """Graph-based agent for product recommendation workflow.

    Follows the joke_agent pattern:
    - Constructor receives injected node instances
    - Builds LangGraph workflow with nodes
    - invoke() method runs the workflow
    """

    def __init__(
        self,
        intent_analysis_node: IntentAnalysisNode,
        parallel_search_node: ParallelSearchNode,
        compose_response_node: ComposeResponseNode,
    ):
        """Initialize agent with injected node instances.

        Args:
            intent_analysis_node: Node for analyzing user intent
            parallel_search_node: Node for parallel vector search
            compose_response_node: Node for composing final response
        """
        self.logger = structlog.get_logger(__name__)

        # Build workflow graph
        workflow = StateGraph(AgentState)
        workflow.add_node("intent_analysis", intent_analysis_node)
        workflow.add_node("parallel_search", parallel_search_node)
        workflow.add_node("compose_response", compose_response_node)

        # Define flow
        workflow.add_edge(START, "intent_analysis")
        workflow.add_edge("intent_analysis", "parallel_search")
        workflow.add_edge("parallel_search", "compose_response")
        workflow.add_edge("compose_response", END)

        self.graph = workflow.compile()
        self.logger.info("product recommendation agent initialized")

    async def invoke(
        self,
        article: str,
        question: str,
        k: int,
        verticals: list[str],
        customer_uuid: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> AgentOutput:
        """Run the agent with the given inputs.

        Args:
            article: Article text to analyze
            question: Question to guide recommendations
            k: Number of products per vertical
            verticals: Which verticals to search
            customer_uuid: Optional customer UUID for filtering
            trace_id: Optional trace_id (auto-generates if None)

        Returns:
            AgentOutput with grouped results

        Note:
            This method is safe for concurrent API requests.
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        self.logger.info(
            "execution started",
            article_length=len(article),
            question_length=len(question),
            verticals=verticals,
            k=k,
            customer_uuid=customer_uuid,
        )

        initial_state = AgentState(
            article=article,
            question=question,
            k=k,
            verticals=verticals,
            trace_id=trace_id,
            customer_uuid=customer_uuid,
        )

        final_state_dict = await self.graph.ainvoke(initial_state)
        final_state = AgentState(**final_state_dict)

        self.logger.info(
            "execution completed",
            total_products=final_state.total_products,
            status=final_state.status,
        )

        return AgentOutput(
            grouped_results=final_state.grouped_results,
            total_products=final_state.total_products,
            status=final_state.status,
            errors=final_state.errors,
            intent=final_state.intent or "No intent provided",
        )
