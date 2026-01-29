"""Product recommendation agent using LangGraph workflow.

Graph-based agent following the joke_agent pattern.

Namespace Architecture:
- State is organized into namespaces per node
- Each node writes to its own namespace only
- Nodes read from any namespace
- ProductResult objects preserved throughout workflow
- Only converted to dict at API boundary
"""

import asyncio

import structlog
import mlflow
from langgraph.graph import StateGraph, START, END

from agent_will_smith.agent.product_recommendation.state import (
    AgentState,
    AgentInputState,
    AgentOutputState,
    AgentInput,
    AgentOutput,
)
from agent_will_smith.agent.product_recommendation.node.intent_analysis_node import IntentAnalysisNode
from agent_will_smith.agent.product_recommendation.node.parallel_search_node import ParallelSearchNode
from agent_will_smith.agent.product_recommendation.node.output_node import OutputNode
from agent_will_smith.agent.product_recommendation.config import Config
from agent_will_smith.core.exceptions import AgentTimeoutError, AgentStateError


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
        output_node: OutputNode,  # RENAMED from compose_response_node
        agent_config: Config,
    ):
        """Initialize agent with injected node instances.

        Args:
            intent_analysis_node: Node for analyzing user intent
            parallel_search_node: Node for parallel vector search
            output_node: Node for creating output DTO
            agent_config: Agent configuration for metadata and tracing
        """
        self.logger = structlog.get_logger(__name__)
        self.agent_config = agent_config

        # Build workflow graph with input/output schemas
        workflow = StateGraph(
            AgentState,
            input_schema=AgentInputState,   # NEW: Validates input field exists
            output_schema=AgentOutputState,  # NEW: Returns only output field
        )
        workflow.add_node("intent_analysis_node", intent_analysis_node)
        workflow.add_node("parallel_search_node", parallel_search_node)
        workflow.add_node("output_node", output_node)  # RENAMED

        # Define flow
        workflow.add_edge(START, "intent_analysis_node")
        workflow.add_edge("intent_analysis_node", "parallel_search_node")
        workflow.add_edge("parallel_search_node", "output_node")  # UPDATED
        workflow.add_edge("output_node", END)  # UPDATED

        self.graph = workflow.compile()
        self.logger.info("product recommendation agent initialized")

    @mlflow.trace(name="product_recommendation_agent")
    async def invoke(self, input_dto: AgentInput) -> AgentOutput:
        """Run the agent with the given input DTO.

        Args:
            input_dto: AgentInput with validated fields

        Returns:
            AgentOutput DTO with grouped results

        Note:
            This method is safe for concurrent API requests.
        """

        # Add agent metadata to MLflow trace
        mlflow.update_current_trace(
            tags={
                "agent_name": self.agent_config.agent_name,
                "agent_version": self.agent_config.agent_version,
            }
        )

        self.logger.info(
            "execution started",
            article_length=len(input_dto.article),
            question_length=len(input_dto.question),
            verticals=input_dto.verticals,
            k=input_dto.k,
        )

        # Create initial state with input namespace (singular!)
        # AgentInput serves dual purpose - no conversion needed!
        initial_state = AgentState(input=input_dto)

        # Run graph with timeout enforcement (LangGraph validates input/output schemas)
        try:
            output_state_dict = await asyncio.wait_for(
                self.graph.ainvoke(initial_state),
                timeout=self.agent_config.agent_timeout_seconds,
            )
        except asyncio.TimeoutError as e:
            self.logger.error(
                "agent execution timeout",
                timeout_seconds=self.agent_config.agent_timeout_seconds,
                article_length=len(input_dto.article),
                verticals=input_dto.verticals,
            )
            raise AgentTimeoutError(
                "Agent execution exceeded timeout",
                details={
                    "timeout_seconds": self.agent_config.agent_timeout_seconds,
                    "article_length": len(input_dto.article),
                    "verticals": input_dto.verticals,
                }
            ) from e

        # LangGraph returns dict with only output field (via output_schema)
        # Convert to AgentOutputState for type safety
        output_state = AgentOutputState(**output_state_dict)

        # Validate output was populated
        if output_state.output is None:
            raise AgentStateError(
                "Output node failed to produce output",
                details={
                    "graph_state_keys": list(output_state_dict.keys()),
                    "expected_field": "output",
                },
                conflict=False,  # Programming error, not user-resolvable
            )

        self.logger.info(
            "execution completed",
            total_products=output_state.output.total_products,
            status=output_state.output.status,
        )

        # Return AgentOutput DTO
        return output_state.output
