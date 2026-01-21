"""Response node for intent chat agent.

Composes the final ChatOutput from the state.
This is the last node in the graph - creates the output DTO.
"""

import structlog

from agent_will_smith.agent.intent_chat.state import ChatState, ChatOutput
from agent_will_smith.agent.intent_chat.model.namespaces import ResponseNodeNamespace


class ResponseNode:
    """Composes final ChatOutput from state.

    This node:
    1. Extracts the latest assistant message as response
    2. Includes tool call results
    3. Copies intent profile to output
    4. Creates ChatOutput DTO
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    def __call__(self, state: ChatState) -> dict:
        """Compose final output from state.

        Args:
            state: Current chat state with messages, tool results, intent profile

        Returns:
            Dict with output ChatOutput and response_node namespace
        """
        self.logger.info(
            "response node started",
            session_id=state.input.session_id,
            num_messages=len(state.messages),
        )

        # Extract latest assistant message as response
        response_text = self._get_latest_assistant_message(state.messages)

        # Collect tool call results
        tool_calls = self._collect_tool_results(state)

        # Create ChatOutput
        output = ChatOutput(
            response=response_text or "I'm sorry, I couldn't generate a response.",
            intent_profile=state.intent_profile,
            tool_calls=tool_calls,
            session_id=state.input.session_id,
            is_complete=True,
        )

        self.logger.info(
            "response node completed",
            response_length=len(output.response),
            num_tool_calls=len(output.tool_calls),
            intent_score=output.intent_profile.intent_score,
        )

        return {
            "output": output,
            "response_node": ResponseNodeNamespace(
                response_text=output.response,
                is_streaming=False,
            ),
        }

    def _get_latest_assistant_message(self, messages: list[dict]) -> str:
        """Extract the latest assistant message from the messages list.

        Args:
            messages: List of message dicts with role and content

        Returns:
            The content of the last assistant message, or empty string
        """
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                return msg.get("content", "")
        return ""

    def _collect_tool_results(self, state: ChatState) -> list[dict]:
        """Collect tool call results from tool_execution_node namespace.

        Args:
            state: Current chat state

        Returns:
            List of tool result dicts for output
        """
        if not state.tool_execution_node:
            return []

        results = []
        for tool_result in state.tool_execution_node.tool_results:
            results.append({
                "tool_call_id": tool_result.tool_call_id,
                "result": tool_result.result,
                "error": tool_result.error,
            })

        return results
