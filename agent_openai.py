"""
Comprehensive example demonstrating AdvancedSQLiteSession functionality.

This example shows both basic session memory features and advanced conversation
branching capabilities, including usage statistics, turn-based organization,
and multi-timeline conversation management.
"""

import asyncio
# Create specialized agents using openai-agents with proper Azure configuration
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the agents library with proper error handling

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrail,
    InputGuardrailTripwireTriggered,
    Runner,
    RunResult,
    function_tool,
    set_default_openai_client,
)
from openai import AsyncAzureOpenAI
from pydantic import BaseModel
from agents.extensions.memory import AdvancedSQLiteSession

print("✅ Agents library imported successfully!")
use_guardrails = True  
# Configure Azure OpenAI client properly
azure_client = AsyncAzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        api_version=os.environ.get("OPENAI_VERSION_NAME"), 
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    )
# Set the default client for the agents library with tracing disabled
set_default_openai_client(azure_client, use_for_tracing=False)

# Completely disable tracing by unsetting OPENAI_API_KEY if it exists
if 'OPENAI_API_KEY' in os.environ:
    del os.environ['OPENAI_API_KEY']

print("✅ Azure OpenAI client configured for agents!")
# Create an advanced session instance
session = AdvancedSQLiteSession(
    session_id="conversation_comprehensive",
    create_tables=True,
    )


# Create agents with proper model specification
model_name = os.environ.get("OPENAI_DEPLOYMENT_NAME", "gpt-4o")
@function_tool
async def get_weather(city: str) -> str:
    if city.strip().lower() == "new york":
        return f"The weather in {city} is cloudy."
    return f"The weather in {city} is sunny."


async def main():
    # Create an agent
    agent = Agent(
        name="Assistant",
        instructions="Reply very concisely.",
        model=model_name,
        tools=[get_weather],
    )


    print("=== AdvancedSQLiteSession Comprehensive Example ===")
    print("This example demonstrates both basic and advanced session features.\n")

    # === PART 1: Basic Session Functionality ===
    print("=== PART 1: Basic Session Memory ===")
    print("The agent will remember previous messages with structured tracking.\n")

    # First turn
    print("First turn:")
    print("User: What city is the Golden Gate Bridge in?")
    result = await Runner().run(
        agent,
        "What city is the Golden Gate Bridge in?", 
        session=session
    )
    print(f"Assistant: {result.final_output}")
if __name__ == "__main__":
    asyncio.run(main())