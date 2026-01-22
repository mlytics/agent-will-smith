"""Tool calling node for intent chat agent.

Uses LLM with bound tools to decide what actions to take.
This node handles the "thinking" phase where the LLM decides whether to use tools.
"""

from typing import Any

import structlog
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from agent_will_smith.agent.intent_chat.state import ChatState
from agent_will_smith.agent.intent_chat.model.namespaces import (
    ToolCallingNodeNamespace,
    ToolCall,
)
from agent_will_smith.agent.intent_chat.tools.clarification_tool import clarification_tool
from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import intent_capture_tool
from agent_will_smith.agent.intent_chat.tools.product_recommendation_tool import product_recommendation_tool
from agent_will_smith.infra.llm_client import LLMClient
from agent_will_smith.infra.prompt_client import PromptClient
from agent_will_smith.agent.intent_chat.config import Config


class ToolCallingNode:
    """Decides what tools to invoke based on conversation context.

    This node:
    1. Loads system prompt
    2. Builds context with intent profile
    3. Calls LLM with bound tools
    4. Returns tool calls if any, or marks for direct response
    """

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_client: PromptClient,
        config: Config,
    ):
        self.llm_client = llm_client
        self.prompt_client = prompt_client
        self.config = config
        self.logger = structlog.get_logger(__name__)

        # Available tools for the LLM
        self.tools = [
            clarification_tool,
            intent_capture_tool,
            product_recommendation_tool,
        ]

    async def __call__(self, state: ChatState) -> dict:
        """Invoke LLM with tools to decide actions.

        Args:
            state: Current chat state with messages and intent profile

        Returns:
            Dict with tool_calling_node namespace and current_tool_calls
        """
        self.logger.info(
            "tool calling node started",
            session_id=state.input.session_id,
            num_messages=len(state.messages),
            intent_score=state.intent_profile.intent_score,
        )

        # Load system prompt
        system_prompt = self.prompt_client.load_prompt(self.config.system_prompt_name)

        # Build context with intent profile
        intent_context = self._build_intent_context(state)
        full_system_prompt = f"{system_prompt}\n\n{intent_context}"

        # Build messages for LLM
        messages = [SystemMessage(content=full_system_prompt)]
        for msg in state.messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                # Include tool_calls if present
                ai_msg = AIMessage(content=msg["content"])
                if msg.get("tool_calls"):
                    ai_msg.tool_calls = msg["tool_calls"]
                messages.append(ai_msg)
            elif msg["role"] == "tool":
                messages.append(ToolMessage(
                    content=msg["content"],
                    tool_call_id=msg.get("tool_call_id", ""),
                ))

        # Bind tools and invoke
        llm_with_tools = self.llm_client.bind_tools(self.tools)
        response = await llm_with_tools.ainvoke(messages)

        # Extract tool calls
        tool_calls = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                tool_calls.append({
                    "id": tc.get("id", ""),
                    "name": tc.get("name", ""),
                    "args": tc.get("args", {}),
                })

        # Build namespace
        namespace_tool_calls = [
            ToolCall(id=tc["id"], name=tc["name"], args=tc["args"])
            for tc in tool_calls
        ]

        # Extract text content from response (may be string or list of content blocks)
        response_text = self._extract_text_content(response.content)

        self.logger.info(
            "tool calling node completed",
            num_tool_calls=len(tool_calls),
            tool_names=[tc["name"] for tc in tool_calls],
            has_content=bool(response_text),
        )

        # Build assistant message with tool calls if any
        assistant_msg = {
            "role": "assistant",
            "content": response_text,
        }
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls

        return {
            "tool_calling_node": ToolCallingNodeNamespace(tool_calls=namespace_tool_calls),
            "current_tool_calls": tool_calls,
            "messages": state.messages + [assistant_msg],
            "step_count": state.step_count + 1,
        }

    def _extract_text_content(self, content) -> str:
        """Extract text from response content (handles string, JSON string, and content blocks).

        Args:
            content: Response content - may be string, JSON string, or list of content blocks

        Returns:
            Extracted text as string
        """
        import json

        if content is None:
            return ""

        # If it's a string, check if it's a JSON array of content blocks
        if isinstance(content, str):
            # Try to parse as JSON
            if content.startswith("["):
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, list):
                        return self._extract_from_blocks(parsed)
                except json.JSONDecodeError:
                    pass
            return content

        # If it's a list of content blocks, extract text parts
        if isinstance(content, list):
            return self._extract_from_blocks(content)

        # Fallback: convert to string
        return str(content)

    def _extract_from_blocks(self, blocks: list) -> str:
        """Extract text from content blocks."""
        text_parts = []
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif isinstance(block, str):
                text_parts.append(block)
        return "".join(text_parts)

    def _build_intent_context(self, state: ChatState) -> str:
        """Build context string from intent profile for LLM."""
        profile = state.intent_profile

        context_parts = ["## Current User Profile"]

        if profile.life_stage:
            context_parts.append(f"- Life Stage: {profile.life_stage}")

        if profile.risk_preference:
            context_parts.append(f"- Risk Preference: {profile.risk_preference}")

        if profile.product_interests:
            context_parts.append(f"- Product Interests: {', '.join(profile.product_interests)}")

        context_parts.append(f"- Intent Score: {profile.intent_score:.2f}")
        context_parts.append(f"- Intent Threshold for Recommendation: {self.config.intent_score_threshold}")

        if profile.intent_score >= self.config.intent_score_threshold:
            context_parts.append("\n**User is ready for product recommendations.**")
        else:
            context_parts.append("\n**Continue gathering intent signals before recommending products.**")

        return "\n".join(context_parts)
