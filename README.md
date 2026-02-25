# Someday App

An ADHD-friendly to-do list Telegram bot using the Now/Soon/Someday method.

## Overview

Someday App is a minimalist task management bot designed to reduce overwhelm and decision fatigue. It uses a simple three-category system:

- **Now** - Tasks prioritized for today (max 3 shown at a time)
- **Soon** - Important but not today
- **Someday** - Brain dump / backlog

## Features

- Brain dump first approach - just send a message to add a task
- Edit tasks by editing your original message
- Smart shuffle algorithm to rotate through NOW tasks
- Prevents overload by limiting visible tasks
- Always shows total backlog count (nothing forgotten)
- Pagination for Soon, Someday, and Completed lists (10 items per page)
- View completed tasks with optional quick-access button
- User-configurable settings:
  - NOW display limit (1-5 tasks)
  - Visual theme (Classic, Minimal, Monospace)
  - Show/hide Completed button

## Tech Stack

- **Bot Backend**: Python, Oracle Cloud
- **Database**: Supabase (PostgreSQL)
- **Future**: Web app (Vercel), AI integration (Groq)

## Getting Started

### Prerequisites

- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Supabase account
- Oracle Cloud account

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your credentials: 
   ```
   copy .env.example .env
   ```
5. Run the bot:
   ```bash
   python -m bot.main
   ```

## Usage

Just send any message to add a task - no command needed!

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + tutorial + help |
| `/now` | View and manage your tasks |

### Adding Tasks

Send any message to the bot and it becomes a task in your Someday list.

Use tags to send tasks directly to a category:
- `Buy milk !now` → adds to NOW
- `Call dentist !soon` → adds to SOON

### Editing Tasks

Edit your original message within 48 hours to update the task content.

### Navigation

- Tap numbered buttons to view task details
- Use navigation buttons to switch between NOW, Soon, and Someday
- Pagination buttons (← Prev / Next →) appear when lists exceed 10 items
- Access Settings to customize your experience

## Implementation

See [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) for detailed implementation plan.

## License

MIT
