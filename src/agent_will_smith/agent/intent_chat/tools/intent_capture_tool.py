"""Intent capture tool for intent chat agent.

Records intent signals detected from user conversation.
Used to build the user's intent profile over time.
"""

from datetime import datetime, timezone
from typing import Literal, Optional

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field


logger = structlog.get_logger(__name__)

VALID_SIGNAL_TYPES = {"explicit", "inferred", "clarified"}
VALID_RISK_PREFERENCES = {"conservative", "moderate", "aggressive"}
VALID_INVESTMENT_EXPERIENCES = {"beginner", "intermediate", "experienced"}


class IntentCaptureToolInput(BaseModel):
    """Input schema for intent capture tool."""

    category: str = Field(
        ...,
        description="The intent category (e.g., retirement, investment, insurance, travel)",
        min_length=1,
        max_length=100,
    )
    signal_type: Literal["explicit", "inferred", "clarified"] = Field(
        ...,
        description="How the intent was detected: explicit (stated), inferred (from context), clarified (after follow-up)",
    )
    confidence: float = Field(
        ...,
        description="Confidence score for this intent signal (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    life_stage: Optional[str] = Field(
        default=None,
        description="User's life stage (e.g., pre_retirement, retired, early_career)",
    )
    risk_preference: Optional[Literal["conservative", "moderate", "aggressive"]] = Field(
        default=None,
        description="User's risk preference for investments",
    )
    investment_experience: Optional[Literal["beginner", "intermediate", "experienced"]] = Field(
        default=None,
        description="User's investment experience level",
    )
    target_age: Optional[int] = Field(
        default=None,
        description="Target age for financial goal",
    )
    target_amount: Optional[str] = Field(
        default=None,
        description="Target amount for financial goal (e.g., '2000萬')",
    )
    timeline: Optional[str] = Field(
        default=None,
        description="Timeline for achieving the goal (e.g., '5年')",
    )
    goal_type: Optional[str] = Field(
        default=None,
        description="Type of financial goal (e.g., retirement, education, house)",
    )
    current_assets: Optional[str] = Field(
        default=None,
        description="User's current assets (e.g., '1000萬台幣')",
    )


def capture_intent(
    category: str,
    signal_type: str,
    confidence: float,
    life_stage: Optional[str] = None,
    risk_preference: Optional[str] = None,
    investment_experience: Optional[str] = None,
    target_age: Optional[int] = None,
    target_amount: Optional[str] = None,
    timeline: Optional[str] = None,
    goal_type: Optional[str] = None,
    current_assets: Optional[str] = None,
) -> dict:
    """Capture an intent signal from user conversation.

    Args:
        category: The intent category (e.g., retirement, investment)
        signal_type: How intent was detected (explicit, inferred, clarified)
        confidence: Confidence score (0.0-1.0)
        life_stage: User's life stage (e.g., pre_retirement, retired)
        risk_preference: User's risk preference (conservative, moderate, aggressive)
        investment_experience: User's experience level (beginner, intermediate, experienced)
        target_age: Target age for financial goal
        target_amount: Target amount for financial goal
        timeline: Timeline for achieving the goal
        goal_type: Type of financial goal
        current_assets: User's current assets

    Returns:
        Dict with intent signal data including timestamp

    Raises:
        ValueError: If confidence is out of range, signal_type is invalid,
                   or risk_preference/investment_experience have invalid values
    """
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")

    if signal_type not in VALID_SIGNAL_TYPES:
        raise ValueError(
            f"signal_type must be one of {VALID_SIGNAL_TYPES}, got '{signal_type}'"
        )

    if risk_preference is not None and risk_preference not in VALID_RISK_PREFERENCES:
        raise ValueError(
            f"risk_preference must be one of {VALID_RISK_PREFERENCES}, got '{risk_preference}'"
        )

    if investment_experience is not None and investment_experience not in VALID_INVESTMENT_EXPERIENCES:
        raise ValueError(
            f"investment_experience must be one of {VALID_INVESTMENT_EXPERIENCES}, got '{investment_experience}'"
        )

    timestamp = datetime.now(timezone.utc).isoformat()

    logger.info(
        "intent captured",
        category=category,
        signal_type=signal_type,
        confidence=confidence,
    )

    result = {
        "type": "intent_signal",
        "category": category,
        "signal_type": signal_type,
        "confidence": confidence,
        "timestamp": timestamp,
    }

    # Only include optional fields if they have values
    if life_stage is not None:
        result["life_stage"] = life_stage
    if risk_preference is not None:
        result["risk_preference"] = risk_preference
    if investment_experience is not None:
        result["investment_experience"] = investment_experience
    if target_age is not None:
        result["target_age"] = target_age
    if target_amount is not None:
        result["target_amount"] = target_amount
    if timeline is not None:
        result["timeline"] = timeline
    if goal_type is not None:
        result["goal_type"] = goal_type
    if current_assets is not None:
        result["current_assets"] = current_assets

    return result


@tool("intent_capture", args_schema=IntentCaptureToolInput)
def intent_capture_tool(
    category: str,
    signal_type: Literal["explicit", "inferred", "clarified"],
    confidence: float,
    life_stage: Optional[str] = None,
    risk_preference: Optional[Literal["conservative", "moderate", "aggressive"]] = None,
    investment_experience: Optional[Literal["beginner", "intermediate", "experienced"]] = None,
    target_age: Optional[int] = None,
    target_amount: Optional[str] = None,
    timeline: Optional[str] = None,
    goal_type: Optional[str] = None,
    current_assets: Optional[str] = None,
) -> dict:
    """Record an intent signal detected from the user's conversation.

    Use this tool to track user intent as the conversation progresses.
    Intent signals help build a profile to determine when to recommend products.

    Args:
        category: Intent category (retirement, investment, insurance, travel, etc.)
        signal_type: Detection method - explicit (user stated), inferred (context), clarified (follow-up)
        confidence: Confidence score from 0.0 (uncertain) to 1.0 (certain)
        life_stage: User's life stage (e.g., pre_retirement, retired, early_career)
        risk_preference: User's risk preference (conservative, moderate, aggressive)
        investment_experience: User's experience level (beginner, intermediate, experienced)
        target_age: Target age for financial goal
        target_amount: Target amount for financial goal (e.g., '2000萬')
        timeline: Timeline for achieving the goal (e.g., '5年')
        goal_type: Type of financial goal (e.g., retirement, education, house)
        current_assets: User's current assets (e.g., '1000萬台幣')

    Returns:
        Recorded intent signal with timestamp
    """
    return capture_intent(
        category=category,
        signal_type=signal_type,
        confidence=confidence,
        life_stage=life_stage,
        risk_preference=risk_preference,
        investment_experience=investment_experience,
        target_age=target_age,
        target_amount=target_amount,
        timeline=timeline,
        goal_type=goal_type,
        current_assets=current_assets,
    )
