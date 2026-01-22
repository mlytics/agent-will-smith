"""Tool execution node for intent chat agent.

Executes tool calls from the tool_calling_node and updates state.
"""

import asyncio
import inspect
from typing import Any

import structlog

from agent_will_smith.agent.intent_chat.state import ChatState, IntentProfile, IntentSignal
from agent_will_smith.agent.intent_chat.model.namespaces import (
    ToolExecutionNodeNamespace,
    ToolResult,
)
from agent_will_smith.agent.intent_chat.config import Config

# Import tools for execution
from agent_will_smith.agent.intent_chat.tools.clarification_tool import get_clarification
from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import capture_intent
from agent_will_smith.agent.intent_chat.tools.product_recommendation_tool import get_product_recommendations


class ToolExecutionNode:
    """Executes tool calls and updates state.

    This node:
    1. Iterates through current_tool_calls
    2. Executes each tool with args
    3. Captures results or errors
    4. Updates intent_profile if intent_capture was called
    """

    # Map tool names to their functions
    TOOL_MAP = {
        "clarification": get_clarification,
        "intent_capture": capture_intent,
        "product_recommendation": get_product_recommendations,
    }

    def __init__(self, config: Config):
        self.config = config
        self.logger = structlog.get_logger(__name__)

    async def __call__(self, state: ChatState) -> dict:
        """Execute tool calls and return results.

        Args:
            state: Current chat state with current_tool_calls

        Returns:
            Dict with tool_execution_node namespace and updated intent_profile
        """
        self.logger.info(
            "tool execution node started",
            session_id=state.input.session_id,
            num_tool_calls=len(state.current_tool_calls),
        )

        tool_results = []
        new_signals = []

        for tool_call in state.current_tool_calls:
            tool_id = tool_call.get("id", "")
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})

            self.logger.debug(
                "executing tool",
                tool_id=tool_id,
                tool_name=tool_name,
            )

            try:
                result = await self._execute_tool(tool_name, tool_args)

                tool_results.append(
                    ToolResult(
                        tool_call_id=tool_id,
                        result=result,
                        error=None,
                    )
                )

                # Track intent signals from intent_capture tool
                if tool_name == "intent_capture" and result.get("type") == "intent_signal":
                    new_signals.append(result)

            except Exception as e:
                self.logger.error(
                    "tool execution failed",
                    tool_id=tool_id,
                    tool_name=tool_name,
                    error=str(e),
                )
                tool_results.append(
                    ToolResult(
                        tool_call_id=tool_id,
                        result=None,
                        error=f"Tool '{tool_name}' not found or failed: {str(e)}",
                    )
                )

        # Build updated intent profile if there are new signals
        updated_profile = self._update_intent_profile(state.intent_profile, new_signals)

        self.logger.info(
            "tool execution node completed",
            num_results=len(tool_results),
            num_errors=sum(1 for r in tool_results if r.error),
            new_signals=len(new_signals),
        )

        # Build tool result messages for the LLM context
        tool_messages = []
        for tr in tool_results:
            tool_messages.append({
                "role": "tool",
                "content": str(tr.result) if tr.result else tr.error or "",
                "tool_call_id": tr.tool_call_id,
            })

        result = {
            "tool_execution_node": ToolExecutionNodeNamespace(tool_results=tool_results),
            "current_tool_calls": [],  # Clear tool calls after execution
            "messages": state.messages + tool_messages,  # Add tool results to messages
        }

        if new_signals:
            result["intent_profile"] = updated_profile

        return result

    async def _execute_tool(self, tool_name: str, args: dict[str, Any]) -> dict:
        """Execute a single tool by name.

        Args:
            tool_name: Name of the tool to execute
            args: Arguments to pass to the tool

        Returns:
            Tool result dict

        Raises:
            ValueError: If tool not found
        """
        tool_func = self.TOOL_MAP.get(tool_name)
        if not tool_func:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Execute with timeout
        try:
            if inspect.iscoroutinefunction(tool_func):
                result = await asyncio.wait_for(
                    tool_func(**args),
                    timeout=self.config.tool_timeout_seconds,
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(tool_func, **args),
                    timeout=self.config.tool_timeout_seconds,
                )
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Tool '{tool_name}' timed out after {self.config.tool_timeout_seconds}s")

    def _update_intent_profile(
        self,
        current_profile: IntentProfile,
        new_signals: list[dict],
    ) -> IntentProfile:
        """Update intent profile with new signals.

        Args:
            current_profile: Current IntentProfile
            new_signals: List of new signal dicts from intent_capture

        Returns:
            Updated IntentProfile
        """
        if not new_signals:
            return current_profile

        # Convert new signal dicts to IntentSignal objects
        updated_signals = list(current_profile.signals)
        for signal_dict in new_signals:
            updated_signals.append(
                IntentSignal(
                    signal_type=signal_dict["signal_type"],
                    category=signal_dict["category"],
                    confidence=signal_dict["confidence"],
                )
            )

        # Calculate new intent score (average confidence of all signals)
        if updated_signals:
            new_score = sum(s.confidence for s in updated_signals) / len(updated_signals)
        else:
            new_score = 0.0

        # Update product interests
        product_interests = set(current_profile.product_interests)
        for signal_dict in new_signals:
            product_interests.add(signal_dict["category"])

        return IntentProfile(
            life_stage=current_profile.life_stage,
            risk_preference=current_profile.risk_preference,
            product_interests=list(product_interests),
            intent_score=min(new_score, 1.0),  # Cap at 1.0
            signals=updated_signals,
        )
