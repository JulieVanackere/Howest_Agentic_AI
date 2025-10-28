import os
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any
import requests

from PIL import Image
import pytesseract
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AzureOpenAIProcessor:
    """
    A class to process images and text using Azure OpenAI (supports both text and vision models)
    """
    
    def __init__(self, 
                 azure_endpoint: str,
                 api_key: str,
                 api_version: str = "2024-02-15-preview",
                 deployment_name: str = "gpt-4o"):
        """
        Initialize Azure OpenAI client
        
        Args:
            azure_endpoint: Azure OpenAI endpoint URL
            api_key: Azure OpenAI API key
            api_version: API version
            deployment_name: Model deployment name (use gpt-4o or gpt-4-vision-preview for image support)
        """
        self.azure_endpoint = azure_endpoint.rstrip('/')
        self.api_key = api_key
        self.api_version = api_version
        self.deployment_name = deployment_name
        
        # Construct the API URL
        self.api_url = f"{self.azure_endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
        
        # Check if this is a vision-capable model
        self.supports_vision = "vision" in deployment_name.lower() or "gpt-4o" in deployment_name.lower()
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode an image to base64 string
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def process_image_directly(self, 
                             image_path: str, 
                             system_prompt: str, 
                             user_prompt: str) -> Dict[str, Any]:
        """
        Process an image directly using Azure OpenAI Vision models (GPT-4o, GPT-4V)
        
        Args:
            image_path: Path to the image file
            system_prompt: System prompt for the AI
            user_prompt: User prompt
            
        Returns:
            Response from Azure OpenAI
        """
        try:
            if not self.supports_vision:
                return {
                    "success": False,
                    "error": f"Model {self.deployment_name} does not support vision. Use gpt-4o or gpt-4-vision-preview.",
                    "content": None
                }
            
            # Encode image to base64
            base64_image = self.encode_image_to_base64(image_path)
            
            # Determine image type
            image_extension = Path(image_path).suffix.lower()
            if image_extension in ['.jpg', '.jpeg']:
                image_media_type = "image/jpeg"
            elif image_extension == '.png':
                image_media_type = "image/png"
            elif image_extension == '.webp':
                image_media_type = "image/webp"
            else:
                image_media_type = "image/jpeg"  # Default fallback
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "api-key": self.api_key
            }
            
            # Prepare the request payload with image
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_media_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 4000
            }
            
            # Make the API call
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=120  # Longer timeout for image processing
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            
            # Extract the response content
            content = response_data["choices"][0]["message"]["content"]
            
            logger.info("Successfully processed image with Azure OpenAI Vision")
            
            return {
                "success": True,
                "content": content,
                "usage": response_data.get("usage", {}),
                "method": "vision"
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error processing image with Azure OpenAI: {str(e)}")
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "content": None
            }
        except Exception as e:
            logger.error(f"Error processing image with Azure OpenAI: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }

    def process_extracted_text(self, 
                             extracted_text: str, 
                             system_prompt: str, 
                             user_prompt: str) -> Dict[str, Any]:
        """
        Process the extracted text using Azure OpenAI (fallback for non-vision models)
        
        Args:
            extracted_text: Text extracted from the image
            system_prompt: System prompt for the AI
            user_prompt: User prompt template
            
        Returns:
            Response from Azure OpenAI
        """
        try:
            # Combine user prompt with extracted text
            full_user_prompt = f"{user_prompt}\n\nExtracted text from image:\n{extracted_text}"
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "api-key": self.api_key
            }
            
            # Prepare the request payload
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 4000
            }
            
            # Make the API call
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            
            # Extract the response content
            content = response_data["choices"][0]["message"]["content"]
            
            logger.info("Successfully processed text with Azure OpenAI")
            
            return {
                "success": True,
                "content": content,
                "usage": response_data.get("usage", {}),
                "method": "text"
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error processing text with Azure OpenAI: {str(e)}")
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "content": None
            }
        except Exception as e:
            logger.error(f"Error processing text with Azure OpenAI: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }





