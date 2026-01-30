"""Intent analysis node for LangGraph workflow."""

import structlog
import mlflow
from langchain.messages import SystemMessage, HumanMessage

from agent_will_smith.agent.product_recommendation.state import AgentState
from agent_will_smith.agent.product_recommendation.model.namespaces import IntentNodeNamespace
from agent_will_smith.agent.product_recommendation.config import Config
from agent_will_smith.infra.llm_client import LLMClient
from agent_will_smith.infra.prompt_client import PromptClient
from agent_will_smith.core.exceptions import DomainValidationError


class IntentAnalysisNode:
    """Analyzes user intent using LLM."""

    def __init__(self, llm_client: LLMClient, prompt_client: PromptClient, config: Config):
        self.llm_client = llm_client
        self.prompt_client = prompt_client
        self.config = config
        self.logger = structlog.get_logger(__name__)

    @mlflow.trace(name="intent_analysis_node")
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

        user_message = f"""文章摘要：{article_excerpt}

使用者問題：{question}"""

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

        # Strip whitespace and validate
        intent_text = response.content.strip() if response.content else ""

        if not intent_text or len(intent_text) < 10:
            raise DomainValidationError(
                "LLM returned insufficient intent",
                details={
                    "validation": "intent_too_short",
                    "expected_min_length": 10,
                    "actual_length": len(intent_text),
                    "raw_content": response.content,
                }
            )

        self.logger.info("intent analysis completed", intent_length=len(intent_text))

        return {"intent_node": IntentNodeNamespace(intent=intent_text)}
