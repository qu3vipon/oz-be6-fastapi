import os
from enum import StrEnum

from pydantic_settings import BaseSettings


class ServerEnv(StrEnum):
    LOCAL = "local"  # 내 로컬 환경
    DEV = "dev"      # 개발 서버
    PROD = "prod"    # 프로덕션 서버

class Settings(BaseSettings):
    database_url: str
    redis_host: str
    redis_port: int

def get_settings(env: ServerEnv):
    match env:
        case ServerEnv.DEV:
            return Settings(_env_file="config/.env.dev")
        case ServerEnv.PROD:
            return Settings(_env_file="config/.env.prod")
        case _:
            return Settings(_env_file="config/.env.local")

ENV = os.getenv("ENV", ServerEnv.LOCAL)
settings = get_settings(env=ENV)
