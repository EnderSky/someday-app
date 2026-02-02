# Someday App - Implementation Plan

A minimalist, brain-dump style to-do list designed for ADHD users, delivered via Telegram bot.

---

## Table of Contents

1. [Core Concept](#core-concept)
2. [Tech Stack](#tech-stack)
3. [Features](#features)
4. [Architecture](#architecture)
5. [Database Schema](#database-schema)
6. [Project Structure](#project-structure)
7. [Telegram Bot Interactions](#telegram-bot-interactions)
8. [Smart Shuffle Algorithm](#smart-shuffle-algorithm)
9. [AI Integration (Future)](#ai-integration-future)
10. [Deployment](#deployment)
11. [Implementation Phases](#implementation-phases)

---

## Core Concept

### Design Philosophy

- **Brain dump first**: Capture everything quickly without friction
- **Minimal classification**: No deadlines, no complex categorization
- **Prevent overload**: Show only 3 tasks at a time, hide the rest
- **Visibility of backlog**: Always show total count (nothing forgotten)

### Now / Soon / Someday Method

| Category | Purpose | Behavior |
|----------|---------|----------|
| **Now** | Tasks prioritized for today | Max 3 displayed (configurable), shuffle to see others |
| **Soon** | Important but not today | Hidden by default, tap to peek |
| **Someday** | Brain dump / backlog | Hidden by default, tap to peek |

---

## Tech Stack

| Layer | Service | Purpose | Free Tier |
|-------|---------|---------|-----------|
| Bot Backend | Pella (Primary) / Fly.io (Legacy) | Python Telegram bot | 100MB RAM, 5GB storage |
| Database | Supabase | PostgreSQL + Auth + Realtime | 500MB storage |
| Web Frontend | Vercel | Future React/Next.js app | Unlimited deploys |
| AI (Future) | Groq API | Task categorization + suggestions | Generous free tier |

---

## Features

### MVP Features

- [x] Add tasks via free-form messages (any message becomes a task)
- [x] Edit tasks by editing the original message
- [x] Now / Soon / Someday categorization
- [x] Promote / demote tasks between categories
- [x] Smart shuffle for NOW tasks (shows 3 at a time)
- [x] User-configurable NOW display limit (default: 3)
- [x] Task completion with brief celebration
- [x] Category counts always visible
- [x] User settings persistence

### Future Features (Post-MVP)

- [ ] AI suggestion button (picks 1-3 important tasks)
- [ ] Web app interface
- [ ] Mobile app

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Telegram API   │────▶│   Pella         │────▶│   Supabase      │
│  (webhooks)     │     │  (Free Bot Host)│     │  (PostgreSQL)   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                         ┌─────────────────┐              │
                         │   Vercel        │◀─────────────┘
                         │  (Web App)      │   (future)
                         └─────────────────┘

                         ┌─────────────────┐
                         │   Groq API      │ (future AI)
                         └─────────────────┘

Alternative (Legacy):
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Telegram API   │────▶│   Fly.io        │────▶│   Supabase      │
│  (webhooks)     │     │  (Paid Required)│     │  (PostgreSQL)   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
```

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_id BIGINT UNIQUE NOT NULL,
  email TEXT UNIQUE,  -- for future web login
  settings JSONB DEFAULT '{
    "now_display_limit": 3
  }',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security (kept enabled for future web app)
-- Bot uses service_role key which bypasses RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can access own record" ON public.users 
  FOR ALL TO authenticated USING ((SELECT auth.uid()) = id) 
  WITH CHECK ((SELECT auth.uid()) = id);
```

### Tasks Table

```sql
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  telegram_message_id BIGINT,  -- Links task to original message for edit detection
  content TEXT NOT NULL,
  category TEXT CHECK (category IN ('now', 'soon', 'someday')) DEFAULT 'someday',
  shown_count INT DEFAULT 0,
  last_shown_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tasks_user_category ON tasks(user_id, category) 
  WHERE completed_at IS NULL;
CREATE INDEX idx_tasks_user_active ON tasks(user_id) 
  WHERE completed_at IS NULL;
CREATE INDEX idx_tasks_message_id ON tasks(user_id, telegram_message_id)
  WHERE completed_at IS NULL;

-- Row Level Security (kept enabled for future web app)
-- Bot uses service_role key which bypasses RLS
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can access own tasks" ON public.tasks 
  FOR ALL TO authenticated USING ((SELECT auth.uid()) = user_id) 
  WITH CHECK ((SELECT auth.uid()) = user_id);
```

---

## Project Structure

```
someday-app/
├── bot/
│   ├── __init__.py
│   ├── main.py                 # Entry point, webhook setup
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── commands.py         # /start, /now (/help redirects to /start)
│   │   ├── callbacks.py        # Inline button handlers
│   │   └── messages.py         # Free-form message + edited_message handling
│   ├── services/
│   │   ├── __init__.py
│   │   ├── task_service.py     # CRUD operations, category management
│   │   ├── user_service.py     # User settings management
│   │   ├── shuffle_service.py  # Smart shuffle logic
│   │   └── ai_service.py       # Stub for future Groq integration
│   ├── db/
│   │   ├── __init__.py
│   │   └── supabase_client.py  # Supabase connection + queries
│   └── utils/
│       ├── __init__.py
│       ├── keyboards.py        # Inline keyboard builders
│       └── formatters.py       # Message formatting helpers
├── config/
│   └── settings.py             # Environment variables, constants
├── tests/
│   └── ...
├── requirements.txt
├── Dockerfile
├── fly.toml
└── .env.example
```

---

## Telegram Bot Interactions

### Commands

| Command | Action |
|---------|--------|
| `/start` | Welcome message + tutorial + help |
| `/now` | Show NOW tasks with navigation to all views |

> **Note:** `/help` exists as an undocumented fallback that redirects to `/start`.

### Adding Tasks

Any free-form message sent to the bot is automatically added as a task to **Someday**. No command required.

```
User: Buy groceries
Bot: ✅ Added to Someday (44 items)
```

### Editing Tasks

Edit your original message to update the task content. The bot silently updates the task.

| Scenario | Behavior |
|----------|----------|
| Task exists & active | Update task content |
| Task completed | Ignore edit |
| Task deleted | Ignore edit |

> **Note:** Telegram allows editing messages for ~48 hours.

### Main View (`/now`)

```
🔥 NOW (showing 3 of 7)
─────────────────────
1. Finish tax documents
2. Call dentist
3. Reply to landlord email

Tap a number to select task.
─────────────────────
⏳ Soon: 12  |  📦 Someday: 43

[1] [2] [3]
[🔀 Shuffle]
[⏳ Soon] [📦 Someday]
[⚙️ Settings]
```

### Soon View

```
⏳ SOON (12 items)
─────────────────────
1. Book flight for March
2. Research new laptop
3. Schedule annual checkup
... and 9 more

Tap a number to select task.
─────────────────────
🔥 Now: 7  |  📦 Someday: 43

[1] [2] [3] [4] [5]
[🔥 Now] [📦 Someday]
[⚙️ Settings]
```

### Someday View

```
📦 SOMEDAY (43 items)
─────────────────────
1. Learn piano
2. Organize garage
3. Read that book Sarah recommended
... and 40 more

Tap a number to select task.
─────────────────────
🔥 Now: 7  |  ⏳ Soon: 12

[1] [2] [3] [4] [5]
[🔥 Now] [⏳ Soon]
[⚙️ Settings]
```

### Task Detail View

```
📌 Finish tax documents
Added 3 days ago

[✅ Done] [⬆️ → Soon] [🗑️ Delete]
[← Back]
```

**Button availability by category:**

| Current Category | Promote | Demote |
|------------------|---------|--------|
| Now | Hidden | `[⬇️ → Soon]` |
| Soon | `[⬆️ → Now]` | `[⬇️ → Someday]` |
| Someday | `[⬆️ → Soon]` | Hidden |

### Settings View

```
⚙️ Settings
─────────────────────
NOW display limit: 3

[1] [2] [3] [4] [5]
[← Back]
```

Note: Values are capped to 1-5 range.

### Completion Behavior

- Brief celebration: "✨ Nice! Task completed"
- Task immediately hidden from views

---

## Smart Shuffle Algorithm

Prioritizes tasks that have been shown less frequently and less recently.

```python
def get_shuffled_now_tasks(tasks: list, limit: int) -> list:
    """
    Smart shuffle prioritizes:
    1. Tasks never shown (shown_count = 0)
    2. Tasks shown least recently (oldest last_shown_at)
    3. Tasks with lowest shown_count
    4. Random tiebreaker for equal scores
    """
    import random
    from datetime import datetime
    
    now = datetime.now().timestamp()
    
    def score(task):
        # Lower score = higher priority
        recency = (now - (task.last_shown_at or 0)) / 86400  # days since shown
        return (task.shown_count * 100) - recency + random.random()
    
    sorted_tasks = sorted(tasks, key=score)
    return sorted_tasks[:limit]
```

After displaying, update `shown_count` and `last_shown_at` for selected tasks.

---

## Deployment

### Alternative: Pella (Recommended for Free Hosting)

**Why Pella over Fly.io:**
- **100% Free Forever**: No credit card, no trial limits
- **Perfect Resource Match**: 100MB RAM, 5GB storage fits bot needs
- **Specialized**: Built specifically for Telegram bots
- **No Infrastructure Management**: Upload and deploy

#### Webhook Implementation Required (Remaining)

**Current Status:** Bot works in polling mode, needs webhook for Pella

**Files to Modify:**
1. **`bot/main.py`** - Fix incomplete webhook implementation (lines 35-56)
2. **`config/settings.py`** - Add webhook URL validation
3. **`bot/webhook_server.py`** - New lightweight server (FastAPI)
4. **`requirements.txt`** - Add FastAPI dependency (already done)

**Required Changes:**
```python
# 1. Fix run_webhook() in bot/main.py
# Current Issue: Incomplete ASGI setup, wrong uvicorn usage
# Fix: Proper FastAPI app with webhook handler

# 2. Create bot/webhook_server.py
# POST /webhook - Process Telegram updates using existing handlers
# GET /health - Simple health check for monitoring
# Integration: Reuse all existing bot.handlers logic

# 3. Update config/settings.py
# Add webhook URL format validation (must end with /webhook)
# Add webhook secret support (optional security)

# 4. Environment Variables for Pella
WEBHOOK_URL=https://your-subdomain.pella.app/webhook
PORT=8080
ENV=production
```

**Implementation Complexity:**
- Main.py fixes: ~30 lines
- New webhook server: ~50 lines  
- Settings validation: ~10 lines
- Total effort: ~2.5 hours

#### Pella Deployment Steps
```bash
# 1. Sign up on pella.app (no credit card required)
# 2. Create new bot deployment
# 3. Upload code (zip or Git)
# 4. Set environment variables
# 5. Configure webhook URL
# 6. Start deployment
```

### Fly.io Setup (Legacy - Not Recommended)

**Issues with Fly.io:**
- **5-minute trial limit** - Requires credit card for continuous operation
- **Over-provisioned resources** - 256MB RAM vs 100MB needed
- **Higher complexity** - Docker + VM management required

**fly.toml:**
```toml
app = "someday-app"
primary_region = "sin"  # Singapore, adjust to your region

[build]
  dockerfile = "Dockerfile"

[env]
  PYTHONUNBUFFERED = "1"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = false  # Keep bot always running
  auto_start_machines = true
  min_machines_running = 1

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "bot.main"]
```

### Environment Variables

```bash
# .env.example
TELEGRAM_BOT_TOKEN=your_bot_token
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key  # Use service_role key (bypasses RLS)

# Pella (Recommended)
WEBHOOK_URL=https://your-subdomain.pella.app/webhook
ENV=production

# Fly.io (Legacy)
# WEBHOOK_URL=https://someday-app.fly.dev/webhook
# ENV=development  # or production

# Future
GROQ_API_KEY=your_groq_key
```

### Deployment Commands

#### Pella (Recommended)
```bash
# 1. Sign up at pella.app (no credit card)
# 2. Create bot deployment
# 3. Upload files or connect Git repo
# 4. Set environment variables
# 5. Deploy with webhook URL configuration
# 6. Test webhook connectivity
```

#### Fly.io (Legacy)
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Create app
fly launch

# Set secrets
fly secrets import < .env

# Deploy
fly deploy

# View logs
fly logs
```

---

## Implementation Phases

### Phase 1: Core MVP (Week 1)

- [x] Project scaffolding + configuration
- [x] Supabase setup (tables, RLS policies)
- [x] Basic bot with /start, /now
- [x] Free-form message → task creation
- [x] Now/Soon/Someday categories
- [x] Promote/demote between categories
- [x] Inline keyboards with navigation
- [ ] **Pella deployment with webhook mode**

### Phase 2: Smart Features (Week 2)

- [x] Smart shuffle algorithm
- [x] User-configurable NOW limit
- [x] User settings persistence
- [x] Message edit detection for task updates
- [x] Completion celebration
- [ ] **Webhook mode optimization for Pella resource constraints**

### Phase 3: Polish (Week 3)

- [x] Error handling + edge cases
- [ ] Message editing (update bot messages in place)
- [ ] Basic usage stats
- [ ] Testing

### Phase 4: AI Integration (Future)

- [ ] Groq API integration
- [ ] Suggest button feature

## Development Status Summary

**Overall Progress: 85% Complete**
- Core bot functionality: ✅ Working
- Database integration: ✅ Working  
- UI/UX features: ✅ Working
- Smart shuffle algorithm: ✅ Working
- User settings: ✅ Working
- **Pella deployment: 🔄 Webhook mode needed**

**Next Steps for Production:**
1. Implement webhook mode (2.5 hours)
2. Deploy to Pella (15 minutes)
3. Test webhook connectivity (10 minutes)

**Total Time to Production: ~3 hours**

---

## Dependencies

**requirements.txt:**
```
# Core bot functionality
python-telegram-bot==22.6
supabase==2.27.2
python-dotenv==1.2.1
httpx==0.28.1

# Webhook mode (Pella deployment)
fastapi==0.104.1
uvicorn[standard]==0.24.0
```

---

## Quick Reference

### Category Flow

```
SOMEDAY ──⬆️ Promote──▶ SOON ──⬆️ Promote──▶ NOW
   ◀──────⬇️ Demote──────  ◀─────⬇️ Demote──────
```

### Current Implementation Status

**Core Bot Logic: ✅ COMPLETE**
- Message → Task creation (with !now, !soon tags)
- Message editing → Task updates (48-hour window)
- Command handling: /start, /now
- Inline keyboards: All navigation buttons
- Smart shuffle: Enhanced algorithm with diversity
- User settings: Persistent, validated (1-5 limits)

**Database Integration: ✅ COMPLETE**
- Supabase PostgreSQL with Row Level Security
- Users table with settings JSONB
- Tasks table with category validation
- Proper indexes for performance

**UI/UX Features: ✅ COMPLETE**
- Responsive inline keyboards
- Task detail views with actions
- Settings management (limit, theme, completed toggle)
- Category counts display
- Message editing in-place

**Missing for Pella Deployment: 🔄 WEBHOOK MODE**
- Webhook server implementation
- Health check endpoint
- Webhook URL validation
- Memory optimization for 100MB constraint

### User Settings Schema

```json
{
  "now_display_limit": 3
}
```

### Free Tier Limits

| Service | Limit | Your Usage |
|---------|-------|------------|
| **Pella RAM** | 100 MB | ~80 MB (optimized) |
| **Pella Storage** | 5 GB | <50 MB |
| **Pella CPU** | 0.1 cores | Minimal usage |
| **Fly.io (Legacy)** | 256 MB RAM, 3 VMs | ~100 MB, 1 VM |
| Supabase Storage | 500 MB | <10 MB |
| Supabase MAU | 50,000 | Low |
| Groq (future) | Generous | Minimal |

---

## Future Improvements

Features considered but deferred for simplicity:

### Future Integrations

- Integration with web app (hosted using Vercel).
- Integration with mobile app (similar to MessMe).

### Auto-Split Tasks

- Detect multiple tasks in a single message (e.g., "Buy milk, call mom, fix bike")
- Options considered:
  - Ask before splitting ("Detected 3 tasks, split them?")
  - Auto-split silently (toggleable)
- Deferred to keep task entry simple and predictable

### AI Task Suggestions

#### Provider: Groq API

- **Models**: Llama 3 8B / 70B
- **Cost**: Generous free tier
- **Speed**: Very fast inference

#### Planned Features

1. **Suggest button**
   - Analyzes SOON + SOMEDAY tasks
   - Picks 1-3 that seem important
   - Based on: urgency keywords, age, life-critical topics

#### Prompt Template

```
You are a minimal task assistant. Given these tasks:

SOON:
{soon_tasks}

SOMEDAY:
{someday_tasks}

Pick 1-3 tasks that seem most important. Consider:
- Urgency words (deadline, due, urgent, asap)
- Life-critical topics (health, money, legal, family)
- Task age (older = possibly forgotten)

Respond with JSON only: {"task_ids": ["id1", "id2"]}
```

2. **AI Auto-Categorization**

- On task creation, AI suggests Now/Soon/Someday
- User confirms or changes category
- Toggleable in settings (`ai_categorize_enabled`)