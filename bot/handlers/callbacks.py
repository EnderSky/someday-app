from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from bot.services.user_service import get_or_create_user, get_user_setting, get_user_theme, update_user_settings
from bot.services.task_service import (
    get_tasks_by_category,
    get_task_counts,
    get_task_by_id,
    update_task_category,
    complete_task,
    delete_task,
    update_task_shown,
    get_completed_tasks,
    get_completed_task_count,
)
from bot.services.shuffle_service import get_shuffled_tasks
from bot.utils.formatters import format_task_list, format_task_detail, format_settings, format_settings_now_limit, format_settings_theme, format_completed_list, format_settings_show_completed
from bot.utils.keyboards import get_main_keyboard, get_task_keyboard, get_settings_keyboard, get_task_list_keyboard, get_settings_now_limit_keyboard, get_settings_theme_keyboard, get_completed_list_keyboard, get_settings_show_completed_keyboard
from config.settings import settings


# Track currently displayed tasks per user for shuffle diversity
_user_current_display = {}


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all inline button callbacks."""
    query = update.callback_query
    await query.answer()
    
    telegram_id = update.effective_user.id
    user = get_or_create_user(telegram_id)
    data = query.data
    
    # View navigation
    if data == "view_now":
        await show_category_view(query, user, "now")
    elif data == "view_soon":
        await show_category_view(query, user, "soon")
    elif data == "view_someday":
        await show_category_view(query, user, "someday")
    
    # Shuffle
    elif data == "shuffle":
        await show_category_view(query, user, "now", shuffle=True)
    
    # Task detail view
    elif data.startswith("task_"):
        task_id = data.replace("task_", "")
        await show_task_detail(query, user, task_id)
    
    # Task actions
    elif data.startswith("complete_"):
        task_id = data.replace("complete_", "")
        await handle_complete_task(query, user, task_id)
    elif data.startswith("move_"):
        # Format: move_{task_id}_{target_category}
        parts = data.split("_")
        task_id = parts[1]
        target_category = parts[2]
        await handle_move_task(query, user, task_id, target_category)
    elif data.startswith("delete_"):
        task_id = data.replace("delete_", "")
        await handle_delete_task(query, user, task_id)
    
    # Settings
    elif data == "settings":
        await show_settings(query, user)
    elif data == "settings_now_limit":
        await show_settings_now_limit(query, user)
    elif data == "settings_theme":
        await show_settings_theme(query, user)
    elif data == "settings_show_completed":
        await show_settings_show_completed(query, user)
    elif data == "view_completed":
        await show_completed_list(query, user)
    elif data.startswith("set_limit_"):
        limit = int(data.replace("set_limit_", ""))
        await handle_set_limit(query, user, limit)
    elif data.startswith("set_theme_"):
        theme_id = data.replace("set_theme_", "")
        await handle_set_theme(query, user, theme_id)
    elif data == "set_show_completed_on":
        await handle_set_show_completed(query, user, True)
    elif data == "set_show_completed_off":
        await handle_set_show_completed(query, user, False)
    
    # Pagination
    elif data.startswith("page_soon_"):
        page = int(data.replace("page_soon_", ""))
        await show_category_view(query, user, "soon", page=page)
    elif data.startswith("page_someday_"):
        page = int(data.replace("page_someday_", ""))
        await show_category_view(query, user, "someday", page=page)
    elif data.startswith("page_completed_"):
        page = int(data.replace("page_completed_", ""))
        await show_completed_list(query, user, page=page)
    
    # No-op (for labels)
    elif data == "noop":
        pass


async def show_category_view(query, user: dict, category: str, shuffle: bool = False, page: int = 0) -> None:
    """Show tasks for a specific category.
    
    Args:
        query: Telegram callback query
        user: User dict
        category: Task category (now, soon, someday)
        shuffle: Whether to shuffle NOW tasks
        page: Page number for pagination (0-indexed, for soon/someday)
    """
    now_limit = get_user_setting(user, "now_display_limit", settings.DEFAULT_NOW_LIMIT)
    theme = get_user_theme(user)
    show_completed = bool(get_user_setting(user, "show_completed_button", False))
    
    counts = get_task_counts(user["id"])
    
    # Apply shuffle for NOW tasks
    if category == "now":
        tasks = get_tasks_by_category(user["id"], category)
        # Get current display tracking for this user
        current_display = _user_current_display.get(user["id"], [])
        
        if shuffle:
            # Use enhanced shuffle with current display exclusion
            display_tasks = get_shuffled_tasks(
                tasks, 
                now_limit or settings.DEFAULT_NOW_LIMIT, 
                currently_displayed=current_display
            )
        else:
            # For initial view, use basic shuffle or take first tasks
            if len(tasks) > now_limit:
                display_tasks = get_shuffled_tasks(
                    tasks, 
                    now_limit or settings.DEFAULT_NOW_LIMIT, 
                    currently_displayed=[]
                )
            else:
                display_tasks = tasks[:now_limit or settings.DEFAULT_NOW_LIMIT]
        
        # Update shown stats for displayed tasks
        for task in display_tasks:
            update_task_shown(task["id"])
        
        # Store current display for next shuffle
        _user_current_display[user["id"]] = [t["id"] for t in display_tasks]
        limit = now_limit
        total_count = counts.get(category, 0)
    else:
        # For soon/someday, use pagination
        offset = page * settings.DEFAULT_PAGE_SIZE
        display_tasks = get_tasks_by_category(
            user["id"], 
            category, 
            limit=settings.DEFAULT_PAGE_SIZE, 
            offset=offset
        )
        limit = None
        total_count = counts.get(category, 0)
    
    message, parse_mode = format_task_list(display_tasks, category, counts, limit=limit, theme=theme, page=page)
    keyboard = get_task_list_keyboard(
        display_tasks, 
        category, 
        counts=counts, 
        limit=limit, 
        show_completed=show_completed,
        page=page,
        total_count=total_count,
        page_size=settings.DEFAULT_PAGE_SIZE
    )
    
    await query.edit_message_text(message, reply_markup=keyboard, parse_mode=parse_mode)


async def show_task_detail(query, user: dict, task_id: str) -> None:
    """Show detail view for a specific task."""
    task = get_task_by_id(task_id)
    theme = get_user_theme(user)
    
    if not task:
        await query.edit_message_text("Task not found.")
        return
    
    message, parse_mode = format_task_detail(task, theme=theme)
    keyboard = get_task_keyboard(task_id, task["category"])
    
    await query.edit_message_text(message, reply_markup=keyboard, parse_mode=parse_mode)


async def handle_complete_task(query, user: dict, task_id: str) -> None:
    """Mark a task as completed with playful celebration."""
    import asyncio
    import random
    
    task = get_task_by_id(task_id)
    if not task:
        await query.edit_message_text("Task not found.")
        return
    
    category = task["category"]
    task_content = task["content"]
    complete_task(task_id)
    
    # Playful celebration messages
    celebrations = [
        "Nice one!",
        "Crushed it!",
        "One less thing!",
        "Done and dusted!",
        "You're on fire!",
        "Boom! Done.",
        "That's how it's done!",
        "Progress!",
    ]
    celebration = random.choice(celebrations)
    
    # Show celebration with task content
    await query.edit_message_text(f"✨ {celebration}\n📝 {task_content}")
    
    # Wait 2 seconds then return to category view
    await asyncio.sleep(2)
    await show_category_view(query, user, category)


async def handle_move_task(query, user: dict, task_id: str, target_category: str) -> None:
    """Move a task to a specific category."""
    task = get_task_by_id(task_id)
    if not task:
        await query.edit_message_text("Task not found.")
        return
    
    if target_category in ("now", "soon", "someday"):
        update_task_category(task_id, target_category)
        await show_task_detail(query, user, task_id)


async def handle_delete_task(query, user: dict, task_id: str) -> None:
    """Delete a task permanently."""
    task = get_task_by_id(task_id)
    if not task:
        await query.edit_message_text("Task not found.")
        return
    
    category = task["category"]
    delete_task(task_id)
    
    # Return to category view
    await show_category_view(query, user, category)


async def show_settings(query, user: dict) -> None:
    """Show settings main menu with category selection."""
    theme = get_user_theme(user)
    message, parse_mode = format_settings(user, theme=theme)
    keyboard = get_settings_keyboard()
    
    await query.edit_message_text(message, reply_markup=keyboard, parse_mode=parse_mode)


async def show_settings_now_limit(query, user: dict) -> None:
    """Show NOW display limit settings view."""
    theme = get_user_theme(user)
    now_limit = get_user_setting(user, "now_display_limit", settings.DEFAULT_NOW_LIMIT)
    
    message, parse_mode = format_settings_now_limit(user, theme=theme)
    keyboard = get_settings_now_limit_keyboard(now_limit or settings.DEFAULT_NOW_LIMIT)
    
    await query.edit_message_text(message, reply_markup=keyboard, parse_mode=parse_mode)


async def show_settings_theme(query, user: dict) -> None:
    """Show theme selection settings view."""
    theme = get_user_theme(user)
    
    message, parse_mode = format_settings_theme(theme, theme=theme)
    keyboard = get_settings_theme_keyboard(theme)
    
    await query.edit_message_text(message, reply_markup=keyboard, parse_mode=parse_mode)


async def show_settings_show_completed(query, user: dict) -> None:
    """Show the show completed button settings view."""
    theme = get_user_theme(user)
    is_enabled = get_user_setting(user, "show_completed_button", False)
    
    message, parse_mode = format_settings_show_completed(bool(is_enabled), theme=theme)
    keyboard = get_settings_show_completed_keyboard(bool(is_enabled))
    
    await query.edit_message_text(message, reply_markup=keyboard, parse_mode=parse_mode)


async def show_completed_list(query, user: dict, page: int = 0) -> None:
    """Show list of completed tasks, sorted by most recently completed.
    
    Args:
        query: Telegram callback query
        user: User dict
        page: Page number for pagination (0-indexed)
    """
    theme = get_user_theme(user)
    
    # Get total count first
    total_count = get_completed_task_count(user["id"])
    
    # Get completed tasks for this page (most recent first)
    offset = page * settings.DEFAULT_PAGE_SIZE
    tasks = get_completed_tasks(user["id"], limit=settings.DEFAULT_PAGE_SIZE, offset=offset)
    
    message, parse_mode = format_completed_list(tasks, total_count, theme=theme, page=page)
    keyboard = get_completed_list_keyboard(
        page=page,
        total_count=total_count,
        page_size=settings.DEFAULT_PAGE_SIZE
    )
    
    await query.edit_message_text(message, reply_markup=keyboard, parse_mode=parse_mode)


async def handle_set_limit(query, user: dict, limit: int) -> None:
    """Update NOW display limit setting."""
    current_settings = user.get("settings", {}) or {}
    current_settings["now_display_limit"] = limit
    
    update_user_settings(user["id"], current_settings)
    
    # Refresh user data and show updated NOW limit settings
    user["settings"] = current_settings
    await show_settings_now_limit(query, user)


async def handle_set_theme(query, user: dict, theme_id: str) -> None:
    """Update theme setting."""
    current_settings = user.get("settings", {}) or {}
    current_settings["theme"] = theme_id
    
    update_user_settings(user["id"], current_settings)
    
    # Refresh user data and show updated theme settings
    user["settings"] = current_settings
    await show_settings_theme(query, user)


async def handle_set_show_completed(query, user: dict, is_enabled: bool) -> None:
    """Update show completed button setting."""
    current_settings = user.get("settings", {}) or {}
    current_settings["show_completed_button"] = is_enabled
    
    update_user_settings(user["id"], current_settings)
    
    # Refresh user data and show updated settings
    user["settings"] = current_settings
    await show_settings_show_completed(query, user)


def register_callback_handlers(application) -> None:
    """Register callback query handlers."""
    application.add_handler(CallbackQueryHandler(handle_callback))
