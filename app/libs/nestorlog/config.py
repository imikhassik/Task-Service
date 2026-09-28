import os
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


#   Logging configuration
class LoggingConfig(BaseSettings):
    #   Primary settings
    enabled: bool = Field(default=True, alias="NLOG_ENABLED")
    levels_str: Union[str, List[str]] = Field(default="DEBUG,INFO,ERROR", alias="NLOG_LEVELS")
    #   Output settings
    handler: str = Field(default="stdout", alias="NLOG_HANDLER")  # stdout, file, synora
    file_path: Optional[str] = Field(default=None, alias="NLOG_FILE_PATH")

    #   Format settings
    max_bytes: int = Field(default=1024, alias="NLOG_MAX_BYTES")
    time_precision: str = Field(default="milliseconds", alias="NLOG_TIME_PRECISION")

    #   Performance settings
    async_send: bool = Field(default=True, alias="NLOG_ASYNC_SEND")

    # Sensitive fields masking settings
    sensitive_fields: List[str] = Field(
        default=["password", "paypass", "token", "secret", "key", "authorization"],
        alias="NLOG_SENSITIVE_FIELDS"
    )
    mask_enabled: bool = Field(default=True, alias="NLOG_MASK_ENABLED")

    class Config:
        env_prefix = "NLOG_"
        case_sensitive = False
        extra = "ignore"

    #   Checks whether the specified level needs to be logged
    #       Transforms 'DEBUG,INFO,ERROR' string into a list and return the list as is
    @property
    def levels(self) -> List[str]:
        if isinstance(self.levels_str, list):
            return [l.strip().upper() for l in self.levels_str] # NOQA: E741
        elif isinstance(self.levels_str, str):
            return [l.strip().upper() for l in self.levels_str.split(',')] # NOQA: E741
        else:
            return ["DEBUG", "INFO", "ERROR"]

    def is_level_enabled(self, level: str) -> bool:
        return level.upper() in self.levels

    def is_enabled(self) -> bool:
        return self.enabled


config = LoggingConfig()