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
from activity_handlers import send_daily_failure_messages

# Singapore timezone for deadline checking
SG_TIMEZONE = pytz.timezone('Asia/Singapore')

def perform_activity_check(bot):
    """
    Check all tracked users for activity and send failure messages
    This function can be called directly from an API endpoint
    
    Args:
        bot: The Telegram bot instance
        
    Returns:
        dict: Results of the activity check
    """
    print(f"[{datetime.datetime.now(SG_TIMEZONE)}] Running activity check...")
    result = send_daily_failure_messages(bot)
    return {
        "timestamp": datetime.datetime.now(SG_TIMEZONE).isoformat(),
        "checked_users": result.get("checked", 0),
        "failures": result.get("failures", 0),
        "success": True
    }


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
