from bot.handlers.commands import register_command_handlers
from bot.handlers.messages import register_message_handlers
from bot.handlers.callbacks import register_callback_handlers


def register_all_handlers(application):
    """Register all handlers with the application."""
    register_command_handlers(application)
    register_message_handlers(application)
    register_callback_handlers(application)
