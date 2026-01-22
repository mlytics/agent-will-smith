from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
import logging

class LogConfig(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CORE_LOG_",
        case_sensitive=False,
        extra="ignore",
    )

    level: Literal["debug", "info", "warning", "error", "fatal"] = Field(
        default="info", description="Logging level"
    )

    format: Literal["json", "pretty"] = Field(
        default="json", description="Logging format"
    )

    third_party_level: Literal["debug", "info", "warning", "error", "fatal"] = Field(
        default="warning", 
        description="Minimum log level for 3rd party libraries (mlflow, databricks, etc.)"
    )

    @property
    def level_int(self) -> int:
        return {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "fatal": logging.FATAL,
        }.get(self.level)

    @property
    def third_party_level_int(self) -> int:
        return {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "fatal": logging.FATAL,
        }.get(self.third_party_level)