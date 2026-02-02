from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Optional

def get_main_keyboard(current_view: str = "now", counts: Optional[dict] = None, show_completed: bool = False) -> InlineKeyboardMarkup:
    """Get the main navigation keyboard based on current view."""
    counts = counts or {}
    buttons = []
    
    now_count = counts.get("now", 0)
    soon_count = counts.get("soon", 0)
    someday_count = counts.get("someday", 0)
    
    if current_view == "now":
        buttons.append([InlineKeyboardButton("🔀 Shuffle Tasks Shown", callback_data="shuffle")])
        buttons.append([
            InlineKeyboardButton(f"⏳ Soon ({soon_count})", callback_data="view_soon"),
            InlineKeyboardButton(f"📦 Someday ({someday_count})", callback_data="view_someday"),
        ])
    elif current_view == "soon":
        buttons.append([
            InlineKeyboardButton(f"🔥 Now ({now_count})", callback_data="view_now"),
            InlineKeyboardButton(f"📦 Someday ({someday_count})", callback_data="view_someday"),
        ])
    elif current_view == "someday":
        buttons.append([
            InlineKeyboardButton(f"🔥 Now ({now_count})", callback_data="view_now"),
            InlineKeyboardButton(f"⏳ Soon ({soon_count})", callback_data="view_soon"),
        ])
    
    # Bottom row: Completed (if enabled) + Settings
    bottom_row = []
    if show_completed:
        bottom_row.append(InlineKeyboardButton("✅ Completed", callback_data="view_completed"))
    bottom_row.append(InlineKeyboardButton("⚙️ Settings", callback_data="settings"))
    buttons.append(bottom_row)
    
    return InlineKeyboardMarkup(buttons)


def get_task_keyboard(task_id: str, category: str) -> InlineKeyboardMarkup:
    """Get keyboard for task detail view with move options based on category."""
    buttons = []
    
    # First row: Move actions with clear labels
    row1 = []
    if category == "now":
        row1.append(InlineKeyboardButton("📥 Move to Soon", callback_data=f"move_{task_id}_soon"))
        row1.append(InlineKeyboardButton("📥 Move to Someday", callback_data=f"move_{task_id}_someday"))
    elif category == "soon":
        row1.append(InlineKeyboardButton("📤 Move to Now", callback_data=f"move_{task_id}_now"))
        row1.append(InlineKeyboardButton("📥 Move to Someday", callback_data=f"move_{task_id}_someday"))
    elif category == "someday":
        row1.append(InlineKeyboardButton("📤 Move to Now", callback_data=f"move_{task_id}_now"))
        row1.append(InlineKeyboardButton("📤 Move to Soon", callback_data=f"move_{task_id}_soon"))
    
    buttons.append(row1)
    
    # Second row: Mark As Done and Delete with emojis
    buttons.append([
        InlineKeyboardButton("✅ Mark As Done", callback_data=f"complete_{task_id}"),
        InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{task_id}")
    ])
    
    # Third row: Back
    buttons.append([InlineKeyboardButton("← Back", callback_data=f"view_{category}")])
    
    return InlineKeyboardMarkup(buttons)


def get_task_list_keyboard(
    tasks: list, 
    category: str, 
    counts: Optional[dict] = None, 
    limit: Optional[int] = None, 
    show_completed: bool = False,
    page: int = 0,
    total_count: Optional[int] = None,
    page_size: int = 10
) -> InlineKeyboardMarkup:
    """Get keyboard with compact numbered buttons for task selection.
    
    Args:
        tasks: List of tasks to display
        category: Task category (now, soon, someday)
        counts: Dict with total counts per category
        limit: Display limit (for NOW category)
        show_completed: Whether to show completed button
        page: Current page number (0-indexed, for soon/someday)
        total_count: Total number of tasks for pagination
        page_size: Number of tasks per page
    """
    counts = counts or {}
    buttons = []
    
    now_count = counts.get("now", 0)
    soon_count = counts.get("soon", 0)
    someday_count = counts.get("someday", 0)
    
    # Compact numbered task selection buttons (up to 10, in rows of 5)
    if tasks:
        task_buttons = []
        for i, task in enumerate(tasks[:10], 1):
            task_id = task["id"]
            task_buttons.append(InlineKeyboardButton(str(i), callback_data=f"task_{task_id}"))
        
        # Split into rows of 5 buttons each
        for j in range(0, len(task_buttons), 5):
            buttons.append(task_buttons[j:j+5])
    
    # Navigation buttons with counts
    if category == "now":
        # Only show shuffle when not all NOW tasks are displayed
        total_now = counts.get("now", len(tasks))
        should_show_shuffle = limit and len(tasks) < total_now
        
        if should_show_shuffle:
            buttons.append([InlineKeyboardButton("🔀 Shuffle Tasks Shown", callback_data="shuffle")])
        
        buttons.append([
            InlineKeyboardButton(f"⏳ Soon ({soon_count})", callback_data="view_soon"),
            InlineKeyboardButton(f"📦 Someday ({someday_count})", callback_data="view_someday"),
        ])
    elif category == "soon":
        # Add pagination buttons if needed
        category_total = total_count if total_count is not None else counts.get("soon", 0)
        if category_total > page_size:
            pagination_row = _get_pagination_buttons(page, category_total, page_size, f"page_soon")
            if pagination_row:
                buttons.append(pagination_row)
        
        buttons.append([
            InlineKeyboardButton(f"🔥 Now ({now_count})", callback_data="view_now"),
            InlineKeyboardButton(f"📦 Someday ({someday_count})", callback_data="view_someday"),
        ])
    elif category == "someday":
        # Add pagination buttons if needed
        category_total = total_count if total_count is not None else counts.get("someday", 0)
        if category_total > page_size:
            pagination_row = _get_pagination_buttons(page, category_total, page_size, f"page_someday")
            if pagination_row:
                buttons.append(pagination_row)
        
        buttons.append([
            InlineKeyboardButton(f"🔥 Now ({now_count})", callback_data="view_now"),
            InlineKeyboardButton(f"⏳ Soon ({soon_count})", callback_data="view_soon"),
        ])
    
    # Bottom row: Completed (if enabled) + Settings
    bottom_row = []
    if show_completed:
        bottom_row.append(InlineKeyboardButton("✅ Completed", callback_data="view_completed"))
    bottom_row.append(InlineKeyboardButton("⚙️ Settings", callback_data="settings"))
    buttons.append(bottom_row)
    
    return InlineKeyboardMarkup(buttons)


def _get_pagination_buttons(page: int, total_count: int, page_size: int, callback_prefix: str) -> list:
    """Get pagination buttons (Prev/Next) based on current page and total items.
    
    Args:
        page: Current page (0-indexed)
        total_count: Total number of items
        page_size: Items per page
        callback_prefix: Prefix for callback data (e.g., "page_soon", "page_completed")
    
    Returns:
        List of InlineKeyboardButton for pagination, or empty list if not needed
    """
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    
    if total_pages <= 1:
        return []
    
    buttons = []
    
    # Previous button
    if page > 0:
        buttons.append(InlineKeyboardButton("← Prev", callback_data=f"{callback_prefix}_{page - 1}"))
    
    # Page indicator (non-clickable, using noop)
    buttons.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    
    # Next button
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton("Next →", callback_data=f"{callback_prefix}_{page + 1}"))
    
    return buttons


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for main settings menu - category selection."""
    buttons = [
        [InlineKeyboardButton("🔢 Display Limit", callback_data="settings_now_limit")],
        [InlineKeyboardButton("🎨 Theme", callback_data="settings_theme")],
        [InlineKeyboardButton("✅ Show Completed Button", callback_data="settings_show_completed")],
        [InlineKeyboardButton("← Back", callback_data="view_now")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_settings_now_limit_keyboard(current_limit: int) -> InlineKeyboardMarkup:
    """Get keyboard for NOW display limit settings."""
    buttons = []
    
    # NOW limit options (1-5 range)
    limit_row = []
    for limit in [1, 2, 3, 4, 5]:
        label = f"[{limit}]" if limit == current_limit else str(limit)
        limit_row.append(InlineKeyboardButton(label, callback_data=f"set_limit_{limit}"))
    
    buttons.append(limit_row)
    buttons.append([InlineKeyboardButton("← Back", callback_data="settings")])
    
    return InlineKeyboardMarkup(buttons)


def get_settings_theme_keyboard(current_theme: str) -> InlineKeyboardMarkup:
    """Get keyboard for theme selection."""
    themes = [
        ("classic", "Classic"),
        ("minimal", "Minimal"),
        ("monospace", "Monospace"),
    ]
    
    buttons = []
    for theme_id, theme_name in themes:
        label = f"[{theme_name}]" if theme_id == current_theme else theme_name
        buttons.append([InlineKeyboardButton(label, callback_data=f"set_theme_{theme_id}")])
    
    buttons.append([InlineKeyboardButton("← Back", callback_data="settings")])
    
    return InlineKeyboardMarkup(buttons)


def get_completed_list_keyboard(
    page: int = 0,
    total_count: int = 0,
    page_size: int = 10
) -> InlineKeyboardMarkup:
    """Get keyboard for completed tasks list view with pagination.
    
    Args:
        page: Current page (0-indexed)
        total_count: Total number of completed tasks
        page_size: Number of tasks per page
    """
    buttons = []
    
    # Add pagination buttons if needed
    if total_count > page_size:
        pagination_row = _get_pagination_buttons(page, total_count, page_size, "page_completed")
        if pagination_row:
            buttons.append(pagination_row)
    
    buttons.append([InlineKeyboardButton("← Back", callback_data="view_now")])
    return InlineKeyboardMarkup(buttons)


def get_settings_show_completed_keyboard(is_enabled: bool) -> InlineKeyboardMarkup:
    """Get keyboard for show completed button toggle."""
    on_label = "[On]" if is_enabled else "On"
    off_label = "[Off]" if not is_enabled else "Off"
    
    buttons = [
        [
            InlineKeyboardButton(on_label, callback_data="set_show_completed_on"),
            InlineKeyboardButton(off_label, callback_data="set_show_completed_off"),
        ],
        [InlineKeyboardButton("← Back", callback_data="settings")]
    ]
    return InlineKeyboardMarkup(buttons)
