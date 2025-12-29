"""Unified configuration access point for common infrastructure.

Provides a single `config` object with namespaced access to common infrastructure:
- config.databricks.*  (Databricks workspace + auth)
- config.mlflow.*      (MLFlow tracking + registry)
- config.fastapi.*     (API server + auth + observability)

Agents should import their own config from their respective modules.

Also provides backward-compatible flat access for existing code.
"""

from core.config.common import DatabricksConfig, MLFlowConfig
from core.config.fastapi import FastAPIConfig


class AppConfig:
    """Unified application configuration with namespaced access.
    
    Usage:
        from core.config import config
        
        # Namespaced access (recommended)
        config.databricks.databricks_host
        config.mlflow.mlflow_experiment_id
        config.fastapi.port
        
        # Flat access (backward compatibility)
        config.databricks_host
        config.port
        config.app_name
    
    Note: Agent-specific configs are imported separately by each agent.
    Example:
        from agent.product_recommendation.config.settings import agent_config
    """
    
    def __init__(self):
        """Initialize common infrastructure config sections."""
        # Initialize all config sections (triggers model_post_init for env vars)
        self.databricks = DatabricksConfig()
        self.mlflow = MLFlowConfig()
        self.fastapi = FastAPIConfig()
    
    def __getattr__(self, name: str):
        """Provide flat access for backward compatibility.
        
        Searches through all config sections to find the attribute.
        """
        # Search through all config sections
        for config_section in [
            self.databricks,
            self.mlflow,
            self.fastapi,
        ]:
            if hasattr(config_section, name):
                return getattr(config_section, name)
        
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'. "
            f"Check config sections: databricks, mlflow, fastapi"
        )


# Global config instance
config = AppConfig()

# Export for convenience
__all__ = [
    "config",
    "AppConfig",
    "DatabricksConfig",
    "MLFlowConfig",
    "FastAPIConfig",
]

