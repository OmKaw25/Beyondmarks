from functools import lru_cache
from pathlib import Path
import re
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore')
    database_url: str = ''
    database_schema: str = Field(default='public', validation_alias='APP_DATABASE_SCHEMA')
    jwt_secret: str = ''
    jwt_expire_minutes: int = 1440
    cors_origins: str = 'http://localhost:3000,http://127.0.0.1:3000'
    demo_password: str = ''
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-3.5-flash-lite'
    secure_cookies: bool = False
    debug: bool = Field(default=False, validation_alias='BM_DEBUG')

    @field_validator('database_schema')
    @classmethod
    def safe_database_schema(cls, value):
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,62}', value) or value.startswith('pg_') or value == 'information_schema':
            raise ValueError('APP_DATABASE_SCHEMA must be a non-system lowercase PostgreSQL identifier.')
        return value

    @property
    def origins(self):
        return [v.strip() for v in self.cors_origins.split(',') if v.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
