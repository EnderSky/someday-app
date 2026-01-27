import random
from datetime import datetime, timezone


def get_shuffled_tasks(tasks: list, limit: int) -> list:
    """
    Smart shuffle that GUARANTEES never-shown tasks appear first.
    
    Algorithm:
    1. Separate tasks into "never shown" (shown_count = 0) and "shown before"
    2. Fill slots with never-shown tasks first (shuffled randomly)
    3. Fill remaining slots with shown tasks, prioritizing:
       - Lowest shown_count
       - Oldest last_shown_at (shown longest ago)
       - Random tiebreaker
    """
    if not tasks:
        return []
    
    # Separate never-shown vs shown tasks
    never_shown = [t for t in tasks if (t.get("shown_count") or 0) == 0]
    shown_before = [t for t in tasks if (t.get("shown_count") or 0) > 0]
    
    result = []
    
    # Step 1: Fill with never-shown tasks first (randomized)
    if never_shown:
        random.shuffle(never_shown)
        result.extend(never_shown[:limit])
    
    # Step 2: If we still have slots, fill with shown tasks
    remaining_slots = limit - len(result)
    if remaining_slots > 0 and shown_before:
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
            
            # Lower score = higher priority
            # Prioritize: fewer shows, shown longer ago, with randomness for ties
            return (shown_count * 1000) - days_since_shown + random.random()
        
        sorted_shown = sorted(shown_before, key=score)
        result.extend(sorted_shown[:remaining_slots])
    
    return result
