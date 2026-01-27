from typing import Optional
from bot.db.supabase_client import get_client


def create_task(user_id: str, content: str, telegram_message_id: int, category: str = "someday") -> dict:
    """Create a new task."""
    client = get_client()
    task = {
        "user_id": user_id,
        "content": content,
        "telegram_message_id": telegram_message_id,
        "category": category,
    }
    response = client.table("tasks").insert(task).execute()
    return response.data[0]


def get_tasks_by_category(user_id: str, category: str) -> list:
    """Get all active tasks for a user in a specific category."""
    client = get_client()
    response = (
        client.table("tasks")
        .select("*")
        .eq("user_id", user_id)
        .eq("category", category)
        .is_("completed_at", "null")
        .order("created_at", desc=False)
        .execute()
    )
    return response.data


def get_task_counts(user_id: str) -> dict:
    """Get count of active tasks in each category."""
    client = get_client()
    
    counts = {"now": 0, "soon": 0, "someday": 0}
    
    for category in counts.keys():
        response = (
            client.table("tasks")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("category", category)
            .is_("completed_at", "null")
            .execute()
        )
        counts[category] = response.count or 0
    
    return counts


def get_task_by_id(task_id: str) -> Optional[dict]:
    """Get a task by its ID."""
    client = get_client()
    response = client.table("tasks").select("*").eq("id", task_id).execute()
    return response.data[0] if response.data else None


def get_task_by_message_id(user_id: str, telegram_message_id: int) -> Optional[dict]:
    """Get an active task by its original Telegram message ID."""
    client = get_client()
    response = (
        client.table("tasks")
        .select("*")
        .eq("user_id", user_id)
        .eq("telegram_message_id", telegram_message_id)
        .is_("completed_at", "null")
        .execute()
    )
    return response.data[0] if response.data else None


def update_task_content(task_id: str, content: str) -> dict:
    """Update task content (for edit detection)."""
    client = get_client()
    response = client.table("tasks").update({"content": content}).eq("id", task_id).execute()
    return response.data[0]


def update_task_category(task_id: str, category: str) -> dict:
    """Move task to a different category (promote/demote)."""
    client = get_client()
    response = client.table("tasks").update({"category": category}).eq("id", task_id).execute()
    return response.data[0]


def complete_task(task_id: str) -> dict:
    """Mark a task as completed."""
    client = get_client()
    from datetime import datetime, timezone
    
    response = (
        client.table("tasks")
        .update({"completed_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", task_id)
        .execute()
    )
    return response.data[0]


def delete_task(task_id: str) -> None:
    """Permanently delete a task."""
    client = get_client()
    client.table("tasks").delete().eq("id", task_id).execute()


def update_task_shown(task_id: str) -> dict:
    """Update shown_count and last_shown_at when task is displayed."""
    client = get_client()
    from datetime import datetime, timezone
    
    # Get current task to increment shown_count
    task = get_task_by_id(task_id)
    if not task:
        return {}
    
    response = (
        client.table("tasks")
        .update({
            "shown_count": (task.get("shown_count", 0) or 0) + 1,
            "last_shown_at": datetime.now(timezone.utc).isoformat()
        })
        .eq("id", task_id)
        .execute()
    )
    return response.data[0]
