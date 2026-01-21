"""Intent capture tool for intent chat agent.

Records intent signals detected from user conversation.
Used to build the user's intent profile over time.
"""

from datetime import datetime, timezone
from typing import Literal

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field


logger = structlog.get_logger(__name__)

VALID_SIGNAL_TYPES = {"explicit", "inferred", "clarified"}


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


def capture_intent(
    category: str,
    signal_type: str,
    confidence: float,
) -> dict:
    """Capture an intent signal from user conversation.

    Args:
        category: The intent category (e.g., retirement, investment)
        signal_type: How intent was detected (explicit, inferred, clarified)
        confidence: Confidence score (0.0-1.0)

    Returns:
        Dict with intent signal data including timestamp

    Raises:
        ValueError: If confidence is out of range or signal_type is invalid
    """
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")

    if signal_type not in VALID_SIGNAL_TYPES:
        raise ValueError(
            f"signal_type must be one of {VALID_SIGNAL_TYPES}, got '{signal_type}'"
        )

    timestamp = datetime.now(timezone.utc).isoformat()

    logger.info(
        "intent captured",
        category=category,
        signal_type=signal_type,
        confidence=confidence,
    )

    return {
        "type": "intent_signal",
        "category": category,
        "signal_type": signal_type,
        "confidence": confidence,
        "timestamp": timestamp,
    }


@tool("intent_capture", args_schema=IntentCaptureToolInput)
def intent_capture_tool(
    category: str,
    signal_type: Literal["explicit", "inferred", "clarified"],
    confidence: float,
) -> dict:
    """Record an intent signal detected from the user's conversation.

    Use this tool to track user intent as the conversation progresses.
    Intent signals help build a profile to determine when to recommend products.

    Args:
        category: Intent category (retirement, investment, insurance, travel, etc.)
        signal_type: Detection method - explicit (user stated), inferred (context), clarified (follow-up)
        confidence: Confidence score from 0.0 (uncertain) to 1.0 (certain)

    Returns:
        Recorded intent signal with timestamp
    """
    return capture_intent(
        category=category,
        signal_type=signal_type,
        confidence=confidence,
    )
