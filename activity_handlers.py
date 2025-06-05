#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers for the activity tracking bot
"""

import datetime
import pytz
from telebot import types
from db_operations import (
    add_tracked_user, 
    remove_tracked_user, 
    is_user_tracked,
    record_user_message,
    get_user_activity_report,
    mark_daily_failures,
    get_user_by_username
)

# Singapore timezone for deadline checking
SG_TIMEZONE = pytz.timezone('Asia/Singapore')


def register_activity_handlers(bot):
    """Register all activity tracking handlers with the bot"""
    
    @bot.message_handler(commands=['track'])
    def track_user_command(message):
        """
        Handle '/track' command
        Format: /track @username (in a group chat)
        or: /track (as a reply to a message)
        """
        # Check if message is in a group chat
        if message.chat.type not in ['group', 'supergroup']:
            bot.reply_to(message, "👻 This command can only be used in group chats where ghosts lurk!")
            return
            
        # Check if user replied to a message
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            
            # Add user to tracking
            if add_tracked_user(message.chat.id, target_user.id, target_user.username):
                bot.reply_to(
                    message,
                    f"👻 WHO YA GONNA CALL? Ghostbusters! Now tracking {target_user.first_name} (@{target_user.username}) in this chat."
                )
            else:
                bot.reply_to(
                    message,
                    f"🔍 Already on the case! {target_user.first_name} (@{target_user.username}) is already being tracked."
                )
            return
            
        # Check if message includes username
        if len(message.text.split()) > 1:
            username = message.text.split()[1].strip('@')
            
            # Check if user is already being tracked by username
            user_data = get_user_by_username(message.chat.id, username)
            if user_data:
                bot.reply_to(
                    message,
                    f"👻 This ghost is already in our trap! @{username} is already being tracked in this chat."
                )
                return
                
            # We can't directly track a user by username without seeing them first
            bot.reply_to(
                message,
                f"🔍 Ghost not detected! To track @{username}, please reply to one of their messages with /track"
            )
            return
            
        # No target specified
        bot.reply_to(
            message,
            "🔍 We need to identify the ghost! Please reply to a user's message with /track to start tracking them."
        )
    
    @bot.message_handler(commands=['untrack'])
    def untrack_user_command(message):
        """
        Handle '/untrack' command
        Format: /untrack @username (in a group chat)
        or: /untrack (as a reply to a message)
        """
        # Check if message is in a group chat
        if message.chat.type not in ['group', 'supergroup']:
            bot.reply_to(message, "This command can only be used in group chats.")
            return
            
        # Check if user replied to a message
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            
            # Remove user from tracking
            if remove_tracked_user(message.chat.id, target_user.id):
                bot.reply_to(
                    message,
                    f"👋 Ghost released! {target_user.first_name} (@{target_user.username}) is no longer being tracked."
                )
            else:
                bot.reply_to(
                    message,
                    f"⚠️ No ghost found! {target_user.first_name} (@{target_user.username}) is not being tracked."
                )
            return
            
        # Check if message includes username
        if len(message.text.split()) > 1:
            username = message.text.split()[1].strip('@')
            
            # Try to find user by username
            user_data = get_user_by_username(message.chat.id, username)
            if user_data:
                # Remove user from tracking
                if remove_tracked_user(message.chat.id, user_data['user_id']):
                    bot.reply_to(
                        message,
                        f"👋 Ghost released! @{username} is no longer being tracked."
                    )
                else:
                    bot.reply_to(
                        message,
                        f"⚠️ Error in the containment unit! Couldn't stop tracking @{username}."
                    )
                return
            else:
                bot.reply_to(
                    message,
                    f"⚠️ No ghost found! @{username} is not being tracked in this chat."
                )
                return
            
        # No target specified
        bot.reply_to(
            message,
            "👻 Which ghost do you want to release? Please reply to a user's message with /untrack or use /untrack @username"
        )
    
    @bot.message_handler(commands=['report'])
    def report_command(message):
        """
        Handle '/report' command
        Format: /report (as a reply to a message)
        or: /report @username
        """
        # Check if message is in a group chat
        if message.chat.type not in ['group', 'supergroup']:
            bot.reply_to(message, "This command can only be used in group chats.")
            return
            
        # Check if user replied to a message
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            
            # Get report for the user
            if is_user_tracked(message.chat.id, target_user.id):
                send_activity_report(bot, message.chat.id, target_user, reply_to=message)
            else:
                bot.reply_to(
                    message,
                    f"⚠️ No ectoplasm detected! {target_user.first_name} (@{target_user.username}) is not being tracked."
                )
            return
            
        # Check if message includes username
        if len(message.text.split()) > 1:
            username = message.text.split()[1].strip('@')
            
            # Try to find user by username
            user_data = get_user_by_username(message.chat.id, username)
            if user_data:
                # Create a simple user object with the data we have
                class SimpleUser:
                    def __init__(self, user_id, username, first_name=None):
                        self.id = user_id
                        self.username = username
                        self.first_name = first_name or username
                
                # Try to get more user info if possible
                try:
                    chat_member = bot.get_chat_member(message.chat.id, user_data['user_id'])
                    target_user = chat_member.user
                except:
                    # If we can't get chat member info, use what we have from the database
                    target_user = SimpleUser(
                        user_data['user_id'],
                        user_data['username'],
                        user_data.get('first_name', username)
                    )
                
                send_activity_report(bot, message.chat.id, target_user, reply_to=message)
                return
            else:
                bot.reply_to(
                    message,
                    f"⚠️ No ectoplasm detected! @{username} is not being tracked in this chat."
                )
                return
            
        # No target specified
        bot.reply_to(
            message,
            "👻 Which ghost's ectoplasmic activity would you like to analyze? Please reply to a user's message with /report or use /report @username"
        )
    
    @bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'], content_types=['text'])
    def handle_group_message(message):
        """
        Handle text messages in a group chat
        Check if the user is being tracked and record their activity
        """
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Check if user is being tracked
        if is_user_tracked(chat_id, user_id):
            success, is_first_message = record_user_message(chat_id, user_id)
            
            # If this is the first message of the day, send a congratulations
            if success and is_first_message:
                # Get user streak
                report = get_user_activity_report(chat_id, user_id)
                if report:
                    streak = report.get('success_streak', 0)
                    
                    # Send congrats with streak information
                    if streak > 1:
                        bot.reply_to(
                            message,
                            f"🎉 GHOST ACTIVITY DETECTED! Way to go, {message.from_user.first_name}! "
                            f"You've materialized in the chat for the first time today.\n"
                            f"Haunting streak: {streak} days 👻🔥"
                        )
                    else:
                        bot.reply_to(
                            message,
                            f"👻 GHOST ACTIVITY DETECTED! {message.from_user.first_name} has materialized in the chat for the first time today!"
                        )
    
    # Additional handlers for specific content types (stickers, photos, etc.)
    @bot.message_handler(content_types=['sticker', 'photo', 'video', 'video_note', 'animation', 'audio', 'voice', 
                                        'document', 'location', 'contact', 'poll', 'dice', 'venue', 'game'], 
                        func=lambda message: message.chat.type in ['group', 'supergroup'])
    def handle_other_content_types(message):
        """
        Handle non-text messages in group chats (stickers, photos, etc.)
        This ensures we track activity regardless of message type
        """
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Check if user is being tracked
        if is_user_tracked(chat_id, user_id):
            content_type = "sticker" if message.sticker else \
                          "photo" if message.photo else \
                          "video" if message.video else \
                          "video note" if hasattr(message, 'video_note') and message.video_note else \
                          "animation" if hasattr(message, 'animation') and message.animation else \
                          "audio" if message.audio else \
                          "voice" if message.voice else \
                          "document" if message.document else \
                          "location" if message.location else \
                          "contact" if message.contact else \
                          "poll" if message.poll else \
                          "dice" if hasattr(message, 'dice') and message.dice else \
                          "venue" if hasattr(message, 'venue') and message.venue else \
                          "game" if hasattr(message, 'game') and message.game else "other"
            
            print(f"Recording non-text activity ({content_type}) for user {user_id} in chat {chat_id}")
            success, is_first_message = record_user_message(chat_id, user_id)
            
            # If this is the first message of the day, send a congratulations
            if success and is_first_message:
                # Get user streak
                report = get_user_activity_report(chat_id, user_id)
                if report:
                    streak = report.get('success_streak', 0)
                    
                    # Send congrats with streak information and mention the content type
                    if streak > 1:
                        bot.reply_to(
                            message,
                            f"👻 GHOST ACTIVITY DETECTED! {message.from_user.first_name} sent a {content_type}!\n"
                            f"You've materialized in the chat for the first time today.\n"
                            f"Haunting streak: {streak} days 👻🔥"
                        )
                    else:
                        bot.reply_to(
                            message,
                            f"👻 GHOST ACTIVITY DETECTED! {message.from_user.first_name} has materialized with a {content_type} for the first time today!"
                        )


def send_activity_report(bot, chat_id, user, reply_to=None):
    """
    Send a report of a user's activity
    
    Args:
        bot: The Telegram bot instance
        chat_id: The chat ID
        user: The Telegram user object
        reply_to: Message to reply to (optional)
    """
    report = get_user_activity_report(chat_id, user.id)
    
    if not report:
        bot.send_message(
            chat_id,
            f"Could not generate a report for {user.first_name}.",
            reply_to_message_id=reply_to.message_id if reply_to else None
        )
        return
    
    # Build report message
    success_streak = report.get('success_streak', 0)
    failure_streak = report.get('failure_streak', 0)
    history = report.get('daily_history', [])
    
    message = f"👻 ECTOPLASMIC ACTIVITY REPORT for {user.first_name}"
    if user.username:
        message += f" (@{user.username})"
    message += ":\n\n"
    
    # Add streak information
    if success_streak > 0:
        message += f"🔥 Current manifestation streak: {success_streak} day"
        message += "s" if success_streak != 1 else ""
        message += "\n"
    elif failure_streak > 0:
        message += f"👻 Current vanishing streak: {failure_streak} day"
        message += "s" if failure_streak != 1 else ""
        message += "\n"
    else:
        message += "No paranormal activity streaks detected\n"
    
    # Add daily history
    message += "\n📝 Ghostly activity log:\n"
    
    for day in history:
        date = datetime.datetime.fromisoformat(day['activity_date']).strftime('%Y-%m-%d')
        status = "✅" if day['messaged'] else "❌"
        
        message += f"{status} {date}"
        
        if day['messaged'] and day['first_message_time']:
            time = datetime.datetime.fromisoformat(day['first_message_time']) \
                .astimezone(SG_TIMEZONE) \
                .strftime('%H:%M:%S')
            message += f" (First message at {time})"
        
        message += "\n"
    
    # Send the report
    bot.send_message(
        chat_id,
        message,
        reply_to_message_id=reply_to.message_id if reply_to else None
    )


def send_daily_failure_messages(bot):
    """
    Send messages for users who failed to message today
    
    Args:
        bot: The Telegram bot instance
        
    Returns:
        dict: Stats about the check (number of users checked, failures found)
    """
    failures = mark_daily_failures()
    failure_count = 0
    
    for user in failures:
        chat_id = user['chat_id']
        user_id = user['user_id']
        
        # Get user information - this requires a chat member lookup
        try:
            chat_member = bot.get_chat_member(chat_id, user_id)
            user_info = chat_member.user
            
            # Get streak information
            report = get_user_activity_report(chat_id, user_id)
            failure_streak = report.get('failure_streak', 0) if report else 0
            
            # Send failure message
            if failure_streak > 1:
                message = (
                    f"👻 WHO YA GONNA CALL? NOT {user_info.first_name}! This ghost has vanished from our radar!\n"
                    f"⚡ Ectoplasmic absence streak: {failure_streak} days and counting! ⚡\n"
                    f"We're picking up strong PKE readings of inactivity!"
                )
            else:
                message = f"👻 SPECTRAL ALERT! {user_info.first_name} has crossed over to the invisible realm today! No messages detected on our PKE meter!"
                
            bot.send_message(chat_id, message)
            failure_count += 1
            print(f"Sent failure message to {user_info.first_name} in chat {chat_id}")
        except Exception as e:
            print(f"Error sending failure message: {e}")
    
    return {
        "checked": len(failures),
        "failures": failure_count
    }
