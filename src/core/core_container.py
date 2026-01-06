from dependency_injector import containers, providers
from src.core.config.databricks_config import DatabricksConfig
from src.core.config.mlflow_config import MLFlowConfig
from src.core.config.fastapi_config import FastAPIConfig


class CoreContainer(containers.DeclarativeContainer):
    """Core infrastructure container providing global configuration."""

    databricks_config = providers.Singleton(DatabricksConfig)
    mlflow_config = providers.Singleton(MLFlowConfig)
    fastapi_config = providers.Singleton(FastAPIConfig)
