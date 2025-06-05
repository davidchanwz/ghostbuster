#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database operations for the activity tracking bot
"""

import datetime
from typing import List, Dict, Optional, Tuple, Any
import pytz
from supabase_client import get_supabase_client

# Singapore timezone for deadline checking
SG_TIMEZONE = pytz.timezone('Asia/Singapore')

# Get Supabase client
supabase = get_supabase_client()


def add_tracked_user(chat_id: int, user_id: int, username: str = None) -> bool:
    """
    Add a user to be tracked in a specific chat
    
    Args:
        chat_id: The Telegram chat ID
        user_id: The Telegram user ID
        username: The Telegram username (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # First check if the user is already being tracked
        result = supabase.table('tracked_users') \
            .select('*') \
            .eq('chat_id', chat_id) \
            .eq('user_id', user_id) \
            .execute()
            
        if result.data:
            # User is already being tracked
            return False
            
        # Add the user to tracked_users
        supabase.table('tracked_users').insert({
            'chat_id': chat_id,
            'user_id': user_id,
            'username': username
        }).execute()
        
        # Initialize user_streaks for this user
        supabase.table('user_streaks').insert({
            'chat_id': chat_id,
            'user_id': user_id,
            'success_streak': 0,
            'failure_streak': 0
        }).execute()
        
        # Initialize today's activity record
        today = datetime.datetime.now(SG_TIMEZONE).date()
        supabase.table('daily_activity').insert({
            'chat_id': chat_id,
            'user_id': user_id,
            'activity_date': today.isoformat(),
            'messaged': False
        }).execute()
        
        return True
    except Exception as e:
        print(f"Error adding tracked user: {e}")
        return False


def remove_tracked_user(chat_id: int, user_id: int) -> bool:
    """
    Remove a tracked user from a specific chat
    
    Args:
        chat_id: The Telegram chat ID
        user_id: The Telegram user ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if the user is being tracked
        result = supabase.table('tracked_users') \
            .select('*') \
            .eq('chat_id', chat_id) \
            .eq('user_id', user_id) \
            .execute()
            
        if not result.data:
            # User is not being tracked
            return False
            
        # Delete from tracked_users (cascades to other tables)
        supabase.table('tracked_users') \
            .delete() \
            .eq('chat_id', chat_id) \
            .eq('user_id', user_id) \
            .execute()
            
        return True
    except Exception as e:
        print(f"Error removing tracked user: {e}")
        return False


def is_user_tracked(chat_id: int, user_id: int) -> bool:
    """
    Check if a user is being tracked in a specific chat
    
    Args:
        chat_id: The Telegram chat ID
        user_id: The Telegram user ID
        
    Returns:
        bool: True if the user is being tracked, False otherwise
    """
    try:
        result = supabase.table('tracked_users') \
            .select('*') \
            .eq('chat_id', chat_id) \
            .eq('user_id', user_id) \
            .execute()
            
        return bool(result.data)
    except Exception as e:
        print(f"Error checking if user is tracked: {e}")
        return False


def get_user_by_username(chat_id: int, username: str) -> Dict[str, Any]:
    """
    Get a tracked user by their username in a specific chat
    
    Args:
        chat_id: The Telegram chat ID
        username: The Telegram username (without @)
        
    Returns:
        Dict with user data or empty dict if not found
    """
    try:
        # Try exact match first (without @)
        result = supabase.table('tracked_users') \
            .select('*') \
            .eq('chat_id', chat_id) \
            .eq('username', username) \
            .execute()
            
        if result.data:
            return result.data[0]
            
        # Try with @ if not found
        result = supabase.table('tracked_users') \
            .select('*') \
            .eq('chat_id', chat_id) \
            .eq('username', f"@{username}") \
            .execute()
            
        if result.data:
            return result.data[0]
            
        return {}
    except Exception as e:
        print(f"Error getting user by username: {e}")
        return {}


def record_user_message(chat_id: int, user_id: int) -> Tuple[bool, bool]:
    """
    Record that a user has sent a message in a specific chat
    
    Args:
        chat_id: The Telegram chat ID
        user_id: The Telegram user ID
        
    Returns:
        Tuple[bool, bool]: (success, is_first_message)
        - success: True if the operation was successful
        - is_first_message: True if this is the first message of the day
    """
    if not is_user_tracked(chat_id, user_id):
        return False, False
    
    try:
        # Get today's date in Singapore timezone
        now = datetime.datetime.now(SG_TIMEZONE)
        today = now.date()
        
        # Check if there's already a record for today
        result = supabase.table('daily_activity') \
            .select('*') \
            .eq('chat_id', chat_id) \
            .eq('user_id', user_id) \
            .eq('activity_date', today.isoformat()) \
            .execute()
            
        is_first_message = False
        
        if not result.data:
            # Create a new record for today
            supabase.table('daily_activity').insert({
                'chat_id': chat_id,
                'user_id': user_id,
                'activity_date': today.isoformat(),
                'messaged': True,
                'first_message_time': now.isoformat()
            }).execute()
            is_first_message = True
        elif not result.data[0]['messaged']:
            # Update existing record if messaged is False
            supabase.table('daily_activity') \
                .update({
                    'messaged': True,
                    'first_message_time': now.isoformat()
                }) \
                .eq('chat_id', chat_id) \
                .eq('user_id', user_id) \
                .eq('activity_date', today.isoformat()) \
                .execute()
            is_first_message = True
        
        # Update streaks if this is the first message
        if is_first_message:
            update_streak(chat_id, user_id, True)
        
        return True, is_first_message
    except Exception as e:
        print(f"Error recording user message: {e}")
        return False, False


def update_streak(chat_id: int, user_id: int, success: bool) -> bool:
    """
    Update a user's streak
    
    Args:
        chat_id: The Telegram chat ID
        user_id: The Telegram user ID
        success: True if the user messaged today, False otherwise
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get current streak information
        result = supabase.table('user_streaks') \
            .select('*') \
            .eq('chat_id', chat_id) \
            .eq('user_id', user_id) \
            .execute()
            
        if not result.data:
            # Initialize streak if it doesn't exist
            streak_data = {
                'chat_id': chat_id,
                'user_id': user_id,
                'success_streak': 1 if success else 0,
                'failure_streak': 0 if success else 1,
                'last_activity_date': datetime.datetime.now(SG_TIMEZONE).date().isoformat()
            }
            supabase.table('user_streaks').insert(streak_data).execute()
            return True
        
        # Update existing streak
        current_streak = result.data[0]
        today = datetime.datetime.now(SG_TIMEZONE).date()
        
        # Calculate streak based on previous data and today's success/failure
        if success:
            # Success case (user messaged today)
            success_streak = current_streak['success_streak'] + 1
            failure_streak = 0  # Reset failure streak
        else:
            # Failure case (user didn't message today)
            success_streak = 0  # Reset success streak
            failure_streak = current_streak['failure_streak'] + 1
        
        # Update the streak in database
        supabase.table('user_streaks') \
            .update({
                'success_streak': success_streak,
                'failure_streak': failure_streak,
                'last_activity_date': today.isoformat()
            }) \
            .eq('chat_id', chat_id) \
            .eq('user_id', user_id) \
            .execute()
            
        return True
    except Exception as e:
        print(f"Error updating streak: {e}")
        return False


def get_user_streak(chat_id: int, user_id: int) -> Dict[str, Any]:
    """
    Get a user's current streak information
    
    Args:
        chat_id: The Telegram chat ID
        user_id: The Telegram user ID
        
    Returns:
        Dict containing streak information or empty dict if not found
    """
    try:
        result = supabase.table('user_streaks') \
            .select('*') \
            .eq('chat_id', chat_id) \
            .eq('user_id', user_id) \
            .execute()
            
        if not result.data:
            return {}
            
        return result.data[0]
    except Exception as e:
        print(f"Error getting user streak: {e}")
        return {}


def get_tracked_users_without_message() -> List[Dict[str, Any]]:
    """
    Get all tracked users who haven't messaged today
    
    Returns:
        List of dicts with chat_id and user_id for users who haven't messaged
    """
    try:
        today = datetime.datetime.now(SG_TIMEZONE).date()
        
        # First get all tracked users
        tracked_users = supabase.table('tracked_users').select('*').execute().data
        
        # For each tracked user, check if they have a successful activity record for today
        users_without_message = []
        
        for user in tracked_users:
            chat_id = user['chat_id']
            user_id = user['user_id']
            
            # Check if there's a record for today with messaged=True
            result = supabase.table('daily_activity') \
                .select('*') \
                .eq('chat_id', chat_id) \
                .eq('user_id', user_id) \
                .eq('activity_date', today.isoformat()) \
                .eq('messaged', True) \
                .execute()
                
            if not result.data:
                # No successful message today
                users_without_message.append({
                    'chat_id': chat_id,
                    'user_id': user_id
                })
                
                # Create or update activity record for today
                existing = supabase.table('daily_activity') \
                    .select('*') \
                    .eq('chat_id', chat_id) \
                    .eq('user_id', user_id) \
                    .eq('activity_date', today.isoformat()) \
                    .execute().data
                    
                if not existing:
                    # Create a new record
                    supabase.table('daily_activity').insert({
                        'chat_id': chat_id,
                        'user_id': user_id,
                        'activity_date': today.isoformat(),
                        'messaged': False
                    }).execute()
        
        return users_without_message
    except Exception as e:
        print(f"Error getting users without message: {e}")
        return []


def mark_daily_failures() -> List[Dict[str, Any]]:
    """
    Mark users who failed to message today and update their streaks
    
    Returns:
        List of users who failed to message
    """
    try:
        failures = get_tracked_users_without_message()
        
        # Update streaks for all failures
        for user in failures:
            update_streak(user['chat_id'], user['user_id'], False)
            
        return failures
    except Exception as e:
        print(f"Error marking daily failures: {e}")
        return []


def get_user_activity_report(chat_id: int, user_id: int, days: int = 7) -> Dict[str, Any]:
    """
    Get a report of a user's activity for the last N days
    
    Args:
        chat_id: The Telegram chat ID
        user_id: The Telegram user ID
        days: Number of days to include in the report (default 7)
        
    Returns:
        Dict with report data including:
        - success_streak: current success streak
        - failure_streak: current failure streak
        - daily_history: list of daily activity records
    """
    try:
        # Get streak information
        streak = get_user_streak(chat_id, user_id)
        if not streak:
            return {}
            
        # Get daily activity history
        end_date = datetime.datetime.now(SG_TIMEZONE).date()
        start_date = end_date - datetime.timedelta(days=days-1)
        
        history = supabase.table('daily_activity') \
            .select('*') \
            .eq('chat_id', chat_id) \
            .eq('user_id', user_id) \
            .gte('activity_date', start_date.isoformat()) \
            .lte('activity_date', end_date.isoformat()) \
            .order('activity_date', desc=True) \
            .execute().data
            
        return {
            'success_streak': streak.get('success_streak', 0),
            'failure_streak': streak.get('failure_streak', 0),
            'daily_history': history
        }
    except Exception as e:
        print(f"Error getting user activity report: {e}")
        return {}
