"""Conversation node for intent chat agent.

Processes incoming message and updates the conversation history.
This is the first node in the graph - prepares messages for LLM.
"""

import structlog

from agent_will_smith.agent.intent_chat.state import ChatState
from agent_will_smith.agent.intent_chat.model.namespaces import ConversationNodeNamespace


class ConversationNode:
    """Manages conversation history and prepares messages for LLM.

    This node:
    1. Loads conversation history from input
    2. Adds the new user message
    3. Estimates token usage
    4. Returns updated messages list and namespace
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    def __call__(self, state: ChatState) -> dict:
        """Process incoming message and update conversation history.

        Args:
            state: Current chat state with input message

        Returns:
            Dict with updated messages list and conversation_node namespace
        """
        self.logger.info(
            "conversation node started",
            session_id=state.input.session_id,
            message_length=len(state.input.message),
        )

        # Build messages list from history + new message
        messages = []

        # Add conversation history first
        for msg in state.input.conversation_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        # Add the new user message
        messages.append({
            "role": "user",
            "content": state.input.message,
        })

        # Estimate token usage (rough approximation: ~4 chars per token)
        total_chars = sum(len(m["content"]) for m in messages)
        estimated_tokens = total_chars // 4

        self.logger.info(
            "conversation node completed",
            total_messages=len(messages),
            estimated_tokens=estimated_tokens,
        )

        return {
            "messages": messages,
            "conversation_node": ConversationNodeNamespace(
                messages_added=1,
                tokens_used=estimated_tokens,
            ),
        }
