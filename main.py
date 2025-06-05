#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This is a simple echo bot using decorators and webhook with fastapi
# It echoes any incoming text messages.
# It can work in webhook mode or polling mode based on environment variable

import logging
import os
import fastapi
import uvicorn
import telebot
from dotenv import load_dotenv
from handlers import register_handlers
from activity_handlers import register_activity_handlers
from scheduler import schedule_midnight_check

# Load environment variables from .env file if it exists
load_dotenv()

# Get the API token from environment variable or use a default for development
API_TOKEN = os.environ.get('TELEGRAM_API_TOKEN', 'TOKEN')

WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST', 'localhost')
WEBHOOK_PORT = int(os.environ.get('WEBHOOK_PORT', 8443))  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = os.environ.get('WEBHOOK_LISTEN', '0.0.0.0')  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = os.environ.get('WEBHOOK_SSL_CERT', './webhook_cert.pem')  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = os.environ.get('WEBHOOK_SSL_PRIV', './webhook_pkey.pem')  # Path to the ssl private key

# Determine if we're running in webhook mode
USE_WEBHOOK = os.environ.get('USE_WEBHOOK', 'false').lower() == 'true'

# Environment variables for local polling mode
POLLING_INTERVAL = int(os.environ.get('POLLING_INTERVAL', 3))

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

WEBHOOK_PATH = f"/{API_TOKEN}/"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}"

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(API_TOKEN)

app = fastapi.FastAPI(docs=None, redoc_url=None)


@app.post(f'/{API_TOKEN}/')
def process_webhook(update: dict):
    """
    Process webhook calls
    """
    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])
    else:
        return
    
def main():
    """Main function to run the bot in either webhook or polling mode"""
    # Register all handlers
    register_handlers(bot)
    register_activity_handlers(bot)
    
    # Schedule the midnight check
    schedule_midnight_check(bot)
    
    if USE_WEBHOOK:
        # Webhook mode for production
        print(f"Starting bot in webhook mode on {WEBHOOK_HOST}:{WEBHOOK_PORT}")
        
        # Remove webhook, it fails sometimes the set if there is a previous webhook
        bot.remove_webhook()

        # Configure webhook URL based on the host
        use_ssl = os.path.exists(WEBHOOK_SSL_CERT) and os.path.exists(WEBHOOK_SSL_PRIV)
        protocol = "https" if use_ssl else "http"
        WEBHOOK_URL_BASE = f"{protocol}://{WEBHOOK_HOST}:{WEBHOOK_PORT}"
        WEBHOOK_URL_PATH = f"/{API_TOKEN}/"
        
        # Set webhook
        if use_ssl:
            print("Using SSL certificates for webhook")
            bot.set_webhook(
                url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r')
            )
        else:
            print("Running webhook without SSL certificates")
            bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

        # Start FastAPI server
        uvicorn_kwargs = {
            "app": app,
            "host": WEBHOOK_LISTEN,
            "port": WEBHOOK_PORT
        }
        
        # Add SSL configuration only if certificates exist
        if use_ssl:
            uvicorn_kwargs.update({
                "ssl_certfile": WEBHOOK_SSL_CERT,
                "ssl_keyfile": WEBHOOK_SSL_PRIV
            })
            
        # Start the server
        uvicorn.run(**uvicorn_kwargs)
    else:
        # Polling mode for local development
        print("Starting bot in polling mode")
        bot.remove_webhook()
        bot.infinity_polling(interval=POLLING_INTERVAL, timeout=10)


if __name__ == "__main__":
    main()