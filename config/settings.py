import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Webhook (production)
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    
    # Environment
    ENV: str = os.getenv("ENV", "development")
    
    # App settings
    DEFAULT_NOW_LIMIT: int = 3
    
    @property
    def is_production(self) -> bool:
        return self.ENV == "production"
    
    def validate(self) -> None:
        """Validate that required settings are present."""
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not self.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is required")
        if not self.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY is required")
        if self.is_production and not self.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL is required in production")


settings = Settings()
