"""Intent analysis node for LangGraph workflow.

This node performs the ONLY LLM call in the workflow to analyze user intent.

Namespace Architecture:
- Reads from: state.inputs (article, question)
- Writes to: state.intent_node (intent)
"""

import structlog
from langchain.messages import SystemMessage, HumanMessage

from agent_will_smith.agent.product_recommendation.schemas.state import AgentState, IntentNodeNamespace
from agent_will_smith.agent.product_recommendation.config import ProductRecommendationAgentConfig
from agent_will_smith.infra.llm_client import LLMClient
from agent_will_smith.infra.prompt_client import PromptClient
from agent_will_smith.core.exceptions import DomainValidationError


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

    def __call__(self, state: AgentState) -> dict:
        """Analyze intent - the single LLM call in the workflow.

        Args:
            state: Current workflow state (Pydantic model with namespaces)

        Returns:
            dict with "intent_node" key containing IntentNodeNamespace

        Raises:
            DomainValidationError: If LLM returns empty intent
            UpstreamError: If LLM or prompt loading fails (bubbled from infra layer)
            UpstreamTimeoutError: If LLM or prompt loading times out (bubbled from infra layer)
        """

        self.logger.info("intent analysis started")

        # Load system prompt from MLflow (may raise UpstreamError/UpstreamTimeoutError)
        system_prompt = self.prompt_client.load_prompt(self.config.prompt_name)
        self.logger.debug(
            "intent prompt loaded",
            prompt_length=len(system_prompt),
            prompt_source=self.config.prompt_name,
        )

        # Read from inputs namespace
        article = state.inputs.article
        question = state.inputs.question

        # Truncate article to avoid token limits (keep first 1000 chars)
        article_excerpt = article[:1000]
        if len(article) > 1000:
            article_excerpt += "..."

        user_message = f"""Article: {article_excerpt}

Question: {question}

Please analyze the intent and key themes of this article and question.
What is the user looking for? What are the main topics?
Provide a concise intent summary (2-3 sentences max)."""

        self.logger.info(
            "intent analysis invoking llm",
            article_length=len(article_excerpt),
            question_length=len(question),
        )

        # Single LLM call (may raise UpstreamError/UpstreamTimeoutError from llm_client)
        response = self.llm_client.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message),
            ]
        )

        # Business logic validation - this is domain validation, not infra error
        if not response.content:
            raise DomainValidationError(
                "LLM returned empty intent",
                details={
                    "validation": "empty_response",
                    "expected": "non-empty intent string",
                }
            )

        self.logger.info("intent analysis completed", intent_length=len(response.content))

        # Write to own namespace
        return {
            "intent_node": IntentNodeNamespace(intent=response.content)
        }
