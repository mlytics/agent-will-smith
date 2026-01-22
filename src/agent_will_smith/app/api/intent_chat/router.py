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
    QuickQuestionsResponse,
    QuickQuestion,
)
from agent_will_smith.agent.intent_chat.container import Container
from agent_will_smith.agent.intent_chat.agent import Agent
from agent_will_smith.agent.intent_chat.state import ChatInput


router = APIRouter()


# Predefined quick questions for the chat interface
QUICK_QUESTIONS = [
    QuickQuestion(
        id="retirement_goals",
        text="What are your retirement goals?",
        category="retirement",
    ),
    QuickQuestion(
        id="risk_tolerance",
        text="What is your risk tolerance for investments?",
        category="risk",
    ),
    QuickQuestion(
        id="investment_timeline",
        text="What is your investment timeline?",
        category="planning",
    ),
    QuickQuestion(
        id="current_savings",
        text="How much are you currently saving?",
        category="savings",
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
    input_dto = ChatInput(
        message=body.message,
        session_id=body.session_id,
        context=body.context,
        conversation_history=body.conversation_history,
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
        intent_profile=IntentProfileResponse(
            life_stage=agent_output.intent_profile.life_stage,
            risk_preference=agent_output.intent_profile.risk_preference,
            product_interests=agent_output.intent_profile.product_interests,
            intent_score=agent_output.intent_profile.intent_score,
        ),
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
    input_dto = ChatInput(
        message=body.message,
        session_id=body.session_id,
        context=body.context,
        conversation_history=body.conversation_history,
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
                for i, word in enumerate(words):
                    accumulated += word + (" " if i < len(words) - 1 else "")
                    response_data = {
                        "response": accumulated,
                        "intent_profile": {
                            "life_stage": "accumulation",
                            "risk_preference": "moderate",
                            "product_interests": ["retirement", "investments"],
                            "intent_score": 0.5,
                        },
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
                "intent_profile": {
                    "life_stage": agent_output.intent_profile.life_stage,
                    "risk_preference": agent_output.intent_profile.risk_preference,
                    "product_interests": agent_output.intent_profile.product_interests,
                    "intent_score": agent_output.intent_profile.intent_score,
                },
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
