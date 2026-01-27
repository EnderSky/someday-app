from typing import Optional
from bot.db.supabase_client import get_client


def get_or_create_user(telegram_id: int) -> dict:
    """Get existing user or create a new one."""
    client = get_client()
    
    # Try to get existing user
    response = client.table("users").select("*").eq("telegram_id", telegram_id).execute()
    
    if response.data:
        return response.data[0]
    
    # Create new user
    new_user = {"telegram_id": telegram_id}
    response = client.table("users").insert(new_user).execute()
    return response.data[0]


def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    """Get user by Telegram ID."""
    client = get_client()
    response = client.table("users").select("*").eq("telegram_id", telegram_id).execute()
    return response.data[0] if response.data else None


def update_user_settings(user_id: str, settings: dict) -> dict:
    """Update user settings."""
    client = get_client()
    response = client.table("users").update({"settings": settings}).eq("id", user_id).execute()
    return response.data[0]


def get_user_setting(user: dict, key: str, default=None):
    """Get a specific setting from user's settings JSON.
    
    Includes validation for specific settings:
    - now_display_limit: capped to 1-5 range
    """
    settings = user.get("settings", {}) or {}
    value = settings.get(key, default)
    
    # Validate now_display_limit to 1-5 range
    if key == "now_display_limit" and value is not None:
        value = max(1, min(5, int(value)))
    
    return value


def get_user_theme(user: dict) -> str:
    """Get user's theme setting, defaulting to 'classic'."""
    theme = get_user_setting(user, "theme", "classic")
    return str(theme) if theme else "classic"
