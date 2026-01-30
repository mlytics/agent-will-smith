from dependency_injector import containers, providers
from agent_will_smith.core.config.log_config import LogConfig
from agent_will_smith.core.config.databricks_config import DatabricksConfig
from agent_will_smith.core.config.mlflow_config import MLFlowConfig
from agent_will_smith.core.config.fastapi_config import FastAPIConfig
from agent_will_smith.core.config.gemini_config import GeminiConfig


class Container(containers.DeclarativeContainer):
    """Core infrastructure container providing global configuration."""

    databricks_config = providers.Singleton(DatabricksConfig)
    mlflow_config = providers.Singleton(MLFlowConfig)
    fastapi_config = providers.Singleton(FastAPIConfig)
    log_config = providers.Singleton(LogConfig)
    gemini_config = providers.Singleton(GeminiConfig)