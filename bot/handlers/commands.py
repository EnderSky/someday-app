from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from bot.services.user_service import get_or_create_user, get_user_setting, get_user_theme
from bot.services.task_service import get_tasks_by_category, get_task_counts
from bot.services.shuffle_service import get_shuffled_tasks
from bot.utils.formatters import format_task_list
from bot.utils.keyboards import get_main_keyboard, get_task_list_keyboard
from config.settings import settings


WELCOME_MESSAGE = """🎯 Someday

Your ADHD-friendly task manager.

HOW IT WORKS
Just send me any message — it becomes a task.
Move important tasks to Soon or Now.
I show only a few NOW tasks to keep you focused.

COMMANDS
/now · View your tasks
/start · Show this help

Send me your first task to begin.
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start and /help commands - show welcome message."""
    telegram_id = update.effective_user.id
    
    # Ensure user exists in database
    get_or_create_user(telegram_id)
    
    await update.message.reply_text(WELCOME_MESSAGE)


async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /now command - show NOW tasks with navigation."""
    telegram_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user = get_or_create_user(telegram_id)
    
    # Delete previous /now message to prevent clutter
    if context.user_data.get("last_now_message_id"):
        try:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=context.user_data["last_now_message_id"]
            )
        except Exception:
            # Message may already be deleted or too old, ignore
            pass
    
    # Get user's NOW limit setting and theme
    now_limit = get_user_setting(user, "now_display_limit", settings.DEFAULT_NOW_LIMIT)
    theme = get_user_theme(user)
    
    # Get tasks and counts
    now_tasks = get_tasks_by_category(user["id"], "now")
    counts = get_task_counts(user["id"])
    
    # Apply smart shuffle
    shuffled_tasks = get_shuffled_tasks(now_tasks, now_limit or settings.DEFAULT_NOW_LIMIT)
    
    # Format message with theme
    message, parse_mode = format_task_list(shuffled_tasks, "now", counts, limit=now_limit, theme=theme)
    
    # Get keyboard with counts
    keyboard = get_task_list_keyboard(shuffled_tasks, "now", counts=counts)
    
    # Send new message and store its ID
    sent_message = await update.message.reply_text(message, reply_markup=keyboard, parse_mode=parse_mode)
    context.user_data["last_now_message_id"] = sent_message.message_id


def register_command_handlers(application) -> None:
    """Register all command handlers."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))  # Undocumented fallback
    application.add_handler(CommandHandler("now", now_command))
