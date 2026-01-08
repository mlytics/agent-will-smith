"""Intent analysis node for LangGraph workflow."""

import structlog
from langchain.messages import SystemMessage, HumanMessage

from agent_will_smith.agent.product_recommendation.state import AgentState
from agent_will_smith.agent.product_recommendation.model.namespaces import IntentNodeNamespace
from agent_will_smith.agent.product_recommendation.config import ProductRecommendationAgentConfig
from agent_will_smith.infra.llm_client import LLMClient
from agent_will_smith.infra.prompt_client import PromptClient
from agent_will_smith.core.exceptions import DomainValidationError


class IntentAnalysisNode:
    """Analyzes user intent using LLM."""

    def __init__(self, llm_client: LLMClient, prompt_client: PromptClient, config: ProductRecommendationAgentConfig):
        self.llm_client = llm_client
        self.prompt_client = prompt_client
        self.config = config
        self.logger = structlog.get_logger(__name__)

    def __call__(self, state: AgentState) -> dict:
        self.logger.info("intent analysis started")

        system_prompt = self.prompt_client.load_prompt(self.config.prompt_name)
        self.logger.debug(
            "intent prompt loaded",
            prompt_length=len(system_prompt),
            prompt_source=self.config.prompt_name,
        )

        article = state.input.article
        question = state.input.question

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

        return {"intent_node": IntentNodeNamespace(intent=response.content)}
