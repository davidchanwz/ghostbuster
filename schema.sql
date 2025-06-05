-- Schema for the Activity Tracking Bot

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
