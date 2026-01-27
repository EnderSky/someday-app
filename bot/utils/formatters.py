from datetime import datetime, timezone
from typing import Optional

# =============================================================================
# THEME CONSTANTS
# =============================================================================

THEME_CLASSIC = "classic"
THEME_MINIMAL = "minimal"
THEME_MONOSPACE = "monospace"

# Theme display names
THEME_NAMES = {
    THEME_CLASSIC: "Classic",
    THEME_MINIMAL: "Minimal",
    THEME_MONOSPACE: "Monospace"
}

# =============================================================================
# CATEGORY ICONS
# =============================================================================

# Category emojis (for non-monospace themes)
CATEGORY_EMOJI = {"now": "🔥", "soon": "⏳", "someday": "📦"}

# Category symbols (for monospace theme)
CATEGORY_SYMBOL = {"now": "[!]", "soon": "[~]", "someday": "[.]"}

# =============================================================================
# COMMON TEXT STRINGS
# =============================================================================

# View titles
TEXT_TASK = "TASK"
TEXT_SETTINGS = "SETTINGS"
TEXT_DISPLAY_LIMIT = "Display Limit"
TEXT_THEME = "THEME"

# Icons/symbols for views
ICON_TASK = "📌"
ICON_SETTINGS = "⚙️"
ICON_THEME = "🎨"
SYMBOL_TASK = "[*]"
SYMBOL_SETTINGS = "[=]"
SYMBOL_THEME = "[#]"

# Labels
TEXT_SHOWN = "Shown"
TEXT_CURRENT = "Current"
TEXT_SELECT_CATEGORY = "Select a category:"
TEXT_SELECT_TASKS = "Select tasks below."

# Display limit description
TEXT_LIMIT_DESC_LINE1 = "Tasks shown at once"
TEXT_LIMIT_DESC_LINE2 = "in NOW view."
TEXT_LIMIT_DESC_FULL = "How many tasks to show at once in NOW view."

# Theme description
TEXT_THEME_DESC_LINE1 = "Choose your visual"
TEXT_THEME_DESC_LINE2 = "style."
TEXT_THEME_DESC_FULL = "Choose your preferred visual style."

# Empty state messages per category
EMPTY_MESSAGES = {
    "now": {
        "short": ("✨ All clear!", "Nothing urgent."),
        "full": "✨ All clear! Nothing urgent now.",
        "mono": ("* All clear!", "Nothing urgent now.")
    },
    "soon": {
        "short": ("Nothing here yet.", "Promote when ready."),
        "full": "Nothing here yet. Promote tasks when ready.",
        "mono": ("Nothing here yet.", "Promote tasks when ready.")
    },
    "someday": {
        "short": ("List is empty.", "Send msg to add."),
        "full": "Your list is empty. Send a message to add.",
        "mono": ("Your list is empty.", "Send a message to add.")
    }
}

DEFAULT_EMPTY = {
    "short": ("No tasks yet.", ""),
    "full": "No tasks yet.",
    "mono": ("No tasks yet.", "")
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_task_age(created_at) -> str:
    """Get human-readable task age."""
    if not created_at:
        return ""
    
    if isinstance(created_at, str):
        created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    else:
        created_dt = created_at
    
    now = datetime.now(timezone.utc)
    delta = now - created_dt
    
    if delta.days == 0:
        return "today"
    elif delta.days == 1:
        return "yesterday"
    else:
        return f"{delta.days}d ago"


def _get_display_counts(tasks: list, counts: dict, category: str, limit: Optional[int]) -> tuple[int, int]:
    """Get displayed and total task counts."""
    total = counts.get(category, len(tasks))
    displayed = min(len(tasks), limit) if limit else min(len(tasks), 10)
    return displayed, total


def _get_display_tasks(tasks: list, limit: Optional[int]) -> list:
    """Get list of tasks to display."""
    return tasks[:limit] if limit else tasks[:10]


def _build_task_meta(category: str, created_at, use_emoji: bool = True, separator: str = " · ") -> str:
    """Build task metadata string (category + age)."""
    if use_emoji:
        icon = CATEGORY_EMOJI.get(category, "📋")
    else:
        icon = CATEGORY_SYMBOL.get(category, "[?]")
    
    meta = f"{icon} {category.capitalize()}"
    age = _get_task_age(created_at)
    if age:
        meta += f"{separator}Added {age}"
    return meta


# =============================================================================
# PUBLIC API
# =============================================================================

def format_task_list(tasks: list, category: str, counts: dict, limit: Optional[int] = None, theme: str = THEME_CLASSIC) -> tuple[str, Optional[str]]:
    """
    Format a list of tasks for display.
    
    Returns:
        tuple: (message_text, parse_mode) - parse_mode is "Markdown" for monospace, None otherwise
    """
    if theme == THEME_MINIMAL:
        return _format_task_list_minimal(tasks, category, counts, limit), None
    elif theme == THEME_MONOSPACE:
        return _format_task_list_monospace(tasks, category, counts, limit), "Markdown"
    else:  # classic
        return _format_task_list_classic(tasks, category, counts, limit), None


def format_task_detail(task: dict, theme: str = THEME_CLASSIC) -> tuple[str, Optional[str]]:
    """
    Format a single task for detail view.
    
    Returns:
        tuple: (message_text, parse_mode)
    """
    if theme == THEME_MINIMAL:
        return _format_task_detail_minimal(task), None
    elif theme == THEME_MONOSPACE:
        return _format_task_detail_monospace(task), "Markdown"
    else:  # classic
        return _format_task_detail_classic(task), None


def format_settings(user: dict, theme: str = THEME_CLASSIC) -> tuple[str, Optional[str]]:
    """
    Format settings main menu view.
    
    Returns:
        tuple: (message_text, parse_mode)
    """
    if theme == THEME_MINIMAL:
        return _format_settings_minimal(), None
    elif theme == THEME_MONOSPACE:
        return _format_settings_monospace(), "Markdown"
    else:  # classic
        return _format_settings_classic(), None


def format_settings_now_limit(user: dict, theme: str = THEME_CLASSIC) -> tuple[str, Optional[str]]:
    """Format NOW display limit settings view."""
    settings_data = user.get("settings", {}) or {}
    now_limit = settings_data.get("now_display_limit", 3)
    
    if theme == THEME_MINIMAL:
        return _format_now_limit_minimal(now_limit), None
    elif theme == THEME_MONOSPACE:
        return _format_now_limit_monospace(now_limit), "Markdown"
    else:  # classic
        return _format_now_limit_classic(now_limit), None


def format_settings_theme(current_theme: str, theme: str = THEME_CLASSIC) -> tuple[str, Optional[str]]:
    """Format theme settings view."""
    if theme == THEME_MINIMAL:
        return _format_theme_minimal(current_theme), None
    elif theme == THEME_MONOSPACE:
        return _format_theme_monospace(current_theme), "Markdown"
    else:  # classic
        return _format_theme_classic(current_theme), None


# =============================================================================
# CLASSIC THEME
# =============================================================================

CLASSIC_BOX_WIDTH = 15

# Rounded edges box components
ROUND_CLASSIC_TOP = f"╭{'─' * CLASSIC_BOX_WIDTH}╮"
ROUND_CLASSIC_MID = f"├{'─' * CLASSIC_BOX_WIDTH}┤"
ROUND_CLASSIC_BOT = f"╰{'─' * CLASSIC_BOX_WIDTH}╯"

# Square edges box components
SQUARE_CLASSIC_TOP = f"┌{'─' * CLASSIC_BOX_WIDTH}┐"
SQUARE_CLASSIC_MID = f"├{'─' * CLASSIC_BOX_WIDTH}┤"
SQUARE_CLASSIC_BOT = f"└{'─' * CLASSIC_BOX_WIDTH}┘"

CLASSIC_SIDE = "  "

CLASSIC_TOP = SQUARE_CLASSIC_TOP
CLASSIC_MID = SQUARE_CLASSIC_MID
CLASSIC_BOT = SQUARE_CLASSIC_BOT

def _format_task_list_classic(tasks: list, category: str, counts: dict, limit: Optional[int] = None) -> str:
    emoji = CATEGORY_EMOJI.get(category, "📋")
    displayed, total = _get_display_counts(tasks, counts, category, limit)
    
    # title_dash_number = CLASSIC_BOX_WIDTH - len(f" {emoji} {category.upper()} ")
    # title = f"┌{'─' * (title_dash_number // 2)} {emoji} {category.upper()} {'─' * (title_dash_number - title_dash_number // 2)}┐"
    
    # shown_dash_number = CLASSIC_BOX_WIDTH - len(f" {TEXT_SHOWN}: {displayed}/{total} ") + 3
    # shown_line = f"├{'─' * (shown_dash_number // 2)} {TEXT_SHOWN}: {displayed}/{total} {'─' * (shown_dash_number - shown_dash_number // 2)}┤"
    # lines = [title, 
    #          shown_line]

    lines = [
        CLASSIC_TOP,
        f"{CLASSIC_SIDE} {emoji} {category.upper()}",
        f"{CLASSIC_SIDE} {TEXT_SHOWN}: {displayed}/{total}",
        CLASSIC_MID,
    ]
    
    if not tasks:
        msg = EMPTY_MESSAGES.get(category, DEFAULT_EMPTY)["short"]
        lines.extend([
            CLASSIC_SIDE,
            f"{CLASSIC_SIDE} {msg[0]}",
            f"{CLASSIC_SIDE} {msg[1]}",
            CLASSIC_SIDE,
        ])
    else:
        display_tasks = _get_display_tasks(tasks, limit)
        lines.append(CLASSIC_SIDE)
        for i, task in enumerate(display_tasks, 1):
            lines.append(f"{CLASSIC_SIDE} [{i}]  {task['content']}")
        
        remaining = total - len(display_tasks)
        if remaining > 0:
            lines.extend([CLASSIC_SIDE, f"{CLASSIC_SIDE} +{remaining} more"])
        lines.append(CLASSIC_SIDE)
        
        if tasks:
            lines.extend([CLASSIC_SIDE + " " + TEXT_SELECT_TASKS])
    
    lines.append(CLASSIC_BOT)
    
    return "\n".join(lines)


def _format_task_detail_classic(task: dict) -> str:
    content = task["content"]
    category = task.get("category", "someday")
    created_at = task.get("created_at")
    meta = _build_task_meta(category, created_at)
    
    return "\n".join([
        CLASSIC_TOP,
        f"{CLASSIC_SIDE} {ICON_TASK} {TEXT_TASK}",
        CLASSIC_MID,
        CLASSIC_SIDE,
        f"{CLASSIC_SIDE} {content}",
        CLASSIC_SIDE,
        f"{CLASSIC_SIDE} {meta}",
        CLASSIC_BOT,
    ])


def _format_settings_classic() -> str:
    return "\n".join([
        CLASSIC_TOP,
        f"{CLASSIC_SIDE} {ICON_SETTINGS} {TEXT_SETTINGS}",
        CLASSIC_MID,
        CLASSIC_SIDE,
        f"{CLASSIC_SIDE} {TEXT_SELECT_CATEGORY}",
        CLASSIC_SIDE,
        CLASSIC_BOT,
    ])


def _format_now_limit_classic(now_limit: int) -> str:
    return "\n".join([
        CLASSIC_TOP,
        f"{CLASSIC_SIDE} {ICON_SETTINGS} {TEXT_DISPLAY_LIMIT}",
        CLASSIC_MID,
        CLASSIC_SIDE,
        f"{CLASSIC_SIDE} {TEXT_CURRENT}: {now_limit}",
        CLASSIC_SIDE,
        f"{CLASSIC_SIDE} {TEXT_LIMIT_DESC_LINE1}",
        f"{CLASSIC_SIDE} {TEXT_LIMIT_DESC_LINE2}",
        CLASSIC_SIDE,
        CLASSIC_BOT,
    ])


def _format_theme_classic(current_theme: str) -> str:
    current_name = THEME_NAMES.get(current_theme, "Classic")
    return "\n".join([
        CLASSIC_TOP,
        f"{CLASSIC_SIDE} {ICON_THEME} {TEXT_THEME}",
        CLASSIC_MID,
        CLASSIC_SIDE,
        f"{CLASSIC_SIDE} {TEXT_CURRENT}: {current_name}",
        CLASSIC_SIDE,
        f"{CLASSIC_SIDE} {TEXT_THEME_DESC_LINE1}",
        f"{CLASSIC_SIDE} {TEXT_THEME_DESC_LINE2}",
        CLASSIC_SIDE,
        CLASSIC_BOT,
    ])


# =============================================================================
# MINIMAL THEME
# =============================================================================

MINIMAL_DIVIDER = "───────────────"


def _format_task_list_minimal(tasks: list, category: str, counts: dict, limit: Optional[int] = None) -> str:
    emoji = CATEGORY_EMOJI.get(category, "📋")
    displayed, total = _get_display_counts(tasks, counts, category, limit)
    
    lines = [
        f"{emoji} {category.upper()}",
        f"{TEXT_SHOWN}: {displayed}/{total}",
        MINIMAL_DIVIDER,
        "",
    ]
    
    if not tasks:
        lines.append(EMPTY_MESSAGES.get(category, DEFAULT_EMPTY)["full"])
    else:
        display_tasks = _get_display_tasks(tasks, limit)
        for i, task in enumerate(display_tasks, 1):
            lines.append(f"[{i}]  {task['content']}")
        
        remaining = total - len(display_tasks)
        if remaining > 0:
            lines.extend(["", f"+{remaining} more"])
        
        lines.extend(["", TEXT_SELECT_TASKS])
    
    return "\n".join(lines)


def _format_task_detail_minimal(task: dict) -> str:
    content = task["content"]
    category = task.get("category", "someday")
    created_at = task.get("created_at")
    meta = _build_task_meta(category, created_at)
    
    return "\n".join([
        f"{ICON_TASK} {TEXT_TASK}",
        MINIMAL_DIVIDER,
        "",
        content,
        "",
        meta,
    ])


def _format_settings_minimal() -> str:
    return "\n".join([
        f"{ICON_SETTINGS} {TEXT_SETTINGS}",
        MINIMAL_DIVIDER,
        "",
        TEXT_SELECT_CATEGORY,
    ])


def _format_now_limit_minimal(now_limit: int) -> str:
    return "\n".join([
        f"{ICON_SETTINGS} {TEXT_DISPLAY_LIMIT}",
        MINIMAL_DIVIDER,
        "",
        f"{TEXT_CURRENT}: {now_limit}",
        "",
        TEXT_LIMIT_DESC_FULL,
    ])


def _format_theme_minimal(current_theme: str) -> str:
    current_name = THEME_NAMES.get(current_theme, "Classic")
    return "\n".join([
        f"{ICON_THEME} {TEXT_THEME}",
        MINIMAL_DIVIDER,
        "",
        f"{TEXT_CURRENT}: {current_name}",
        "",
        TEXT_THEME_DESC_FULL,
    ])


# =============================================================================
# MONOSPACE THEME
# =============================================================================

MONO_BOX_WIDTH = 30


def _pad(text: str, width: int = MONO_BOX_WIDTH) -> str:
    """Pad text to fixed width for monospace alignment."""
    return text[:width].ljust(width)


def _mono_box_top() -> str:
    return f"┌{'─' * MONO_BOX_WIDTH}┐"


def _mono_box_mid() -> str:
    return f"├{'─' * MONO_BOX_WIDTH}┤"


def _mono_box_bot() -> str:
    return f"└{'─' * MONO_BOX_WIDTH}┘"


def _mono_line(text: str = "") -> str:
    return f"│{_pad(text)}│"


def _format_task_list_monospace(tasks: list, category: str, counts: dict, limit: Optional[int] = None) -> str:
    symbol = CATEGORY_SYMBOL.get(category, "[?]")
    displayed, total = _get_display_counts(tasks, counts, category, limit)
    
    lines = [
        "```",
        _mono_box_top(),
        _mono_line(f"  {symbol} {category.upper()}"),
        _mono_line(f"  {TEXT_SHOWN}: {displayed}/{total}"),
        _mono_box_mid(),
    ]
    
    if not tasks:
        msg = EMPTY_MESSAGES.get(category, DEFAULT_EMPTY)["mono"]
        lines.extend([
            _mono_line(),
            _mono_line(f"  {msg[0]}"),
            _mono_line(f"  {msg[1]}"),
            _mono_line(),
        ])
    else:
        display_tasks = _get_display_tasks(tasks, limit)
        lines.append(_mono_line())
        for i, task in enumerate(display_tasks, 1):
            content = task["content"]
            max_len = MONO_BOX_WIDTH - 8
            if len(content) > max_len:
                content = content[:max_len - 2] + ".."
            lines.append(_mono_line(f"  [{i}]  {content}"))
        
        remaining = total - len(display_tasks)
        if remaining > 0:
            lines.extend([_mono_line(), _mono_line(f"  +{remaining} more")])
        lines.append(_mono_line())
    
    lines.extend([_mono_box_bot(), "```"])
    
    if tasks:
        lines.extend([TEXT_SELECT_TASKS])
    
    return "\n".join(lines)


def _format_task_detail_monospace(task: dict) -> str:
    content = task["content"]
    category = task.get("category", "someday")
    created_at = task.get("created_at")
    meta = _build_task_meta(category, created_at, use_emoji=False, separator=" - ")
    
    lines = [
        "```",
        _mono_box_top(),
        _mono_line(f"  {SYMBOL_TASK} {TEXT_TASK}"),
        _mono_box_mid(),
        _mono_line(),
    ]
    
    # Word wrap content
    max_len = MONO_BOX_WIDTH - 4
    if len(content) <= max_len:
        lines.append(_mono_line(f"  {content}"))
    else:
        words = content.split()
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= max_len:
                current_line = f"{current_line} {word}".strip()
            else:
                if current_line:
                    lines.append(_mono_line(f"  {current_line}"))
                current_line = word
        if current_line:
            lines.append(_mono_line(f"  {current_line}"))
    
    lines.extend([
        _mono_line(),
        _mono_line(f"  {meta}"),
        _mono_box_bot(),
        "```",
    ])
    
    return "\n".join(lines)


def _format_settings_monospace() -> str:
    return "\n".join([
        "```",
        _mono_box_top(),
        _mono_line(f"  {SYMBOL_SETTINGS} {TEXT_SETTINGS}"),
        _mono_box_mid(),
        _mono_line(),
        _mono_line(f"  {TEXT_SELECT_CATEGORY}"),
        _mono_line(),
        _mono_box_bot(),
        "```",
    ])


def _format_now_limit_monospace(now_limit: int) -> str:
    return "\n".join([
        "```",
        _mono_box_top(),
        _mono_line(f"  {SYMBOL_SETTINGS} {TEXT_DISPLAY_LIMIT}"),
        _mono_box_mid(),
        _mono_line(),
        _mono_line(f"  {TEXT_CURRENT}: {now_limit}"),
        _mono_line(),
        _mono_line(f"  {TEXT_LIMIT_DESC_LINE1}"),
        _mono_line(f"  {TEXT_LIMIT_DESC_LINE2}"),
        _mono_line(),
        _mono_box_bot(),
        "```",
    ])


def _format_theme_monospace(current_theme: str) -> str:
    current_name = THEME_NAMES.get(current_theme, "Classic")
    return "\n".join([
        "```",
        _mono_box_top(),
        _mono_line(f"  {SYMBOL_THEME} {TEXT_THEME}"),
        _mono_box_mid(),
        _mono_line(),
        _mono_line(f"  {TEXT_CURRENT}: {current_name}"),
        _mono_line(),
        _mono_line(f"  {TEXT_THEME_DESC_LINE1}"),
        _mono_line(f"  {TEXT_THEME_DESC_LINE2}"),
        _mono_line(),
        _mono_box_bot(),
        "```",
    ])
