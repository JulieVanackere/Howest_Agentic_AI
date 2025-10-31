"""
Agent-powered Calendar Scheduler

This script uses the openai-agents library to create an intelligent agent
that can schedule events to Google Calendar using natural language input.
"""

import asyncio
import os
import json
import datetime
import pickle
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import agents library
from agents import (
    Agent,
    Runner,
    function_tool,
    set_default_openai_client,
)
from openai import AsyncAzureOpenAI

# Import Google Calendar libraries
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

print("✅ Libraries imported successfully!")

# Configure Azure OpenAI client
azure_client = AsyncAzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version=os.environ.get("OPENAI_VERSION_NAME"), 
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

# Set the default client for the agents library with tracing disabled
set_default_openai_client(azure_client, use_for_tracing=False)

# Completely disable tracing
if 'OPENAI_API_KEY' in os.environ:
    del os.environ['OPENAI_API_KEY']

print("✅ Azure OpenAI client configured!")

# Google Calendar setup
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Get authenticated Google Calendar service"""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Get credentials from environment
            Client_id = os.getenv("GOOGLE_CLIENT_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
            
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": Client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                },
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

@function_tool
async def create_calendar_event(
    title: str,
    date: str,
    start_time: str,
    end_time: str,
    location: str = "",
    description: str = ""
) -> str:
    """
    Create a Google Calendar event
    
    Args:
        title: Event title/name
        date: Event date in YYYY-MM-DD format
        start_time: Start time in HH:MM format (24-hour)
        end_time: End time in HH:MM format (24-hour)
        location: Event location (optional)
        description: Event description (optional)
        
    Returns:
        Success message with event details
    """
    try:
        # Get calendar service
        service = get_calendar_service()
        
        # Create datetime strings (ISO format for Google Calendar)
        start_datetime = f"{date}T{start_time}:00"
        end_datetime = f"{date}T{end_time}:00"
        
        # Build the event structure
        event = {
            'summary': title,
            'location': location,
            'description': description or f"Event: {title}",
            'start': {
                'dateTime': start_datetime,
                'timeZone': 'Europe/Brussels',
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': 'Europe/Brussels',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 15},
                    {'method': 'email', 'minutes': 60},
                ],
            },
        }
        
        # Create the event
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        
        event_link = created_event.get('htmlLink', 'No link available')
        
        return f"✅ Successfully created event: '{title}' on {date} from {start_time} to {end_time}. Event link: {event_link}"
        
    except Exception as e:
        return f"❌ Failed to create event: {str(e)}"

@function_tool 
async def get_current_date() -> str:
    """Get the current date in YYYY-MM-DD format"""
    return datetime.datetime.now().strftime('%Y-%m-%d')

@function_tool
async def parse_event_details(event_description: str) -> str:
    """
    Parse natural language event description into structured format
    
    Args:
        event_description: Natural language description of the event
        
    Returns:
        JSON string with parsed event details
    """
    # This is a simple parser - in a real application, you might use more sophisticated NLP
    import re
    
    # Try to extract date, time, and other details
    details = {
        "title": "",
        "date": "",
        "start_time": "",
        "end_time": "",
        "location": "",
        "description": event_description
    }
    
    # Simple extraction (you could make this more sophisticated)
    date_match = re.search(r'\d{4}-\d{2}-\d{2}', event_description)
    if date_match:
        details["date"] = date_match.group()
    
    time_match = re.search(r'(\d{1,2}):(\d{2})', event_description)
    if time_match:
        details["start_time"] = time_match.group()
        # Assume 1 hour duration if no end time specified
        start_hour = int(time_match.group(1))
        end_hour = start_hour + 1
        details["end_time"] = f"{end_hour:02d}:{time_match.group(2)}"
    
    return json.dumps(details, indent=2)

async def main():
    """Main function to demonstrate the calendar scheduling agent"""
    
    # Create the calendar scheduling agent
    calendar_agent = Agent(
        name="Calendar Scheduler",
        model=os.environ.get("OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
        instructions="""You are a helpful calendar scheduling assistant. 

Your job is to help users schedule events in their Google Calendar. When a user describes an event they want to schedule:

1. Extract the key details: title, date, start time, end time, location, description
2. If any required information is missing (title, date, start_time, end_time), ask the user for clarification
3. Use the create_calendar_event function to schedule the event
4. Provide a clear confirmation of what was scheduled

Required format for times: Use 24-hour format (HH:MM) like 14:30 for 2:30 PM
Required format for dates: Use YYYY-MM-DD format like 2025-10-28

Be friendly and helpful. Always confirm the details before creating the event.""",
        tools=[create_calendar_event, get_current_date, parse_event_details]
    )
    
    print("🤖 Calendar Scheduling Agent Ready!")
    print("="*50)
    
    # Example event to schedule
    example_events = [
        "Schedule a team meeting tomorrow from 2:00 PM to 3:30 PM in Conference Room A",
        "Create an event for 'Machine Learning Lecture' on 2025-10-29 from 09:00 to 11:00 at University Campus",
        "Add 'Dentist Appointment' on 2025-10-30 at 14:30 for 1 hour",
    ]
    
    # Let's schedule one of these events
    event_to_schedule = example_events[1]  # Machine Learning Lecture
    
    print(f"📅 Scheduling Event: {event_to_schedule}")
    print("-" * 50)
    
    try:
        # Run the agent to schedule the event
        result = await Runner().run(
            starting_agent=calendar_agent,
            input=event_to_schedule,
            max_turns=5
        )
        
        print(f"🎉 Agent Response: {result.final_output}")
        
    except Exception as e:
        print(f"❌ Error scheduling event: {e}")
    
    print("\n" + "="*50)
    print("💡 You can modify the 'event_to_schedule' variable above to test different events!")
    print("💡 The agent can handle natural language descriptions and will ask for missing details.")

if __name__ == "__main__":
    asyncio.run(main())