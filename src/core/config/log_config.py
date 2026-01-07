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
    )

    level: Literal["debug", "info", "warning", "error", "fatal"] = Field(
        default="info", description="Logging level"
    )

    format: Literal["json", "pretty"] = Field(
        default="json", description="Logging format"
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