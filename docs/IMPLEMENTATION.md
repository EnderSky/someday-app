# Someday App - Implementation Plan

A minimalist, brain-dump style to-do list designed for ADHD users, delivered via Telegram bot.

## Table of Contents

1. [Core Concept](#core-concept)
2. [Tech Stack](#tech-stack)
3. [Features](#features)
4. [Architecture](#architecture)
5. [Database Schema](#database-schema)
6. [Deployment](#deployment)
   - [Supabase](#supabase)
   - [Oracle Cloud](#oracle-cloud)
7. [Future Improvements](#future-improvements)

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

## Tech Stack

| Layer | Service | Purpose | Free Tier |
|-------|---------|---------|-----------|
| Bot Backend | Oracle Cloud Always Free | Python Telegram bot | 24GB RAM, 200GB storage, 4 cores |
| Database | Supabase | PostgreSQL + Auth + Realtime | 500MB storage |
| Web Frontend | Vercel | Future React/Next.js app | Unlimited deploys |
| AI (Future) | Groq API | Task categorization + suggestions | Generous free tier |

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

## Database Schema

### Users Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT `gen_random_uuid()` | Unique identifier |
| `telegram_id` | BIGINT | UNIQUE, NOT NULL | Telegram user ID |
| `email` | TEXT | UNIQUE | For future web login |
| `settings` | JSONB | DEFAULT `{"now_display_limit": 3}` | User preferences |
| `created_at` | TIMESTAMPTZ | DEFAULT `NOW()` | Account creation timestamp |

Row Level Security is enabled. Bot uses `service_role` key which bypasses RLS.

### Tasks Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT `gen_random_uuid()` | Unique identifier |
| `user_id` | UUID | REFERENCES `users(id)` ON DELETE CASCADE | Owner reference |
| `telegram_message_id` | BIGINT | | Links task to original message for edit detection |
| `content` | TEXT | NOT NULL | Task description |
| `category` | TEXT | CHECK (`now`, `soon`, `someday`), DEFAULT `someday` | Task priority category |
| `shown_count` | INT | DEFAULT `0` | Times shown in shuffle |
| `last_shown_at` | TIMESTAMPTZ | | Last shuffle display time |
| `completed_at` | TIMESTAMPTZ | | Completion timestamp (NULL if active) |
| `created_at` | TIMESTAMPTZ | DEFAULT `NOW()` | Task creation timestamp |

Row Level Security is enabled. Bot uses `service_role` key which bypasses RLS.

### Indexes

| Index Name | Columns | Condition | Purpose |
|------------|---------|-----------|---------|
| `idx_tasks_user_category` | `user_id`, `category` | `completed_at IS NULL` | Fast category queries |
| `idx_tasks_user_active` | `user_id` | `completed_at IS NULL` | Active task lookups |
| `idx_tasks_message_id` | `user_id`, `telegram_message_id` | `completed_at IS NULL` | Message edit detection |

## Deployment

This section provides detailed setup & deployment instructions for all required services.

### Supabase

Supabase provides the PostgreSQL database with built-in authentication and Row Level Security.

#### Step 1: Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/log in
2. Click **New Project**
3. Configure your project:
   - **Name**: `someday-app`
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to your deployment (e.g., Singapore for `ap-singapore-1`)
4. Click **Create new project** and wait for provisioning (~2 minutes)

#### Step 2: Get Your API Keys

1. Go to **Project Settings** → **API**
2. Copy the following values:
   - **Project URL**: `https://your-project-id.supabase.co`
   - **Service Role Key**: Under "Project API keys" → `service_role` (secret, bypasses RLS)

> **Important**: Use the `service_role` key for the bot, NOT the `anon` key. The service role key bypasses Row Level Security, which is required for bot operations.

**Documentation**: [Supabase API Settings](https://supabase.com/docs/guides/api)

#### Step 3: Create Database Tables

1. Go to **SQL Editor** in your Supabase dashboard
2. Click **New Query**
3. Paste and run the following SQL:

```sql
-- Create Users Table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_id BIGINT UNIQUE NOT NULL,
  email TEXT UNIQUE,
  settings JSONB DEFAULT '{
    "now_display_limit": 3
  }',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can access own record" ON public.users 
  FOR ALL TO authenticated USING ((SELECT auth.uid()) = id) 
  WITH CHECK ((SELECT auth.uid()) = id);

-- Create Tasks Table
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  telegram_message_id BIGINT,
  content TEXT NOT NULL,
  category TEXT CHECK (category IN ('now', 'soon', 'someday')) DEFAULT 'someday',
  shown_count INT DEFAULT 0,
  last_shown_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can access own tasks" ON public.tasks 
  FOR ALL TO authenticated USING ((SELECT auth.uid()) = user_id) 
  WITH CHECK ((SELECT auth.uid()) = user_id);

-- Create Indexes for Performance
CREATE INDEX idx_tasks_user_category ON tasks(user_id, category) 
  WHERE completed_at IS NULL;
CREATE INDEX idx_tasks_user_active ON tasks(user_id) 
  WHERE completed_at IS NULL;
CREATE INDEX idx_tasks_message_id ON tasks(user_id, telegram_message_id)
  WHERE completed_at IS NULL;
```

4. Click **Run** to execute

#### Step 4: Verify Setup

1. Go to **Table Editor** in the sidebar
2. Confirm `users` and `tasks` tables exist
3. Check indexes under **Database** → **Indexes**

**Documentation**: [Supabase Database Guide](https://supabase.com/docs/guides/database)

---

### Oracle Cloud

Oracle Cloud Infrastructure (OCI) provides the compute resources to run the bot container.

#### Prerequisites

- Oracle Cloud account ([Sign up for Always Free](https://www.oracle.com/cloud/free/))
- Docker installed locally
- OCI CLI installed ([Installation Guide](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm))

#### Step 1: Install and Configure OCI CLI

**Install OCI CLI:**

```bash
# Windows (PowerShell as Administrator)
Set-ExecutionPolicy RemoteSigned
Invoke-WebRequest https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.ps1 -OutFile install.ps1
./install.ps1 -AcceptAllDefaults

# Linux/macOS
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
```

**Configure OCI CLI:**

```bash
oci setup config
```

You'll be prompted for:
- **User OCID**: OCI Console → Profile → My Profile → OCID
- **Tenancy OCID**: OCI Console → Profile → Tenancy → OCID
- **Region**: `ap-singapore-1` (Singapore)
- **API Key**: Generate a new key pair when prompted

**Documentation**: [CLI Configuration](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliconfigure.htm)

#### Step 2: Create Container Registry Repository

**Using OCI Console:**

1. Navigate to **Developer Services** → **Container Registry**
2. Select your compartment
3. Click **Create Repository**
4. Configure:
   - **Repository name**: `someday-app`
   - **Access**: Private (recommended)
5. Click **Create**

**Using OCI CLI:**

```bash
# Get your compartment OCID
oci iam compartment list --query "data[].{name:name, id:id}" --output table

# Create repository (replace COMPARTMENT_OCID)
oci artifacts container repository create \
  --compartment-id <COMPARTMENT_OCID> \
  --display-name someday-app \
  --is-public false \
  --region ap-singapore-1
```

**Documentation**: [Container Registry Overview](https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryoverview.htm)

#### Step 3: Generate Auth Token

1. Go to **OCI Console** → **Profile** → **My Profile**
2. Under **Resources**, click **Auth Tokens**
3. Click **Generate Token**
4. Enter description: `docker-login-token`
5. **Copy the token immediately** - it won't be shown again!

**Documentation**: [Getting an Auth Token](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrygettingauthtoken.htm)

#### Step 4: Log in to Container Registry

```bash
# Get your tenancy namespace
oci os ns get --query "data" --raw-output

# Login to OCIR (Singapore region)
docker login ap-singapore-1.ocir.io
```

When prompted:
- **Username**: `<tenancy-namespace>/<username>`
  - Example: `axaxnpcrorw5/john.doe@email.com`
- **Password**: The auth token from Step 3

**Documentation**: [Pushing Images to OCIR](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm)

#### Step 5: Build and Push Docker Image

```bash
# Navigate to project directory
cd /path/to/someday-app

# Build the image
docker build -t someday-app:latest .

# Tag for OCIR (replace <tenancy-namespace> with your actual namespace)
docker tag someday-app:latest ap-singapore-1.ocir.io/<tenancy-namespace>/someday-app:latest

# Push to OCIR
docker push ap-singapore-1.ocir.io/<tenancy-namespace>/someday-app:latest
```

**Example with actual namespace:**

```bash
docker tag someday-app:latest ap-singapore-1.ocir.io/axaxnpcrorw5/someday-app:latest
docker push ap-singapore-1.ocir.io/axaxnpcrorw5/someday-app:latest
```

#### Step 6: Create Container Instance

**Using OCI Console (Recommended):**

1. Navigate to **Developer Services** → **Container Instances**
2. Click **Create Container Instance**
3. Configure:
   - **Name**: `someday-app`
   - **Compartment**: Select your compartment
   - **Availability Domain**: Choose one (e.g., `AP-SINGAPORE-1-AD-1`)
   - **Shape**: `CI.Standard.E4.Flex` with 1 OCPU, 1GB RAM
4. Under **Container Configuration**:
   - **Image**: `ap-singapore-1.ocir.io/<tenancy-namespace>/someday-app:latest`
   - **Environment Variables**:
     ```
     TELEGRAM_BOT_TOKEN=your_bot_token
     SUPABASE_URL=https://your-project.supabase.co
     SUPABASE_KEY=your_service_role_key
     ENV=production
     WEBHOOK_URL=https://your-public-ip/webhook
     ```
5. Under **Networking**:
   - Select or create a VCN with public subnet
   - Enable public IP if using webhooks
6. Click **Create**

**Using OCI CLI:**

```bash
oci container-instances container-instance create \
  --compartment-id <COMPARTMENT_OCID> \
  --availability-domain <AD_NAME> \
  --shape CI.Standard.E4.Flex \
  --shape-config '{"ocpus": 1, "memoryInGBs": 1}' \
  --containers '[{
    "displayName": "someday-app",
    "imageUrl": "ap-singapore-1.ocir.io/<tenancy-namespace>/someday-app:latest",
    "environmentVariables": {
      "TELEGRAM_BOT_TOKEN": "your_bot_token",
      "SUPABASE_URL": "https://your-project.supabase.co",
      "SUPABASE_KEY": "your_service_role_key",
      "ENV": "production"
    }
  }]' \
  --vnics '[{"subnetId": "<SUBNET_OCID>"}]' \
  --display-name someday-app \
  --region ap-singapore-1
```

**Documentation**: [Container Instances](https://docs.oracle.com/en-us/iaas/Content/container-instances/home.htm)

#### Quick Reference: Singapore Region

| Property | Value |
|----------|-------|
| Region Name | Singapore |
| Region Identifier | `ap-singapore-1` |
| Region Key | `SIN` |
| OCIR Endpoint | `ap-singapore-1.ocir.io` |

#### Deployment Script

Save this as `deploy.sh` for easy redeployment:

```bash
#!/bin/bash
# deploy.sh - Deploy someday-app to Oracle Cloud

set -e

REGION="ap-singapore-1"
TENANCY_NAMESPACE=$(oci os ns get --query "data" --raw-output)
REPO_NAME="someday-app"
IMAGE_TAG="latest"
FULL_IMAGE_PATH="${REGION}.ocir.io/${TENANCY_NAMESPACE}/${REPO_NAME}:${IMAGE_TAG}"

echo "Building Docker image..."
docker build -t ${REPO_NAME}:${IMAGE_TAG} .

echo "Tagging image for OCIR..."
docker tag ${REPO_NAME}:${IMAGE_TAG} ${FULL_IMAGE_PATH}

echo "Pushing to OCIR..."
docker push ${FULL_IMAGE_PATH}

echo "Done! Image pushed to: ${FULL_IMAGE_PATH}"
echo ""
echo "Next steps:"
echo "1. Go to OCI Console → Container Instances"
echo "2. Restart your container instance to pull the new image"
```

#### Troubleshooting

| Error | Solution |
|-------|----------|
| `unauthorized: authentication required` | Verify auth token and username format `<namespace>/<user>` |
| `denied: requested access denied` | Check IAM policies and repository name |
| `image not found` | Wait a few seconds, verify full image path |
| Container won't start | Check logs in OCI Console, verify env vars |

#### Useful OCI Documentation Links

- [Container Registry Overview](https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryoverview.htm)
- [Pushing Images to OCIR](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm)
- [Getting Auth Tokens](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrygettingauthtoken.htm)
- [Container Instances](https://docs.oracle.com/en-us/iaas/Content/container-instances/home.htm)
- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/)
- [Regions and Availability Domains](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm)
- [Telegram Bot Webhooks](https://core.telegram.org/bots/api#getting-updates)

#### Dockerfile

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "bot.main"]
```

#### Environment Variables

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key  # Use service_role key (bypasses RLS)

# Oracle Cloud
WEBHOOK_URL=https://your-public-ip/webhook
ENV=production

# Future
GROQ_API_KEY=your_groq_key
```

#### Tips

- Use OCI's managed environment variable injection for secrets
- Outbound internet is required for Supabase and Telegram API
- Set container restart policy to "always" for reliability
- Configure webhook URL in BotFather pointing to your container's public endpoint

#### Legacy VM-Based Deployment

For advanced/self-managed scenarios requiring custom firewall, VM, and load balancer setup:

1. Create Always Free compute instance (Ampere A1), block storage, load balancer
2. Deploy and run Docker manually
3. Configure firewall, webhooks, health checks

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