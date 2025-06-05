# Activity Tracking Telegram Bot

A Telegram bot that tracks user activity in group chats, with features to monitor and report on user messaging streaks.

## Features

- Track when users send messages in group chats
- Congratulate users on their first message of the day
- Send notifications when users fail to message by midnight
- Track and report on user streaks (consecutive days with/without messages)
- Docker support for easy deployment
- Support for both webhook (production) and polling (development) modes

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)
- A Telegram Bot Token (get it from [@BotFather](https://t.me/botfather))
- A Supabase account and project

## Setup

1. Clone this repository
2. Copy the example environment file:
   ```
   cp example.env .env
   ```
3. Edit `.env` and add your Telegram bot token and Supabase credentials

## Database Setup

1. Create a Supabase account and project at [supabase.com](https://supabase.com/)
2. Set up the database schema by running the SQL commands in `schema.sql`
3. Add your Supabase URL and API key to the `.env` file

## Bot Commands

- `/start` or `/help` - Show help information
- `/track` - Start tracking a user (reply to their message)
- `/untrack` - Stop tracking a user (reply to their message)
- `/report` - Get activity report for a user (reply to their message)

## Running Locally with Polling (Development Mode)

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the bot:
   ```
   python main.py
   ```

This will start the bot in polling mode, which is suitable for local development.

## Running with Docker

### Using Docker Compose (Recommended)

```
docker-compose up --build
```

### Using Docker Directly

```
docker build -t activity-bot .
docker run -p 8443:8443 --env-file .env activity-bot
```

## How It Works

1. **User Tracking**:
   - Admins can start tracking users by replying to their messages with `/track`
   - The bot will monitor when these users send messages

2. **Daily Check-ins**:
   - When a tracked user sends their first message of the day, they get a congratulation
   - If a user doesn't send any messages by midnight (Singapore time), the bot will note their failure

3. **Streaks**:
   - The bot tracks consecutive days of successful messaging (success streak)
   - It also tracks consecutive days of missed messaging (failure streak)

4. **Reporting**:
   - Admins can get a report on any tracked user's activity with the `/report` command
   - Reports show streak information and recent activity history

4. Run the bot as described above

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| TELEGRAM_API_TOKEN | Your Telegram Bot API token | TOKEN |
| USE_WEBHOOK | Whether to use webhook mode | false |
| WEBHOOK_HOST | Host for webhook mode | localhost |
| WEBHOOK_PORT | Port for webhook mode | 8443 |
| WEBHOOK_LISTEN | Interface to listen on | 0.0.0.0 |
| WEBHOOK_SSL_CERT | Path to SSL certificate (optional) | empty |
| WEBHOOK_SSL_PRIV | Path to SSL private key (optional) | empty |
| POLLING_INTERVAL | Interval for polling updates | 3 |
| SUPABASE_URL | Your Supabase project URL | empty |
| SUPABASE_API_KEY | Your Supabase API key | empty |

## Setting Up Webhook (Production Mode)

1. Set `USE_WEBHOOK=true` in your `.env` file

2. Configure your webhook settings in `.env`:
   ```
   WEBHOOK_HOST=your-domain-or-ip
   WEBHOOK_PORT=8443
   ```

3. SSL Certificates (Optional):
   
   You can run the webhook without SSL certificates, which is useful for:
   - Development environments
   - When behind a reverse proxy that handles SSL termination
   - When using a service like Ngrok for testing
   
   If you want to use SSL directly with your bot:
   ```
   openssl genrsa -out webhook_pkey.pem 2048
   openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
   ```
   When prompted for "Common Name", enter your server's domain name or IP address.
   
   Then update your .env file:
   ```
   WEBHOOK_SSL_CERT=./webhook_cert.pem
   WEBHOOK_SSL_PRIV=./webhook_pkey.pem
   ```

## Database Schema

The bot uses Supabase with the following schema:

```sql
-- 1. tracked_users: which (chat, user) pairs are being monitored
CREATE TABLE IF NOT EXISTS tracked_users (
  chat_id        BIGINT       NOT NULL,
  user_id        BIGINT       NOT NULL,
  added_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  PRIMARY KEY (chat_id, user_id)
);

-- 2. daily_activity: one row per (chat, user, date), recording if they sent a message
CREATE TABLE IF NOT EXISTS daily_activity (
  chat_id             BIGINT       NOT NULL,
  user_id             BIGINT       NOT NULL,
  activity_date       DATE         NOT NULL,
  messaged            BOOLEAN      NOT NULL DEFAULT FALSE,
  first_message_time  TIMESTAMPTZ,
  PRIMARY KEY (chat_id, user_id, activity_date),
  FOREIGN KEY (chat_id, user_id)
    REFERENCES tracked_users (chat_id, user_id)
    ON DELETE CASCADE
);

-- 3. user_streaks: caching consecutive‐day counts
CREATE TABLE IF NOT EXISTS user_streaks (
  chat_id             BIGINT       NOT NULL,
  user_id             BIGINT       NOT NULL,
  success_streak      INT          NOT NULL DEFAULT 0,
  failure_streak      INT          NOT NULL DEFAULT 0,
  last_activity_date  DATE,
  PRIMARY KEY (chat_id, user_id),
  FOREIGN KEY (chat_id, user_id)
    REFERENCES tracked_users (chat_id, user_id)
    ON DELETE CASCADE
);
```

## License

MIT

MIT
