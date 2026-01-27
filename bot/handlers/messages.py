import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.services.user_service import get_or_create_user
from bot.services.task_service import (
    create_task,
    get_task_by_message_id,
    update_task_content,
    get_task_counts,
)

logger = logging.getLogger(__name__)


async def handle_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-form messages - add as new task to Someday."""
    # Guard against None message (can happen with edited messages)
    if not update.message or not update.message.text:
        return
    
    telegram_id = update.effective_user.id
    message_id = update.message.message_id
    content = update.message.text.strip()
    
    if not content:
        return
    
    # Get or create user
    user = get_or_create_user(telegram_id)
    
    # Create task
    create_task(
        user_id=user["id"],
        content=content,
        telegram_message_id=message_id,
        category="someday"
    )
    
    # Get updated counts
    counts = get_task_counts(user["id"])
    
    # Send confirmation
    task_text = "task" if counts["someday"] == 1 else "tasks"
    await update.message.reply_text(
        f"✓ Added to someday ({counts['someday']} {task_text})"
    )


async def handle_edited_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle edited messages - update corresponding task if it exists and is active."""
    # Check if this is an edited message with text
    if not update.edited_message or not update.edited_message.text:
        return
    
    telegram_id = update.effective_user.id
    message_id = update.edited_message.message_id
    new_content = update.edited_message.text.strip()
    
    if not new_content:
        return
    
    # Get user
    user = get_or_create_user(telegram_id)
    
    # Find task by message ID
    task = get_task_by_message_id(user["id"], message_id)
    
    if task:
        # Task exists and is active - update it
        update_task_content(task["id"], new_content)
        
        # Reply to the original edited message
        await update.edited_message.reply_text(
            "✓ Task updated",
            reply_to_message_id=message_id
        )
    else:
        # Task not found - notify user
        await update.edited_message.reply_text(
            "Task not found. It may have been completed or deleted.",
            reply_to_message_id=message_id
        )


def register_message_handlers(application) -> None:
    """Register message handlers."""
    # Handle new text messages (not commands)
    # Explicitly exclude edited messages to prevent double handling
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE,
            handle_new_message
        )
    )
    
    # Handle edited messages - must include TEXT filter and exclude commands
    application.add_handler(
        MessageHandler(
            filters.UpdateType.EDITED_MESSAGE & filters.TEXT & ~filters.COMMAND,
            handle_edited_message
        )
    )
