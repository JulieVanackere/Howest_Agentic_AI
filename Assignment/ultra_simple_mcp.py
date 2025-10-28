#!/usr/bin/env python3
"""
Ultra-simple MCP function calling example - Schedule ONE event
Mimics OpenAI function calling pattern but uses Azure OpenAI
"""

import json
import requests
import sys
from pathlib import Path

# Import your existing calendar functions
sys.path.append(str(Path(__file__).parent))
from agents.calendar_agent import GoogleCalendarIntegration
from config.config import azure_openai_api_key, azure_openai_endpoint, openai_deployment_name, openai_version_name

def schedule_event(course, event_type, location, date, start_time, end_time):
    """
    The actual function that schedules an event - this gets called by AI
    """
    print(f"🤖 Scheduling: {course} on {date} from {start_time} to {end_time}")
    
    # Create event data
    event_data = {
        "course": course,
        "type": event_type,
        "location": location,
        "date": date,
        "from": start_time,
        "to": end_time
    }
    
    # Use existing calendar integration
    calendar = GoogleCalendarIntegration()
    
    # Authenticate and schedule
    if calendar.authenticate():
        event = calendar.parse_schedule_item(event_data)
        if event and calendar.create_event(event):
            return f"✅ Successfully scheduled {course}!"
        else:
            return "❌ Failed to create event"
    else:
        return "❌ Authentication failed"

def main():
    """
    Simple MCP function calling demo
    """
    print("📅 Simple Calendar MCP Function Calling")
    print("="*50)
    
    # Azure OpenAI setup
    api_url = f"{azure_openai_endpoint.rstrip('/')}/openai/deployments/{openai_deployment_name}/chat/completions?api-version={openai_version_name}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": azure_openai_api_key
    }
    
    # Define the function (MCP tool)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "schedule_event",
                "description": "Schedule a single event in Google Calendar",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course": {"type": "string", "description": "Event/course name"},
                        "event_type": {"type": "string", "description": "Type: lecture, lab, exam, etc."},
                        "location": {"type": "string", "description": "Room or location"},
                        "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                        "start_time": {"type": "string", "description": "Start time HH:MM"},
                        "end_time": {"type": "string", "description": "End time HH:MM"}
                    },
                    "required": ["course", "event_type", "location", "date", "start_time", "end_time"],
                    "additionalProperties": False
                }
            }
        }
    ]
    
    # User message
    messages = [
        {
            "role": "user",
            "content": """Please schedule this class for me:

Python Programming - Lab Session
Tomorrow (2025-10-17) from 10:00 to 12:00
Location: Computer Lab 3

Use the schedule_event function to add it to my calendar."""
        }
    ]
    
    # Request payload
    payload = {
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    print("🤖 Calling AI with function calling...")
    
    # Make API call
    response = requests.post(api_url, headers=headers, json=payload, timeout=60)
    
    # Debug: print response if there's an error
    if response.status_code != 200:
        print(f"❌ Error {response.status_code}: {response.text}")
        return
    
    result = response.json()
    
    # Process response
    message = result["choices"][0]["message"]
    
    print(f"AI says: {message.get('content', '')}")
    
    # Execute function calls
    if message.get("tool_calls"):
        for call in message["tool_calls"]:
            if call["function"]["name"] == "schedule_event":
                # Parse arguments
                args = json.loads(call["function"]["arguments"])
                print(f"\n🔧 AI wants to call: schedule_event({args})")
                
                # Execute the function
                result = schedule_event(
                    course=args["course"],
                    event_type=args.get("event_type", "Class"),
                    location=args.get("location", ""),
                    date=args["date"],
                    start_time=args["start_time"],
                    end_time=args["end_time"]
                )
                
                print(f"📋 Result: {result}")
    else:
        print("⚠️  No function calls made")
    
    print("\n✨ Done!")

if __name__ == "__main__":
    main()