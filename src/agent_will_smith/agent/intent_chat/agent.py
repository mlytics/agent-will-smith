"""Intent chat agent using LangGraph workflow.

Graph-based agent for orchestrating chat conversations with intent tracking.

Namespace Architecture:
- State is organized into namespaces per node
- Each node writes to its own namespace only
- Nodes read from any namespace
- Tool calls flow through tool_calling_node → tool_execution_node
"""

import asyncio

import structlog
from langgraph.graph import StateGraph, START, END

from agent_will_smith.agent.intent_chat.state import (
    ChatState,
    ChatInput,
    ChatOutput,
)
from agent_will_smith.agent.intent_chat.config import Config
from agent_will_smith.core.exceptions import AgentTimeoutError, AgentStateError


class Agent:
    """Graph-based agent for intent chat workflow.

    Follows the product_recommendation agent pattern:
    - Constructor receives injected node instances
    - Builds LangGraph workflow with nodes
    - invoke() method runs the workflow with timeout
    """

    def __init__(
        self,
        conversation_node,
        tool_calling_node,
        tool_execution_node,
        response_node,
        agent_config: Config,
    ):
        """Initialize agent with injected node instances.

        Args:
            conversation_node: Node for processing messages and updating history
            tool_calling_node: Node for LLM with bound tools
            tool_execution_node: Node for executing tool calls
            response_node: Node for composing final ChatOutput
            agent_config: Agent configuration for metadata and timeouts
        """
        self.logger = structlog.get_logger(__name__)
        self.agent_config = agent_config

        # Store nodes
        self.conversation_node = conversation_node
        self.tool_calling_node = tool_calling_node
        self.tool_execution_node = tool_execution_node
        self.response_node = response_node

        # Build workflow graph
        workflow = StateGraph(ChatState)
        workflow.add_node("conversation_node", conversation_node)
        workflow.add_node("tool_calling_node", tool_calling_node)
        workflow.add_node("tool_execution_node", tool_execution_node)
        workflow.add_node("response_node", response_node)

        # Define flow:
        # START → conversation_node → tool_calling_node → [conditional]
        #                                     ├─ has tools → tool_execution_node → response_node → END
        #                                     └─ no tools  → response_node → END
        workflow.add_edge(START, "conversation_node")
        workflow.add_edge("conversation_node", "tool_calling_node")
        workflow.add_conditional_edges(
            "tool_calling_node",
            self._route_after_tool_calling,
            {
                "execute_tools": "tool_execution_node",
                "respond": "response_node",
            },
        )
        workflow.add_edge("tool_execution_node", "response_node")
        workflow.add_edge("response_node", END)

        self.graph = workflow.compile()
        self.logger.info("intent chat agent initialized")

    def _route_after_tool_calling(self, state: ChatState) -> str:
        """Route based on whether tool calls were made.

        Args:
            state: Current chat state

        Returns:
            "execute_tools" if there are tool calls, "respond" otherwise
        """
        if state.current_tool_calls:
            return "execute_tools"
        return "respond"

    async def invoke(self, input_dto: ChatInput) -> ChatOutput:
        """Run the agent with the given input DTO.

        Args:
            input_dto: ChatInput with message and session_id

        Returns:
            ChatOutput DTO with response and intent profile

        Raises:
            AgentTimeoutError: If execution exceeds timeout
            AgentStateError: If output node fails to produce output
        """
        self.logger.info(
            "execution started",
            session_id=input_dto.session_id,
            message_length=len(input_dto.message),
        )

        # Create initial state with input
        initial_state = ChatState(input=input_dto)

        # Run graph with timeout enforcement
        try:
            output_state_dict = await asyncio.wait_for(
                self.graph.ainvoke(initial_state),
                timeout=self.agent_config.agent_timeout_seconds,
            )
        except asyncio.TimeoutError as e:
            self.logger.error(
                "agent execution timeout",
                timeout_seconds=self.agent_config.agent_timeout_seconds,
                session_id=input_dto.session_id,
            )
            raise AgentTimeoutError(
                "Agent execution exceeded timeout",
                details={
                    "timeout_seconds": self.agent_config.agent_timeout_seconds,
                    "session_id": input_dto.session_id,
                }
            ) from e

        # Extract output from state dict
        output = output_state_dict.get("output")

        # Validate output was populated
        if output is None:
            raise AgentStateError(
                "Response node failed to produce output",
                details={
                    "graph_state_keys": list(output_state_dict.keys()),
                    "expected_field": "output",
                },
                conflict=False,
            )

        self.logger.info(
            "execution completed",
            session_id=output.session_id,
            response_length=len(output.response),
            num_tool_calls=len(output.tool_calls),
        )

        return output
