# Calendar Agent: Google Agenda https://developers.google.com/workspace/calendar/api/guides/overview


from __future__ import print_function
import datetime
import json
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import os.path
import pickle
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get Google API credentials from environment variables
Client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

# If modifying these scopes, delete the file token.pickle.

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
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
            creds = flow.run_local_server(port=0)  # automatically opens browser and handles redirect

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service


class GoogleCalendarIntegration:
    """
    Integration class for Google Calendar operations
    """
    
    def __init__(self):
        """
        Initialize Google Calendar integration
        """
        self.service = None
        self.calendar_id = 'primary'  # Use primary calendar by default
    
    def authenticate(self):
        """
        Authenticate with Google Calendar API
        """
        try:
            self.service = get_calendar_service()
            print("✅ Successfully authenticated with Google Calendar")
            return True
        except Exception as e:
            print(f"❌ Authentication failed: {str(e)}")
            return False
    
    def parse_schedule_item(self, item: dict) -> dict:
        """
        Parse a schedule item from the image processing result into Google Calendar event format
        
        Args:
            item: Dictionary containing schedule information
            
        Returns:
            Google Calendar event dictionary
        """
        try:
            # Extract information from the parsed item
            course = item.get('course', 'Unknown Course')
            event_type = item.get('type', 'Class')
            location = item.get('location', '')
            date_str = item.get('date', '')
            day = item.get('day', '')
            start_time = item.get('from', '08:00')
            end_time = item.get('to', '10:00')
            
            # Create event title
            title = f"{course}"
            if event_type:
                title += f" - {event_type}"
            
            # Parse date and time
            if date_str:
                # Use provided date
                event_date = date_str
            else:
                # Calculate date based on day if no specific date provided
                today = datetime.datetime.now()
                days_ahead = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(day.lower())
                days_ahead = days_ahead - today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                event_date = (today + datetime.timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            
            # Create start and end datetime strings
            start_datetime = f"{event_date}T{start_time}:00"
            end_datetime = f"{event_date}T{end_time}:00"
            
            # Create Google Calendar event
            event = {
                'summary': title,
                'location': location,
                'description': f"Course: {course}\nType: {event_type}",
                'start': {
                    'dateTime': start_datetime,
                    'timeZone': 'Europe/Brussels',  # Adjust timezone as needed
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
            
            return event
            
        except Exception as e:
            print(f"❌ Error parsing schedule item: {str(e)}")
            return None
    
    def create_event(self, event: dict) -> bool:
        """
        Create a single event in Google Calendar
        
        Args:
            event: Google Calendar event dictionary
            
        Returns:
            Success status
        """
        try:
            if not self.service:
                print("❌ Calendar service not authenticated")
                return False
            
            created_event = self.service.events().insert(
                calendarId=self.calendar_id, 
                body=event
            ).execute()
            
            print(f"✅ Created event: {event['summary']} on {event['start']['dateTime']}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating event '{event.get('summary', 'Unknown')}': {str(e)}")
            return False
    
    def create_events_from_schedule(self, schedule_data: list) -> dict:
        """
        Create multiple events from parsed schedule data
        
        Args:
            schedule_data: List of schedule items from image processing
            
        Returns:
            Summary of creation results
        """
        results = {
            'total': len(schedule_data),
            'created': 0,
            'failed': 0,
            'errors': []
        }
        
        if not self.service:
            if not self.authenticate():
                results['errors'].append("Failed to authenticate with Google Calendar")
                return results
        
        print(f"\n📅 Creating {len(schedule_data)} calendar events...")
        print("="*50)
        
        for i, item in enumerate(schedule_data, 1):
            print(f"\n[{i}/{len(schedule_data)}] Processing: {item.get('course', 'Unknown Course')}")
            
            # Parse schedule item to Google Calendar event format
            event = self.parse_schedule_item(item)
            
            if event:
                # Create the event
                if self.create_event(event):
                    results['created'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to create event for {item.get('course', 'Unknown Course')}")
            else:
                results['failed'] += 1
                results['errors'].append(f"Failed to parse schedule item: {item}")
        
        return results
    
    def list_upcoming_events(self, max_results: int = 10) -> list:
        """
        List upcoming events from the calendar
        
        Args:
            max_results: Maximum number of events to return
            
        Returns:
            List of upcoming events
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return []
            
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return events
            
        except Exception as e:
            print(f"❌ Error listing events: {str(e)}")
            return []

def integrate_schedule_with_calendar(parsed_schedule_result: dict) -> dict:
    """
    Main function to integrate parsed schedule with Google Calendar
    
    Args:
        parsed_schedule_result: Result from image parsing agent
        
    Returns:
        Integration summary
    """
    print("\n🔗 INTEGRATING SCHEDULE WITH GOOGLE CALENDAR")
    print("="*60)
    
    # Check if parsing was successful
    if not parsed_schedule_result.get('success'):
        return {
            'success': False,
            'error': f"Schedule parsing failed: {parsed_schedule_result.get('error', 'Unknown error')}",
            'calendar_results': None
        }
    
    # Extract schedule data
    parsed_content = parsed_schedule_result.get('parsed_content', '')
    
    # Try to parse JSON from the content
    try:
        if parsed_content.startswith('```json'):
            # Remove code block markers
            json_content = parsed_content.replace('```json', '').replace('```', '').strip()
        else:
            json_content = parsed_content
        
        schedule_data = json.loads(json_content)
        
        # Handle different JSON structures
        if isinstance(schedule_data, dict) and 'schedule' in schedule_data:
            # Extract events from nested structure
            events = []
            for day_data in schedule_data['schedule'].get('days', []):
                for event in day_data.get('events', []):
                    event['day'] = day_data.get('day', '')
                    events.append(event)
            schedule_data = events
        elif isinstance(schedule_data, dict) and not isinstance(schedule_data, list):
            # Single event
            schedule_data = [schedule_data]
        
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f"Failed to parse schedule JSON: {str(e)}",
            'calendar_results': None
        }
    
    print(f"📊 Found {len(schedule_data)} schedule items to process")
    
    # Initialize calendar integration
    calendar_integration = GoogleCalendarIntegration()
    
    # Create events
    results = calendar_integration.create_events_from_schedule(schedule_data)
    
    # Print summary
    print("\n📈 INTEGRATION SUMMARY:")
    print("="*30)
    print(f"Total items: {results['total']}")
    print(f"Successfully created: {results['created']}")
    print(f"Failed: {results['failed']}")
    
    if results['errors']:
        print("\n❌ Errors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    return {
        'success': results['created'] > 0,
        'calendar_results': results,
        'message': f"Successfully created {results['created']} out of {results['total']} calendar events"
    }
