"""Tool execution node for intent chat agent.

Executes tool calls from the tool_calling_node and updates state.
"""

import asyncio
import inspect
from typing import Any

import structlog

from agent_will_smith.agent.intent_chat.state import ChatState, FinancialGoal, IntentProfile, IntentSignal
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
                        name=tool_name,
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
                        name=tool_name,
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
            updated_intent_score=updated_profile.intent_score if new_signals else None,
        )

        # Build tool result messages for the LLM context
        tool_messages = []
        for tr in tool_results:
            tool_messages.append({
                "role": "tool",
                "content": str(tr.result) if tr.result else tr.error or "",
                "tool_call_id": tr.tool_call_id,
            })

        # Build namespace with optional intent profile updates
        namespace = ToolExecutionNodeNamespace(
            tool_results=tool_results,
            updated_intent_score=updated_profile.intent_score if new_signals else None,
            updated_product_interests=list(updated_profile.product_interests) if new_signals else None,
            updated_life_stage=updated_profile.life_stage if new_signals else None,
            updated_risk_preference=updated_profile.risk_preference if new_signals else None,
            updated_investment_experience=updated_profile.investment_experience if new_signals else None,
            updated_current_assets=updated_profile.current_assets if new_signals else None,
            updated_financial_goal=updated_profile.financial_goal.model_dump() if new_signals and updated_profile.financial_goal else None,
            updated_signals=[s.model_dump() for s in updated_profile.signals] if new_signals else None,
        )

        result = {
            "tool_execution_node": namespace,
            "current_tool_calls": [],  # Clear tool calls after execution
            "messages": state.messages + tool_messages,  # Add tool results to messages
        }

        # Also try direct state update (may not work with nested Pydantic models)
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

        # Extract new profile fields from signals (use latest value from signals)
        new_life_stage = current_profile.life_stage
        new_risk_preference = current_profile.risk_preference
        new_current_assets = current_profile.current_assets
        new_investment_experience = current_profile.investment_experience

        # Financial goal fields - start with current or None
        goal_target_age = current_profile.financial_goal.target_age if current_profile.financial_goal else None
        goal_target_amount = current_profile.financial_goal.target_amount if current_profile.financial_goal else None
        goal_timeline = current_profile.financial_goal.timeline if current_profile.financial_goal else None
        goal_type = current_profile.financial_goal.goal_type if current_profile.financial_goal else None

        # Update from signals (later signals override earlier ones)
        for signal_dict in new_signals:
            if signal_dict.get("life_stage") is not None:
                new_life_stage = signal_dict["life_stage"]
            if signal_dict.get("risk_preference") is not None:
                new_risk_preference = signal_dict["risk_preference"]
            if signal_dict.get("current_assets") is not None:
                new_current_assets = signal_dict["current_assets"]
            if signal_dict.get("investment_experience") is not None:
                new_investment_experience = signal_dict["investment_experience"]
            # Financial goal fields
            if signal_dict.get("target_age") is not None:
                goal_target_age = signal_dict["target_age"]
            if signal_dict.get("target_amount") is not None:
                goal_target_amount = signal_dict["target_amount"]
            if signal_dict.get("timeline") is not None:
                goal_timeline = signal_dict["timeline"]
            if signal_dict.get("goal_type") is not None:
                goal_type = signal_dict["goal_type"]

        # Build financial goal if any field is set
        new_financial_goal = None
        if any([goal_target_age, goal_target_amount, goal_timeline, goal_type]):
            new_financial_goal = FinancialGoal(
                target_age=goal_target_age,
                target_amount=goal_target_amount,
                timeline=goal_timeline,
                goal_type=goal_type,
            )

        return IntentProfile(
            life_stage=new_life_stage,
            risk_preference=new_risk_preference,
            product_interests=list(product_interests),
            intent_score=min(new_score, 1.0),  # Cap at 1.0
            signals=updated_signals,
            financial_goal=new_financial_goal,
            current_assets=new_current_assets,
            investment_experience=new_investment_experience,
        )
