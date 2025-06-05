import os
import json
from datetime import datetime, timedelta
from typing import Optional, List
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import asyncio

def get_calendar_service():
    """Initialize Google Calendar service with service account credentials"""
    try:
        client_email = os.getenv("GOOGLE_CLIENT_EMAIL")
        private_key = os.getenv("GOOGLE_PRIVATE_KEY")
        
        if not client_email or not private_key:
            print("Missing Google Calendar credentials in environment variables")
            return None
        
        # Replace escaped newlines in private key
        private_key = private_key.replace("\\n", "\n")
        
        credentials_info = {
            "type": "service_account",
            "client_email": client_email,
            "private_key": private_key,
            "private_key_id": "dummy",
            "client_id": "dummy",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
        }
        
        credentials = Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/calendar.readonly']
        )
        
        service = build('calendar', 'v3', credentials=credentials)
        return service
    
    except Exception as e:
        print(f"Error initializing Google Calendar service: {e}")
        return None

async def check_upcoming_events() -> bool:
    """
    Check for calendar events starting within the next 10 minutes
    Returns True if there are upcoming events, False otherwise
    """
    try:
        # Run the synchronous Google API call in a thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _check_upcoming_events_sync)
        return result
    except Exception as e:
        print(f"Error checking upcoming events: {e}")
        return False

def _check_upcoming_events_sync() -> bool:
    """Synchronous helper function for checking upcoming events"""
    service = get_calendar_service()
    
    if not service:
        return False
    
    try:
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'  # 'Z' indicates UTC time
        time_max = (now + timedelta(minutes=10)).isoformat() + 'Z'
        
        # Call the Calendar API
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if events:
            print(f"Found {len(events)} upcoming events in the next 10 minutes")
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"  - {event.get('summary', 'No title')} at {start}")
            return True
        else:
            return False
    
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        return False

async def get_calendar_list() -> Optional[List[dict]]:
    """Get list of available calendars for debugging"""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _get_calendar_list_sync)
        return result
    except Exception as e:
        print(f"Error getting calendar list: {e}")
        return None

def _get_calendar_list_sync() -> Optional[List[dict]]:
    """Synchronous helper function for getting calendar list"""
    service = get_calendar_service()
    
    if not service:
        return None
    
    try:
        calendar_list = service.calendarList().list().execute()
        return calendar_list.get('items', [])
    except Exception as e:
        print(f"Error fetching calendar list: {e}")
        return None 