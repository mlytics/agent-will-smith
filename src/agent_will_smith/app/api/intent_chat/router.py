"""API routes for intent chat endpoints.

Follows guideline: "1 HTTP URL ↔ 1 agent"
Each endpoint maps to a single agent.
"""

import os
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
import structlog

from dependency_injector.wiring import inject, Provide

# Enable mock mode for local development without Databricks
MOCK_MODE = os.getenv("INTENT_CHAT_MOCK_MODE", "false").lower() == "true"

from agent_will_smith.app.api.intent_chat.dto import (
    ChatRequest,
    ChatResponse,
    IntentProfileResponse,
    IntentSignalResponse,
    FinancialGoalResponse,
    QuickQuestionsResponse,
    QuickQuestion,
)
from agent_will_smith.app.api.intent_chat.dto import IntentProfileRequest
from agent_will_smith.agent.intent_chat.container import Container
from agent_will_smith.agent.intent_chat.agent import Agent
from agent_will_smith.agent.intent_chat.state import ChatInput, IntentProfile, IntentSignal, FinancialGoal
from datetime import datetime


def _convert_request_to_intent_profile(req: IntentProfileRequest) -> IntentProfile:
    """Convert API request DTO to internal IntentProfile."""
    # Convert signals from request format
    signals = [
        IntentSignal(
            signal_type=s.signal_type,
            category=s.category,
            confidence=s.confidence,
            timestamp=datetime.fromisoformat(s.timestamp),
        )
        for s in req.signals
    ]

    # Convert financial goal if present
    financial_goal = None
    if req.financial_goal:
        financial_goal = FinancialGoal(
            target_age=req.financial_goal.target_age,
            target_amount=req.financial_goal.target_amount,
            timeline=req.financial_goal.timeline,
            goal_type=req.financial_goal.goal_type,
        )

    return IntentProfile(
        life_stage=req.life_stage,
        risk_preference=req.risk_preference,
        product_interests=req.product_interests,
        intent_score=req.intent_score,
        signals=signals,
        financial_goal=financial_goal,
        current_assets=req.current_assets,
        investment_experience=req.investment_experience,
    )


def _convert_intent_profile_to_response(profile: IntentProfile) -> IntentProfileResponse:
    """Convert internal IntentProfile to API response DTO."""
    # Convert signals to response format
    signals = [
        IntentSignalResponse(
            signal_type=s.signal_type,
            category=s.category,
            confidence=s.confidence,
            timestamp=s.timestamp.isoformat(),
        )
        for s in profile.signals
    ]

    # Convert financial goal if present
    financial_goal = None
    if profile.financial_goal:
        financial_goal = FinancialGoalResponse(
            target_age=profile.financial_goal.target_age,
            target_amount=profile.financial_goal.target_amount,
            timeline=profile.financial_goal.timeline,
            goal_type=profile.financial_goal.goal_type,
        )

    return IntentProfileResponse(
        life_stage=profile.life_stage,
        risk_preference=profile.risk_preference,
        product_interests=profile.product_interests,
        intent_score=profile.intent_score,
        signals=signals,
        financial_goal=financial_goal,
        current_assets=profile.current_assets,
        investment_experience=profile.investment_experience,
    )


def _intent_profile_to_dict(profile: IntentProfile) -> dict:
    """Convert IntentProfile to dict for SSE streaming."""
    signals = [
        {
            "signal_type": s.signal_type,
            "category": s.category,
            "confidence": s.confidence,
            "timestamp": s.timestamp.isoformat(),
        }
        for s in profile.signals
    ]

    financial_goal = None
    if profile.financial_goal:
        financial_goal = {
            "target_age": profile.financial_goal.target_age,
            "target_amount": profile.financial_goal.target_amount,
            "timeline": profile.financial_goal.timeline,
            "goal_type": profile.financial_goal.goal_type,
        }

    return {
        "life_stage": profile.life_stage,
        "risk_preference": profile.risk_preference,
        "product_interests": profile.product_interests,
        "intent_score": profile.intent_score,
        "signals": signals,
        "financial_goal": financial_goal,
        "current_assets": profile.current_assets,
        "investment_experience": profile.investment_experience,
    }


router = APIRouter()


# Predefined quick questions for the chat interface
# These are phrased from the USER's perspective (what they would say/ask)
QUICK_QUESTIONS = [
    QuickQuestion(
        id="retirement_planning",
        text="我想了解退休規劃，有什麼建議？",
        category="retirement",
    ),
    QuickQuestion(
        id="investment_options",
        text="幫我推薦適合的投資理財產品",
        category="investment",
    ),
    QuickQuestion(
        id="risk_assessment",
        text="我想評估自己的風險承受度",
        category="risk",
    ),
    QuickQuestion(
        id="financial_goals",
        text="我想開始規劃我的財務目標",
        category="planning",
    ),
]


def _mock_chat_response(message: str, session_id: str) -> ChatResponse:
    """Generate a mock chat response for local development."""
    return ChatResponse(
        response=f"Thanks for your question! I'm the Intent Advisor assistant. You asked: '{message}'. In a production environment, I would analyze your financial goals and help guide your investment journey. For now, I'm running in mock mode for local development.",
        intent_profile=IntentProfileResponse(
            life_stage="accumulation",
            risk_preference="moderate",
            product_interests=["retirement", "investments"],
            intent_score=0.5,
            signals=[],
            financial_goal=None,
            current_assets=None,
            investment_experience=None,
        ),
        tool_calls=[],
        session_id=session_id,
        is_complete=False,
    )


@router.post(
    "/chat/sync",
    response_model=ChatResponse,
    summary="Synchronous chat with intent tracking",
    description="""
    Sends a message to the chat agent and receives a complete response.

    This endpoint is synchronous - it waits for the full response before returning.
    For streaming responses, use POST /chat instead.

    **Architecture:** DI Container pattern following product_recommendation architecture.
    **Authentication:** Requires Bearer token in Authorization header.
    """,
    tags=["Chat"],
)
async def chat_sync_endpoint(
    request: Request,
    body: ChatRequest,
) -> ChatResponse:
    """Synchronous chat endpoint - maps 1:1 to Agent.

    Args:
        request: FastAPI request (for trace_id)
        body: Request payload with message and session_id

    Returns:
        ChatResponse with agent's response and intent profile
    """
    logger = structlog.get_logger(__name__)
    trace_id = getattr(request.state, "trace_id", "unknown")

    logger.info(
        "chat sync request",
        trace_id=trace_id,
        message_length=len(body.message),
        session_id=body.session_id,
        mock_mode=MOCK_MODE,
    )

    if MOCK_MODE:
        # Mock response for local development - no agent needed
        logger.info("mock mode enabled, returning mock response")
        return _mock_chat_response(body.message, body.session_id)

    # Get agent from container only when not in mock mode
    from agent_will_smith.agent.intent_chat.container import Container as IntentChatContainer
    container = IntentChatContainer()
    agent = container.agent()

    # Create ChatInput DTO from request body
    # Convert intent_profile from request if provided (includes signals for accumulation)
    initial_intent_profile = None
    if body.intent_profile:
        initial_intent_profile = _convert_request_to_intent_profile(body.intent_profile)

    input_dto = ChatInput(
        message=body.message,
        session_id=body.session_id,
        context=body.context,
        conversation_history=body.conversation_history,
        initial_intent_profile=initial_intent_profile,
    )

    # Invoke agent with DTO - returns ChatOutput DTO
    # Any exceptions will bubble to the global exception handler in main.py
    agent_output = await agent.invoke(input_dto)

    logger.info(
        "chat sync success",
        trace_id=trace_id,
        session_id=body.session_id,
        response_length=len(agent_output.response),
        intent_score=agent_output.intent_profile.intent_score,
    )

    # Transform ChatOutput to ChatResponse
    return ChatResponse(
        response=agent_output.response,
        intent_profile=_convert_intent_profile_to_response(agent_output.intent_profile),
        tool_calls=agent_output.tool_calls,
        session_id=agent_output.session_id,
        is_complete=agent_output.is_complete,
    )


@router.get(
    "/quick-questions",
    response_model=QuickQuestionsResponse,
    summary="Get quick question options",
    description="""
    Returns a list of predefined quick questions that users can select
    to start or continue a conversation.

    **Use case:** Displayed as quick-action buttons in the chat UI.
    """,
    tags=["Chat"],
)
def quick_questions_endpoint() -> QuickQuestionsResponse:
    """Get quick questions for the chat interface.

    Returns:
        QuickQuestionsResponse with list of quick question options
    """
    return QuickQuestionsResponse(questions=QUICK_QUESTIONS)


@router.post(
    "/chat",
    summary="Streaming chat with SSE",
    description="""
    Sends a message to the chat agent and receives a streaming response via SSE.

    Events:
    - text-delta: Partial text response
    - tool-call: Tool invocation notification
    - tool-result: Tool execution result
    - intent-profile-update: Updated intent profile
    - finish: End of stream

    **Architecture:** DI Container pattern with LangGraph streaming.
    **Authentication:** Requires Bearer token in Authorization header.
    """,
    tags=["Chat"],
)
async def chat_streaming_endpoint(
    request: Request,
    body: ChatRequest,
) -> StreamingResponse:
    """Streaming chat endpoint with SSE.

    Args:
        request: FastAPI request (for trace_id)
        body: Request payload with message and session_id

    Returns:
        StreamingResponse with SSE events
    """
    logger = structlog.get_logger(__name__)
    trace_id = getattr(request.state, "trace_id", "unknown")

    logger.info(
        "chat streaming request",
        trace_id=trace_id,
        message_length=len(body.message),
        session_id=body.session_id,
        mock_mode=MOCK_MODE,
    )

    # Create ChatInput DTO from request body
    # Convert intent_profile from request if provided (includes signals for accumulation)
    initial_intent_profile = None
    if body.intent_profile:
        initial_intent_profile = _convert_request_to_intent_profile(body.intent_profile)

    input_dto = ChatInput(
        message=body.message,
        session_id=body.session_id,
        context=body.context,
        conversation_history=body.conversation_history,
        initial_intent_profile=initial_intent_profile,
    )

    async def sse_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events from agent execution."""
        import json
        import asyncio

        try:
            if MOCK_MODE:
                # Mock response for local development
                logger.info("mock mode enabled, returning mock response")

                # Simulate streaming delay
                mock_response = f"Thanks for your question! I'm the Intent Advisor assistant. You asked: '{body.message}'. In a production environment, I would analyze your financial goals and help guide your investment journey. For now, I'm running in mock mode for local development."

                # Stream the response word by word
                words = mock_response.split()
                accumulated = ""
                mock_intent_profile = {
                    "life_stage": "accumulation",
                    "risk_preference": "moderate",
                    "product_interests": ["retirement", "investments"],
                    "intent_score": 0.5,
                    "signals": [],
                    "financial_goal": None,
                    "current_assets": None,
                    "investment_experience": None,
                }
                for i, word in enumerate(words):
                    accumulated += word + (" " if i < len(words) - 1 else "")
                    response_data = {
                        "response": accumulated,
                        "intent_profile": mock_intent_profile,
                    }
                    yield f"event: text-delta\ndata: {json.dumps(response_data)}\n\n"
                    await asyncio.sleep(0.05)  # Simulate streaming delay

                yield "event: finish\ndata: {}\n\n"
                return

            # Get agent from container only when not in mock mode
            from agent_will_smith.agent.intent_chat.container import Container as IntentChatContainer
            container = IntentChatContainer()
            agent = container.agent()

            # For now, use synchronous invoke and emit single finish event
            # TODO: Implement proper streaming with astream_events
            agent_output = await agent.invoke(input_dto)

            # Emit response as single text event
            response_data = {
                "response": agent_output.response,
                "intent_profile": _intent_profile_to_dict(agent_output.intent_profile),
                "tool_calls": agent_output.tool_calls,
                "session_id": agent_output.session_id,
            }
            yield f"event: text-delta\ndata: {json.dumps(response_data)}\n\n"
            yield "event: finish\ndata: {}\n\n"

        except Exception as e:
            logger.error(
                "streaming error",
                trace_id=trace_id,
                error=str(e),
            )
            error_data = {"error": str(e)}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
