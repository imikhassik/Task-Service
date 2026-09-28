from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    ENVIRONMENT: str
    SERVICE_NAME: str


    SERVICE_REGISTRY_URL: str
    QUEST_API_REGISTRY_URL: str


    USER_PROFILES_API: str
    APPLICATION_PROCESSOR: str


    # HTTP client settings
    UHTTP_TIMEOUT: float = 20
    UHTTP_RESOLVE_IP: bool = False
    UHTTP_LOG_DNS: bool = False
    UHTTP_LOG_RESPONSE: bool = False
    UHTTP_VERIFY_SSL: bool = False


    # Nestorlog settings
    NLOG_ENABLED: bool = True
    NLOG_LEVELS: List[str] = ["DEBUG", "INFO", "ERROR"]  # ERROR must be enabled!
    NLOG_HANDLER: str = "stdout"
    NLOG_MAX_BYTES: int = 2048
    NLOG_TIME_PRECISION: str = "milliseconds"
    NLOG_ASYNC_SEND: bool = True
    NLOG_FILE_PATH: str = "/var/log/service/logs.json"  # for the file handler


    # Authorization settings
    AUTH_PATH: str
    AUTH_ENABLED: bool


    JWT_ALGORITHM: str
    ACCESS_TOKEN_PUBLIC_KEY: str


    ALLOWED_HOSTS: str = "http://127.0.0.1 http://10.0.0.21"
    VERSION: str = "0.2.0"


    model_config = SettingsConfigDict(env_file=".env")



settings = Settings()