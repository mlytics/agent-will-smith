from dependency_injector import containers, providers
from core.config.databricks_config import DatabricksConfig
from core.config.mlflow_config import MLFlowConfig
from core.config.fastapi_config import FastAPIConfig


class CoreContainer(containers.DeclarativeContainer):
    """Core infrastructure container providing global configuration."""

    databricks_config = providers.Singleton(DatabricksConfig)
    mlflow_config = providers.Singleton(MLFlowConfig)
    fastapi_config = providers.Singleton(FastAPIConfig)
