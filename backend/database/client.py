from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from config import get_settings


@lru_cache
def get_supabase() -> Optional[Client]:
    """Return a cached Supabase client, or None if creds are missing.

    Returning None lets the app boot for local dev without Supabase configured;
    routes that need DB access should check for None and 503 gracefully.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        return None
    return create_client(settings.supabase_url, settings.supabase_service_key)
