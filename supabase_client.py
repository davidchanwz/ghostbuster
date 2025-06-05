#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Supabase client for the Telegram bot
This module provides a Supabase client instance for database operations.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables if not already loaded
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_API_KEY")


class SupabaseClient:
    """Singleton class for Supabase client"""
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            # Initialize the client when first instantiated
            cls._initialize_client()
        return cls._instance

    @classmethod
    def _initialize_client(cls):
        """Initialize the Supabase client"""
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "Supabase URL and API key must be set as environment variables: "
                "SUPABASE_URL and SUPABASE_API_KEY"
            )
        
        cls._client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    @property
    def client(self) -> Client:
        """Get the Supabase client instance"""
        return self._client


# Create a global instance of the client for easy importing
supabase = SupabaseClient().client


def get_supabase_client() -> Client:
    """
    Get the Supabase client instance.
    
    Returns:
        Client: A Supabase client instance
    
    Example:
        ```python
        from supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        users = supabase.table('users').select('*').execute()
        ```
    """
    return supabase


# Example usage functions - these can be used as reference or removed

def fetch_all_users():
    """Example function to fetch all users from the database"""
    try:
        response = supabase.table('users').select('*').execute()
        return response.data
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []


def save_user(user_id, username, first_name=None, last_name=None):
    """
    Example function to save a user to the database
    
    Args:
        user_id (int): Telegram user ID
        username (str): Telegram username
        first_name (str, optional): User's first name
        last_name (str, optional): User's last name
    
    Returns:
        dict: The inserted user data
    """
    try:
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "last_active": "now()"
        }
        
        # Insert the user with upsert (update if exists)
        response = supabase.table('users').upsert(
            user_data, 
            on_conflict='user_id'
        ).execute()
        
        return response.data
    except Exception as e:
        print(f"Error saving user: {e}")
        return None


if __name__ == "__main__":
    # Simple test to check if the connection works
    try:
        client = get_supabase_client()
        print("Successfully connected to Supabase!")
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")
