import random
from datetime import datetime, timezone


def get_shuffled_tasks(tasks: list, limit: int, currently_displayed: list = None) -> list:
    """
    Enhanced shuffle that prioritizes not-currently-shown tasks.
    
    Algorithm:
    1. Exclude currently displayed tasks if possible (highest priority)
    2. Prioritize never-shown tasks from remaining pool
    3. For large pools (> 2x limit): implement semi-random cycling with rotation bias
    4. For small pools: maximize diversity, allow minimal repeats when necessary
    5. Fallback: include currently displayed tasks only when no other options
    
    Args:
        tasks: All available tasks in the category
        limit: Number of tasks to display
        currently_displayed: List of task IDs currently on screen
    """
    if not tasks:
        return []
    
    # Convert currently_displayed to set for faster lookup
    current_display_ids = set(currently_displayed or [])
    total_tasks = len(tasks)
    
    # Step 1: Separate tasks by priority
    not_currently_shown = [t for t in tasks if t["id"] not in current_display_ids]
    currently_shown = [t for t in tasks if t["id"] in current_display_ids]
    
    # Step 2: Further categorize not-currently-shown tasks
    never_shown = [t for t in not_currently_shown if (t.get("shown_count") or 0) == 0]
    shown_before = [t for t in not_currently_shown if (t.get("shown_count") or 0) > 0]
    
    result = []
    
    # Step 3: Try to fill with not-currently-shown tasks first
    if not_currently_shown:
        # Shuffle each category for randomness
        if never_shown:
            random.shuffle(never_shown)
            result.extend(never_shown)
        if shown_before:
            # Apply cycling logic for shown tasks
            cycled_shown = _apply_cycling_logic(shown_before, limit - len(result), total_tasks)
            result.extend(cycled_shown)
        
        # Limit to requested number
        result = result[:limit]
    
    # Step 4: If we don't have enough tasks, include currently displayed ones
    if len(result) < limit and currently_shown:
        remaining_slots = limit - len(result)
        
        # Prioritize currently shown tasks that were shown least recently
        currently_shown_sorted = _sort_by_recency(currently_shown)
        result.extend(currently_shown_sorted[:remaining_slots])
    
    # Step 5: Final limit and shuffle for randomness
    result = result[:limit]
    random.shuffle(result)
    
    return result

def _apply_cycling_logic(tasks: list, limit: int, total_pool_size: int) -> list:
    """
    Apply semi-random cycling logic for task selection.
    
    For large pools (> 2x limit): implement rotation bias
    For small pools: maximize diversity
    """
    if not tasks:
        return []
    
    # Determine if we're dealing with a large pool
    is_large_pool = total_pool_size > (limit * 2)
    
    if is_large_pool:
        return _apply_large_pool_cycling(tasks, limit, total_pool_size)
    else:
        return _apply_small_pool_diversity(tasks, limit)
def _apply_large_pool_cycling(tasks: list, limit: int, total_pool_size: int) -> list:
    """
    Semi-random cycling for large task pools with rotation bias.
    """
    now = datetime.now(timezone.utc).timestamp()
    
    def score(task):
        shown_count = task.get("shown_count", 0) or 0
        last_shown = task.get("last_shown_at")
        
        if last_shown:
            # Parse ISO format timestamp
            if isinstance(last_shown, str):
                last_shown_dt = datetime.fromisoformat(last_shown.replace("Z", "+00:00"))
                last_shown_ts = last_shown_dt.timestamp()
            else:
                last_shown_ts = 0
        else:
            last_shown_ts = 0
        
        # Days since shown (higher = shown longer ago)
        days_since_shown = (now - last_shown_ts) / 86400
        
        # Scoring for large pools:
        # - Reduce shown_count weight from 1000 to 100 for more variety
        # - Increase recency weight for rotation bias
        # - Add stronger randomization for semi-random behavior
        return (shown_count * 100) - (days_since_shown * 2) + (random.random() * 10)
    
    # Sort by score and take top tasks
    sorted_tasks = sorted(tasks, key=score)
    return sorted_tasks[:limit]
def _apply_small_pool_diversity(tasks: list, limit: int) -> list:
    """
    Maximize diversity for small task pools.
    """
    now = datetime.now(timezone.utc).timestamp()
    
    def score(task):
        shown_count = task.get("shown_count", 0) or 0
        last_shown = task.get("last_shown_at")
        
        if last_shown:
            # Parse ISO format timestamp
            if isinstance(last_shown, str):
                last_shown_dt = datetime.fromisoformat(last_shown.replace("Z", "+00:00"))
                last_shown_ts = last_shown_dt.timestamp()
            else:
                last_shown_ts = 0
        else:
            last_shown_ts = 0
        
        # Days since shown (higher = shown longer ago)
        days_since_shown = (now - last_shown_ts) / 86400
        
        # Scoring for small pools:
        # - Heavily prioritize tasks not shown recently
        # - Strong randomization to avoid patterns
        return (shown_count * 50) - (days_since_shown * 5) + (random.random() * 20)
    
    # Sort by score and take top tasks
    sorted_tasks = sorted(tasks, key=score)
    return sorted_tasks[:limit]
def _sort_by_recency(tasks: list) -> list:
    """
    Sort tasks by how recently they were shown (oldest first).
    """
    now = datetime.now(timezone.utc).timestamp()
    
    def get_last_shown_timestamp(task):
        last_shown = task.get("last_shown_at")
        if not last_shown:
            return 0
        
        if isinstance(last_shown, str):
            last_shown_dt = datetime.fromisoformat(last_shown.replace("Z", "+00:00"))
            return last_shown_dt.timestamp()
        else:
            return 0
    
    # Sort by last shown time (oldest first)
    return sorted(tasks, key=get_last_shown_timestamp)