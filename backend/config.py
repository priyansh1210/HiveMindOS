from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    gemini_api_key_2: str = ""  # optional second key for free-tier failover
    groq_api_key: str = ""

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    gemini_orchestrator_model: str = "gemini-2.5-pro"
    gemini_agent_model: str = "gemini-2.5-flash"
    groq_fallback_model: str = "llama-3.3-70b-versatile"

    # CSV in env: "https://foo.vercel.app,http://localhost:3000". Stored
    # as a raw string because pydantic-settings 2.x JSON-decodes list
    # fields from env. Use the cors_origin_list() helper to get the parsed
    # list.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    environment: str = "development"

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
