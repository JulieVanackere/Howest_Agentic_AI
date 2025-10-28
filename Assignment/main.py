#### Imports ####
import os
from dotenv import load_dotenv
from config.prompts import PARSING_SYSTEM_PROMPT,  PARSING_USER_PROMPT
from agents.parsing_agent import ImageScheduleParser

# Load environment variables
load_dotenv()

# Get Azure OpenAI configuration from environment variables
azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_deployment_name = os.getenv("OPENAI_DEPLOYMENT_NAME")
openai_version_name = os.getenv("OPENAI_VERSION_NAME")

    
# Image file path
image_path = "download.jpeg"  # Adjust this to your image file

# Initialize the parser
parser = ImageScheduleParser(
    azure_endpoint=azure_openai_endpoint,
    api_key=azure_openai_api_key,
    api_version=openai_version_name,
    deployment_name=openai_deployment_name
    )
        
# Load prompts
system_prompt = PARSING_SYSTEM_PROMPT
user_prompt = PARSING_USER_PROMPT

# Parse the schedule from image
result = parser.parse_schedule_from_image(
    image_path=image_path,
    system_prompt=system_prompt,
    user_prompt=user_prompt
    )

# Display results
print("="*60)
print("IMAGE PROCESSING RESULTS")
print("="*60)
print(f"Success: {result['success']}")
print(f"Method: {result.get('method', 'unknown')}")

if result['success']:
    print(f"Parsed Content:\n{result['parsed_content']}")
    if 'usage' in result and result['usage']:
        print(f"Token Usage: {result['usage']}")
else:
    print(f"Error: {result['error']}")

if result.get('extracted_text') and result['extracted_text'] != "[Processed directly with vision model]":
    print(f"\nExtracted Text (first 200 chars):\n{result['extracted_text']}")

print("="*60)
