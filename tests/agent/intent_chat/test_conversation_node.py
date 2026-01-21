"""Tests for conversation node.

This node processes the incoming message and updates the message history.
"""

import pytest


class TestConversationNode:
    """Tests for ConversationNode that manages message history."""

    def test_node_is_callable(self):
        """Node should be a callable class with __call__ method."""
        from agent_will_smith.agent.intent_chat.node.conversation_node import (
            ConversationNode,
        )

        node = ConversationNode()
        assert callable(node)

    def test_node_adds_user_message_to_state(self):
        """Node should add the user's message to the messages list."""
        from agent_will_smith.agent.intent_chat.node.conversation_node import (
            ConversationNode,
        )
        from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput

        node = ConversationNode()
        chat_input = ChatInput(
            message="Hello, I need help with retirement planning",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(input=chat_input)

        result = node(state)

        # Node should return dict with updated messages and conversation_node namespace
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"] == "Hello, I need help with retirement planning"

    def test_node_preserves_conversation_history(self):
        """Node should preserve existing conversation history in messages."""
        from agent_will_smith.agent.intent_chat.node.conversation_node import (
            ConversationNode,
        )
        from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput

        node = ConversationNode()
        chat_input = ChatInput(
            message="What about bonds?",
            session_id="550e8400-e29b-41d4-a716-446655440000",
            conversation_history=[
                {"role": "user", "content": "Tell me about investing"},
                {"role": "assistant", "content": "I can help with that!"},
            ],
        )
        state = ChatState(input=chat_input)

        result = node(state)

        # Should have history (2) + new message (1)
        assert len(result["messages"]) == 3
        assert result["messages"][0]["content"] == "Tell me about investing"
        assert result["messages"][2]["content"] == "What about bonds?"

    def test_node_returns_conversation_namespace(self):
        """Node should return ConversationNodeNamespace with messages_added."""
        from agent_will_smith.agent.intent_chat.node.conversation_node import (
            ConversationNode,
        )
        from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput
        from agent_will_smith.agent.intent_chat.model.namespaces import (
            ConversationNodeNamespace,
        )

        node = ConversationNode()
        chat_input = ChatInput(
            message="New message",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(input=chat_input)

        result = node(state)

        assert "conversation_node" in result
        namespace = result["conversation_node"]
        assert isinstance(namespace, ConversationNodeNamespace)
        assert namespace.messages_added == 1

    def test_node_estimates_token_usage(self):
        """Node should estimate tokens used in conversation."""
        from agent_will_smith.agent.intent_chat.node.conversation_node import (
            ConversationNode,
        )
        from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput

        node = ConversationNode()
        chat_input = ChatInput(
            message="This is a test message with some words",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(input=chat_input)

        result = node(state)

        namespace = result["conversation_node"]
        # Should have some token count estimate (rough approximation)
        assert namespace.tokens_used > 0
