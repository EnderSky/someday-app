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
7. [Deployment](#deployment)
8. [Future Improvements](#future-improvements)

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
| Bot Backend | Oracle Cloud Always Free | Python Telegram bot | 24GB RAM, 200GB storage, 4 cores |
| Database | Supabase | PostgreSQL + Auth + Realtime | 500MB storage |
| Web Frontend | Vercel | Future React/Next.js app | Unlimited deploys |
| AI (Future) | Groq API | Task categorization + suggestions | Generous free tier |

---

## Features

**Task Management:**
- [x] Message → Task creation (free-form, with !now, !soon tags)
- [x] Message editing → Task updates (48-hour window)
- [x] Now/Soon/Someday categorization with smart promotions
- [x] Task completion with celebration messages
- [x] Task deletion and editing

**User Interface:**
- [x] Inline keyboards with navigation
- [x] Category views with pagination
- [x] Task detail views with action buttons
- [x] Settings management (limit, theme, completed toggle)
- [x] User-configurable NOW display limits (1-5 validation)
- [x] Message editing in-place for task updates

**Smart Features:**
- [x] Enhanced shuffle algorithm with diversity optimization
- [x] User settings persistence with JSONB storage
- [x] Category counts always visible
- [x] Responsive UI with multiple themes

**Database Integration:**
- [x] Supabase PostgreSQL with Row Level Security
- [x] Proper database indexes for performance
- [x] Service role key for bot operations
- [x] Error handling and validation

**Deployment Infrastructure:**
- [x] Webhook mode implementation (FastAPI server)
- [x] Health check endpoint for monitoring
- [x] Environment variable validation
- [x] Docker containerization
- [x] Oracle Cloud deployment configuration

---

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Telegram API   │────▶│  Oracle Cloud        │───▶│   Supabase      │
│  (webhooks)     │     │  (Always Free)       │     │  (PostgreSQL)   │
└─────────────────┘     └──────────────────────┘     └────────┬────────┘
                                                              │
                         ┌─────────────────┐                  │
                         │   Vercel        │◀────────────────┘
                         │  (Web App)      │   (future)
                         └─────────────────┘

                         ┌─────────────────┐
                         │   Groq API      │ (future AI)
                         └─────────────────┘
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

-- Row Level Security (kept enabled for future web app)
-- Bot uses service_role key which bypasses RLS
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can access own tasks" ON public.tasks 
  FOR ALL TO authenticated USING ((SELECT auth.uid()) = user_id) 
  WITH CHECK ((SELECT auth.uid()) = user_id);

-- Indexes
CREATE INDEX idx_tasks_user_category ON tasks(user_id, category) 
  WHERE completed_at IS NULL;
CREATE INDEX idx_tasks_user_active ON tasks(user_id) 
  WHERE completed_at IS NULL;
CREATE INDEX idx_tasks_message_id ON tasks(user_id, telegram_message_id)
  WHERE completed_at IS NULL;
```

---

## Project Structure

```
someday-app/
├── bot/
│   ├── __init__.py
│   ├── main.py                    # Entry point, webhook/polling modes
│   ├── webhook_server.py           # FastAPI webhook server (production)
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── commands.py            # /start, /now commands
│   │   ├── callbacks.py           # Inline button handlers
│   │   └── messages.py            # Free-form message + edited_message handling
│   ├── services/
│   │   ├── __init__.py
│   │   ├── task_service.py        # CRUD operations, category management
│   │   ├── user_service.py        # User settings management
│   │   └── shuffle_service.py     # Smart shuffle logic
│   ├── db/
│   │   ├── __init__.py
│   │   └── supabase_client.py   # Supabase connection + queries
│   └── utils/
│       ├── __init__.py
│       ├── keyboards.py            # Inline keyboard builders
│       └── formatters.py           # Message formatting helpers
├── config/
│   └── settings.py                 # Environment variables, webhook validation
├── docs/
│   └── IMPLEMENTATION_PLAN.md   # Implementation guide
├── requirements.txt               # Python dependencies (FastAPI ready)
├── Dockerfile                    # Container configuration
└── .env.example                  # Environment variable template
```

---

## Deployment

**Recommended: Oracle Cloud Container Instances (OCI CI, 2024+)**
- Zero server maintenance, managed networking, seamless Docker image deployment
- Modern, scalable, secure: official Oracle docs/release notes [here](https://www.oracle.com/cloud/cloud-native/container-instances/)

**Concise Steps:**
1. Sign up at [cloud.oracle.com](https://cloud.oracle.com) (credit card required for verification)
2. Build Docker image:
   ```sh
   docker build -t someday-bot:latest .
   ```
3. Push to Oracle Container Registry (OCIR):
   - [Set up OCIR auth](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrygettingauthtoken.htm)
   - Login to Docker: `docker login <region-key>.ocir.io`
     - Username: `<tenancy-namespace>/<username>`
     - Password: `<generated-authtoken>`
   - Tag and push:
     ```sh
     docker tag someday-bot:latest <region-key>.ocir.io/<tenancy-namespace>/<repo>:latest
     docker push <region-key>.ocir.io/<tenancy-namespace>/<repo>:latest
     ```
4. In OCI Console → Cloud Native → Container Instances:
   - Click "Create Container Instance"
   - Enter OCIR image URI
   - Inject env vars directly (TELEGRAM_BOT_TOKEN, SUPABASE_*, etc)
   - Pick shape (RAM/CPU), enable public networking as needed
   - Set restart policy to "always" for reliability
5. (Optional) Configure webhook URL in BotFather pointing to your container's public endpoint if using webhooks
6. Monitor/container logs via OCI Console; scale/upsize as needed

---

**Legacy (VM-Based) Instructions:**
- Still valid for advanced/self-managed scenarios
- Requires custom firewall, VM, and load balancer setup

1. Create Always Free compute instance (Ampere A1), block storage, load balancer
2. Deploy/image/run Docker manually
3. Configure firewall, webhooks, health checks

---

**Tip:**
- Use OCI's managed env var injection for secrets
- Outbound internet is required for Supabase and Telegram API

**References:**
- [OCI Container Instances Overview](https://www.oracle.com/cloud/cloud-native/container-instances/)
- [Container Registry Setup](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrygettingauthtoken.htm)
- [Bot webhook docs](https://core.telegram.org/bots/api#getting-updates)


**Dockerfile:**
```dockerfile
FROM python:3.13-slim

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

# Oracle Cloud (Recommended)
WEBHOOK_URL=https://your-app-name.apps.oc.io.oraclecloudapps.com/webhook
ENV=production

# Future
GROQ_API_KEY=your_groq_key
```

---

## Future Improvements

Future improvements to be implemented:

### Future Integrations

- Integration with web app (hosted using Vercel).
- Integration with mobile app (similar to MessMe).

### Auto-Split Tasks

- Detect multiple tasks in a single message (e.g., "Buy milk, call mom, fix bike")
- Options considered:
  - Ask before splitting ("Detected 3 tasks, split them?")
  - Auto-split silently (toggleable)
- Deferred to keep task entry simple and predictable

### AI Integration

#### Provider: Groq API

- **Models**: Llama 3 8B / 70B
- **Cost**: Generous free tier
- **Speed**: Very fast inference

#### Planned Features

1. **Suggest Button**
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

---