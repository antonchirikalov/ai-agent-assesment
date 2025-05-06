"""
Image analysis tool for the AI agent project.
"""

import os
from typing import Optional
import base64
import io
import openai
from PIL import Image
import logging
from .base_tool import EnhancedTool

class ImageAnalysisTool(EnhancedTool):
    """Tool for analyzing images."""
    
    name = "ImageAnalysisTool"
    description = "Analyze a downloaded image file associated with a task ID using OpenAI Vision. Provide a detailed description of what's in the image."
    inputs = {
        "task_id": {
            "type": "string",
            "description": "Task ID for which the image file has been downloaded"
        },
        "prompt": {
            "type": "string",
            "description": "Optional specific question or aspect to analyze about the image",
            "nullable": True
        }
    }
    output_type = "string"
    
    def __init__(self):
        """Initialize the image analysis tool with OpenAI client."""
        super().__init__()
        self.logger = logging.getLogger()
        
        # Initialize OpenAI client
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            self.logger.warning("OPENAI_API_KEY not found in environment variables")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def forward(self, task_id: str, prompt: str = "Describe what you see in this image in detail.") -> str:
        """
        Analyze an image using OpenAI Vision API.
        
        Args:
            task_id: Task ID for which the image file has been downloaded
            prompt: Specific question or aspect to analyze about the image
            
        Returns:
            Analysis of the image
        """
        try:
            # Check for API key
            if not self.api_key:
                return "Error: OPENAI_API_KEY not set. Cannot analyze image."
            
            filename = f"{task_id}_downloaded_file"
            
            # Check if file exists
            if not os.path.exists(filename):
                return f"Error: Image file for task {task_id} does not exist. Please download it first."
            
            with open(filename, 'rb') as img_file:
                img_bytes = img_file.read()
                
            # Handle potential image format issues
            try:
                img = Image.open(io.BytesIO(img_bytes))
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()
                
                base64_image = base64.b64encode(img_byte_arr).decode('utf-8')
            except Exception as img_error:
                self.logger.error(f"Error processing image: {str(img_error)}")
                return f"Error processing image: {str(img_error)}"
            
            # Try both vision models
            models_to_try = ["gpt-4o", "gpt-4-vision-preview"]
            
            for model in models_to_try:
                try:
                    self.logger.info(f"Attempting image analysis with model: {model}")
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text", 
                                        "text": prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=1000
                    )
                    # Return the content directly
                    return response.choices[0].message.content
                except Exception as model_error:
                    self.logger.warning(f"Failed with model {model}: {str(model_error)}")
                    if model == models_to_try[-1]:  # If this is the last model in the list
                        raise
            
            # Fallback if all models fail but don't raise exceptions
            return f"Unable to analyze the image. All vision models failed."
            
        except Exception as e:
            self.logger.error(f"Error analyzing image: {str(e)}")
            # Return specific error message
            return f"Error analyzing image. The image format may be unsupported or the image may be corrupted." 