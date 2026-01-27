from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Optional

def get_main_keyboard(current_view: str = "now", counts: Optional[dict] = None) -> InlineKeyboardMarkup:
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
    
    buttons.append([InlineKeyboardButton("⚙️ Settings", callback_data="settings")])
    
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


def get_task_list_keyboard(tasks: list, category: str, counts: Optional[dict] = None) -> InlineKeyboardMarkup:
    """Get keyboard with compact numbered buttons for task selection."""
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
        buttons.append([InlineKeyboardButton("🔀 Shuffle Tasks Shown", callback_data="shuffle")])
        buttons.append([
            InlineKeyboardButton(f"⏳ Soon ({soon_count})", callback_data="view_soon"),
            InlineKeyboardButton(f"📦 Someday ({someday_count})", callback_data="view_someday"),
        ])
    elif category == "soon":
        buttons.append([
            InlineKeyboardButton(f"🔥 Now ({now_count})", callback_data="view_now"),
            InlineKeyboardButton(f"📦 Someday ({someday_count})", callback_data="view_someday"),
        ])
    elif category == "someday":
        buttons.append([
            InlineKeyboardButton(f"🔥 Now ({now_count})", callback_data="view_now"),
            InlineKeyboardButton(f"⏳ Soon ({soon_count})", callback_data="view_soon"),
        ])
    
    buttons.append([InlineKeyboardButton("⚙️ Settings", callback_data="settings")])
    
    return InlineKeyboardMarkup(buttons)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for main settings menu - category selection."""
    buttons = [
        [InlineKeyboardButton("🔢 Display Limit", callback_data="settings_now_limit")],
        [InlineKeyboardButton("🎨 Theme", callback_data="settings_theme")],
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
