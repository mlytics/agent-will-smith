"""Intent analysis node for LangGraph workflow.

This node performs the ONLY LLM call in the workflow to analyze user intent.
"""

import structlog
from langchain.messages import SystemMessage, HumanMessage

from agent_will_smith.agent.product_recommendation.schemas.state import AgentState
from agent_will_smith.agent.product_recommendation.schemas.messages import IntentAnalysisOutput
from agent_will_smith.agent.product_recommendation.config import ProductRecommendationAgentConfig
from agent_will_smith.infra.llm_client import LLMClient
from agent_will_smith.infra.prompt_client import PromptClient
from agent_will_smith.core.exceptions import DomainValidationError, UpstreamError, UpstreamTimeoutError, ToolExecutionError


class IntentAnalysisNode:
    """Node that analyzes user intent using LLM.

    Injectable class following the joke_agent pattern.
    """

    def __init__(self, llm_client: LLMClient, prompt_client: PromptClient, config: ProductRecommendationAgentConfig):
        """Initialize with injected dependencies.

        Args:
            llm_client: LLM client for making LLM calls
            prompt_client: Prompt client for loading prompts from MLflow
            config: Agent configuration
        """
        self.llm_client = llm_client
        self.prompt_client = prompt_client
        self.config = config
        self.logger = structlog.get_logger(__name__)

    def __call__(self, state: AgentState) -> IntentAnalysisOutput:
        """Analyze intent - the single LLM call in the workflow.

        Args:
            state: Current workflow state (Pydantic model)

        Returns:
            IntentAnalysisOutput with intent string

        Raises:
            DomainValidationError: If LLM returns empty intent
            UpstreamError: If LLM service has issues
            UpstreamTimeoutError: If LLM call times out
            ToolExecutionError: If intent analysis fails unexpectedly
        """

        self.logger.info("intent analysis started")

        try:
            # Load system prompt from MLflow
            system_prompt = self.prompt_client.load_prompt(self.config.prompt_name)
            self.logger.debug(
                "intent prompt loaded",
                prompt_length=len(system_prompt),
                prompt_source=self.config.prompt_name,
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
                "intent analysis invoking llm",
                article_length=len(article_excerpt),
                question_length=len(state.question),
            )

            # Single LLM call
            response = self.llm_client.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_message),
                ]
            )

            if not response.content:
                raise DomainValidationError(
                    "LLM returned empty intent",
                    details={
                        "validation": "empty_response",
                        "expected": "non-empty intent string",
                    }
                )

            self.logger.info("intent analysis completed", intent_length=len(response.content))

            return IntentAnalysisOutput(intent=response.content)

        except TimeoutError as e:
            self.logger.error("intent analysis timeout", error=str(e), exc_info=True)
            raise UpstreamTimeoutError(
                "Intent analysis timed out",
                details={
                    "provider": "databricks_llm",
                    "operation": "chat_completion",
                }
            ) from e

        except (DomainValidationError, UpstreamError, UpstreamTimeoutError):
            # Let specific exceptions bubble up
            raise

        except Exception as e:
            # Catch truly unexpected errors
            self.logger.error(
                "intent analysis failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            raise ToolExecutionError(
                "Intent analysis failed unexpectedly",
                details={
                    "tool_name": "intent_analysis",
                    "is_external": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            ) from e
