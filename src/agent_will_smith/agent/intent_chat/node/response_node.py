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

        # Get intent profile, checking for updates in tool_execution_node namespace
        # (workaround for LangGraph not properly updating nested Pydantic models)
        intent_profile = self._get_updated_intent_profile(state)

        # Create ChatOutput
        output = ChatOutput(
            response=response_text or "I'm sorry, I couldn't generate a response.",
            intent_profile=intent_profile,
            tool_calls=tool_calls,
            session_id=state.input.session_id,
            is_complete=True,
        )

        self.logger.info(
            "response node completed",
            response_length=len(output.response),
            num_tool_calls=len(output.tool_calls),
            intent_score=intent_profile.intent_score,
            product_interests=intent_profile.product_interests,
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
                content = msg.get("content", "")
                return self._extract_text_content(content)
        return ""

    def _extract_text_content(self, content) -> str:
        """Extract text from content (handles string, JSON string, and content blocks).

        Args:
            content: Content - may be string, JSON string, or list of content blocks

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
                "name": tool_result.name,
                "result": tool_result.result,
                "error": tool_result.error,
            })

        return results

    def _get_updated_intent_profile(self, state: ChatState):
        """Get intent profile with any updates from tool_execution_node.

        LangGraph doesn't properly update nested Pydantic models in state,
        so we check the tool_execution_node namespace for updates.

        Args:
            state: Current chat state

        Returns:
            Updated IntentProfile
        """
        from agent_will_smith.agent.intent_chat.state import IntentProfile, FinancialGoal

        base_profile = state.intent_profile

        if state.tool_execution_node:
            ns = state.tool_execution_node
            has_updates = (
                ns.updated_intent_score is not None
                or ns.updated_product_interests is not None
                or ns.updated_life_stage is not None
                or ns.updated_risk_preference is not None
                or ns.updated_investment_experience is not None
                or ns.updated_current_assets is not None
                or ns.updated_financial_goal is not None
            )

            if has_updates:
                self.logger.info(
                    "applying intent profile updates from namespace",
                    original_score=base_profile.intent_score,
                    updated_score=ns.updated_intent_score,
                    updated_life_stage=ns.updated_life_stage,
                )

                # Build financial goal from namespace if present
                financial_goal = base_profile.financial_goal
                if ns.updated_financial_goal:
                    financial_goal = FinancialGoal(**ns.updated_financial_goal)

                return IntentProfile(
                    life_stage=ns.updated_life_stage if ns.updated_life_stage is not None else base_profile.life_stage,
                    risk_preference=ns.updated_risk_preference if ns.updated_risk_preference is not None else base_profile.risk_preference,
                    product_interests=ns.updated_product_interests if ns.updated_product_interests is not None else base_profile.product_interests,
                    intent_score=ns.updated_intent_score if ns.updated_intent_score is not None else base_profile.intent_score,
                    signals=base_profile.signals,
                    financial_goal=financial_goal,
                    current_assets=ns.updated_current_assets if ns.updated_current_assets is not None else base_profile.current_assets,
                    investment_experience=ns.updated_investment_experience if ns.updated_investment_experience is not None else base_profile.investment_experience,
                )

        return base_profile
