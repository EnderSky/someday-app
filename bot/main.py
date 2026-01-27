import logging
from telegram.ext import Application

from config.settings import settings
from bot.handlers import register_all_handlers

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def create_application() -> Application:
    """Create and configure the bot application."""
    settings.validate()
    
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    register_all_handlers(application)
    
    return application


def run_polling():
    """Run the bot in polling mode (for local development)."""
    logger.info("Starting bot in polling mode...")
    application = create_application()
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "edited_message", "callback_query"]
    )


async def run_webhook():
    """Run the bot in webhook mode (for production)."""
    import uvicorn
    from telegram.ext import ApplicationBuilder
    
    logger.info("Starting bot in webhook mode...")
    
    application = create_application()
    
    # Set up webhook
    await application.bot.set_webhook(
        url=f"{settings.WEBHOOK_URL}",
        allowed_updates=["message", "edited_message", "callback_query"]
    )
    
    # Create ASGI app for uvicorn
    # Note: python-telegram-bot v21 has built-in webhook support
    await application.start()
    
    # Keep running
    import asyncio
    await asyncio.Event().wait()


def main():
    """Main entry point."""
    if settings.is_production:
        import asyncio
        asyncio.run(run_webhook())
    else:
        run_polling()


if __name__ == "__main__":
    main()
