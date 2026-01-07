"""Unified configuration access point for common infrastructure.

Provides a single `config` object with namespaced access to common infrastructure:
- config.databricks.*  (Databricks workspace + auth)
- config.mlflow.*      (MLFlow tracking + registry)
- config.fastapi.*     (API server + auth + observability)

Agents should import their own config from their respective modules.

Also provides backward-compatible flat access for existing code.
"""

from agent_will_smith.core.config.databricks_config import DatabricksConfig
from agent_will_smith.core.config.mlflow_config import MLFlowConfig
from agent_will_smith.core.config.fastapi_config import FastAPIConfig


# Export for convenience
__all__ = [
    "DatabricksConfig",
    "MLFlowConfig",
    "FastAPIConfig",
]
