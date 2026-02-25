"""
Simplified Gemini service - only handles LLM API calls.
Prompt building is now in prompt_builder.py.
"""
import os
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


class GeminiService:
    """
    Service for interacting with Google Gemini API.
    Simplified to only handle LLM calls - prompt building is in prompt_builder.py.
    """
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def generate_content(self, prompt: str, image_data: Optional[str] = None) -> str:
        """
        Generate content from Gemini API with optional image input.
        
        Args:
            prompt: The prompt to send to the model
            image_data: Optional base64 encoded image data (JPEG)
        
        Returns:
            Response text from the model
        """
        import base64
        
        # Build content list (text + optional image)
        content_parts = [prompt]
        
        if image_data:
            try:
                # Decode base64 image data
                image_bytes = base64.b64decode(image_data)
                content_parts.append({
                    "mime_type": "image/jpeg",
                    "data": image_bytes
                })
            except Exception as e:
                print(f"Warning: Failed to decode image data: {e}")
                # Continue without image if decoding fails
        
        try:
            response = self.model.generate_content(
                content_parts,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def generate_text(self, prompt: str) -> str:
        """
        Generate plain text from Gemini API (not JSON).
        Used for text refinement tasks.
        
        Args:
            prompt: The prompt to send to the model
        
        Returns:
            Response text from the model
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise

