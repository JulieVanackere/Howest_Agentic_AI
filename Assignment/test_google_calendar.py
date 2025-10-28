#!/usr/bin/env python3
"""
Direct Google Calendar API test with sample schedule data
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent))

from agents.calendar_agent import GoogleCalendarIntegration
import json

def test_google_calendar_with_sample_data():
    """
    Test Google Calendar integration with sample schedule data
    """
    print("🗓️  TESTING GOOGLE CALENDAR API INTEGRATION")
    print("="*60)
    
    # Sample schedule data - exactly as you provided
    schedule = [
        {
            "course": "Wiskunde I", 
            "type": "Lecture", 
            "location": "A0.030",
            "date": "2025-09-01", 
            "day": "Monday", 
            "from": "08:30", 
            "to": "10:30"
        },
        {
            "course": "Fysica", 
            "type": "Lab", 
            "location": "B1.020",
            "date": "2025-09-02", 
            "day": "Tuesday", 
            "from": "14:00", 
            "to": "16:00"
        },
        {
            "course": "Chemie", 
            "type": "Exercise", 
            "location": "C2.010",
            "date": "2025-09-03", 
            "day": "Wednesday", 
            "from": "10:00", 
            "to": "12:00"
        }
    ]
    
    print(f"📊 Sample schedule data:")
    for i, item in enumerate(schedule, 1):
        print(f"   {i}. {item['course']} - {item['type']}")
        print(f"      📅 {item['date']} ({item['day']})")
        print(f"      🕒 {item['from']} - {item['to']}")
        print(f"      📍 {item['location']}")
        print()
    
    # Initialize Google Calendar integration
    print("🔗 Initializing Google Calendar integration...")
    calendar_integration = GoogleCalendarIntegration()
    
    # Test authentication
    print("🔐 Testing Google Calendar authentication...")
    if not calendar_integration.authenticate():
        print("❌ Authentication failed. Please check your credentials in config.py")
        return
    
    print("✅ Authentication successful!")
    
    # Create events from schedule data
    print(f"\n📅 Creating calendar events...")
    print("-" * 40)
    
    results = calendar_integration.create_events_from_schedule(schedule)
    
    # Display results
    print(f"\n📈 RESULTS SUMMARY:")
    print("=" * 30)
    print(f"📊 Total events processed: {results['total']}")
    print(f"✅ Successfully created: {results['created']}")
    print(f"❌ Failed: {results['failed']}")
    
    if results['errors']:
        print(f"\n⚠️  Errors encountered:")
        for error in results['errors']:
            print(f"   - {error}")
    
    # Test listing upcoming events
    print(f"\n📋 Listing upcoming events (to verify creation)...")
    print("-" * 40)
    
    try:
        upcoming_events = calendar_integration.list_upcoming_events(max_results=10)
        
        if upcoming_events:
            print(f"Found {len(upcoming_events)} upcoming events:")
            for i, event in enumerate(upcoming_events[:5], 1):  # Show first 5
                start = event['start'].get('dateTime', event['start'].get('date'))
                summary = event.get('summary', 'No title')
                location = event.get('location', 'No location')
                print(f"   {i}. {summary}")
                print(f"      📅 {start}")
                print(f"      📍 {location}")
        else:
            print("   No upcoming events found.")
    except Exception as e:
        print(f"   ❌ Error listing events: {str(e)}")
    
    # Final status
    print(f"\n🏁 FINAL STATUS:")
    print("=" * 20)
    if results['created'] > 0:
        print("✅ Google Calendar integration test SUCCESSFUL!")
        print(f"🎉 {results['created']} events were created in your Google Calendar")
        print("📱 Check your Google Calendar app or web interface to verify")
    else:
        print("❌ Google Calendar integration test FAILED")
        print("🔧 Check the error messages above for troubleshooting")
    
    print("\n" + "="*60)

def test_single_event():
    """
    Test creating a single event (minimal test)
    """
    print("\n🧪 TESTING SINGLE EVENT CREATION")
    print("=" * 40)
    
    # Single test event
    test_event = {
        "course": "Test Course", 
        "type": "Test", 
        "location": "Test Room",
        "date": "2025-01-15", 
        "day": "Wednesday", 
        "from": "09:00", 
        "to": "10:00"
    }
    
    print(f"📝 Test event: {test_event['course']}")
    print(f"📅 Date: {test_event['date']} at {test_event['from']}-{test_event['to']}")
    
    # Initialize and test
    calendar_integration = GoogleCalendarIntegration()
    
    if calendar_integration.authenticate():
        # Parse the single event
        google_event = calendar_integration.parse_schedule_item(test_event)
        
        if google_event:
            print("✅ Successfully parsed event to Google Calendar format")
            print(f"📋 Event title: {google_event['summary']}")
            print(f"🕒 Start time: {google_event['start']['dateTime']}")
            print(f"🕐 End time: {google_event['end']['dateTime']}")
            
            # Create the event
            if calendar_integration.create_event(google_event):
                print("🎉 Single event test SUCCESSFUL!")
            else:
                print("❌ Failed to create single event")
        else:
            print("❌ Failed to parse event")
    else:
        print("❌ Authentication failed")

if __name__ == "__main__":
    # Run the full test
    test_google_calendar_with_sample_data()
    
    # Optionally run single event test
    print("\n" + "="*60)
    choice = input("🤔 Would you like to test creating a single event as well? (y/n): ").lower().strip()
    if choice in ['y', 'yes']:
        test_single_event()