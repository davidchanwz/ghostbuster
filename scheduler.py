#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Scheduler for the activity tracking bot
This module handles scheduling tasks like midnight checks.
"""

import time
import threading
import datetime
import pytz
import schedule
from activity_handlers import send_daily_failure_messages

# Singapore timezone for deadline checking
SG_TIMEZONE = pytz.timezone('Asia/Singapore')


def schedule_midnight_check(bot):
    """
    Schedule the midnight check for activity tracking
    
    Args:
        bot: The Telegram bot instance
    """
    # Schedule the task to run at midnight Singapore time
    schedule.every().day.at("00:00").do(send_daily_failure_messages, bot)
    
    # Start the scheduling thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    print("Scheduled midnight check for activity tracking")


def run_scheduler():
    """Run the scheduler in a separate thread"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


def seconds_until_midnight():
    """
    Calculate seconds until midnight in Singapore timezone
    
    Returns:
        int: Seconds until midnight
    """
    now = datetime.datetime.now(SG_TIMEZONE)
    midnight = (now + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return (midnight - now).total_seconds()
