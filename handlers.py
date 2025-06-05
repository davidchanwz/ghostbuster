#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram bot message handlers
This module contains base message handlers for the Telegram bot.
"""

def register_handlers(bot):
    """Register all base message handlers with the bot"""
    
    @bot.message_handler(commands=['help', 'start'])
    def send_welcome(message):
        """
        Handle '/start' and '/help'
        """
        bot.reply_to(message,
                    ("Hi there, I am Ghostbuster.\n"
                     "I help track user activity in group chats.\n\n"
                     "Commands:\n"
                     "/track - Start tracking a user (reply to their message)\n"
                     "/untrack - Stop tracking a user (reply to their message)\n"
                     "/report - Get activity report for a user (reply to their message)"))


    # We don't need the echo handler anymore as we'll be handling all messages
    # in the activity_handlers.py
