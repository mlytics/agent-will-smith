"""Intent analysis node for LangGraph workflow.

This node performs the ONLY LLM call in the workflow to analyze user intent.
"""

import structlog

from agent.product_recommendation.schemas import AgentState, IntentAnalysisOutput
from agent.product_recommendation.infra.llm_client import LLMClient
from agent.product_recommendation.infra.prompts import load_prompt_from_registry
from core.exceptions import IntentAnalysisError, LLMServiceError, LLMServiceTimeout


class IntentAnalysisNode:
    """Node that analyzes user intent using LLM.

    Injectable class following the joke_agent pattern.
    """

    def __init__(self, llm_client: LLMClient, logger: structlog.BoundLogger):
        """Initialize with injected dependencies.

        Args:
            llm_client: LLM client for making LLM calls
            logger: Structlog logger with bound context
        """
        self.llm_client = llm_client
        self.logger = logger

    def __call__(self, state: AgentState) -> IntentAnalysisOutput:
        """Analyze intent - the single LLM call in the workflow.

        Args:
            state: Current workflow state (Pydantic model)

        Returns:
            IntentAnalysisOutput with intent string

        Raises:
            IntentAnalysisError: If intent analysis fails
            LLMServiceError: If LLM service has issues
            LLMServiceTimeout: If LLM call times out
        """

        self.logger.info("intent_analysis_started")

        try:
            # Load system prompt from MLflow
            prompt_content = load_prompt_from_registry()
            system_prompt = prompt_content.text
            self.logger.debug(
                "intent_prompt_loaded",
                prompt_length=len(system_prompt),
                prompt_source=prompt_content.source,
            )

            # Truncate article to avoid token limits (keep first 1000 chars)
            article_excerpt = state.article[:1000]
            if len(state.article) > 1000:
                article_excerpt += "..."

            user_message = f"""Article: {article_excerpt}

Question: {state.question}

Please analyze the intent and key themes of this article and question.
What is the user looking for? What are the main topics?
Provide a concise intent summary (2-3 sentences max)."""

            self.logger.info(
                "intent_analysis_invoking_llm",
                article_length=len(article_excerpt),
                question_length=len(state.question),
            )

            # Single LLM call
            intent = self.llm_client.invoke_with_messages(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ]
            )

            if not intent:
                raise IntentAnalysisError("LLM returned empty intent")

            self.logger.info("intent_analysis_completed", intent_length=len(intent))

            return IntentAnalysisOutput(intent=intent)

        except TimeoutError as e:
            self.logger.error("intent_analysis_timeout", error=str(e), exc_info=True)
            raise LLMServiceTimeout(f"Intent analysis timed out: {str(e)}") from e

        except Exception as e:
            self.logger.error(
                "intent_analysis_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )

            error_msg = str(e).lower()
            if "endpoint" in error_msg or "service" in error_msg or "connection" in error_msg:
                raise LLMServiceError(f"LLM service error: {str(e)}") from e

            raise IntentAnalysisError(f"Intent analysis failed: {str(e)}") from e
