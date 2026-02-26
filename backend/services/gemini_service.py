"""
Simplified Gemini service - only handles LLM API calls.
Prompt building is now in prompt_builder.py.
"""
import base64
import os
from typing import Generator, Optional
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

AUDIO_REFINE_PROMPT = """Listen to this audio. The user is asking a question about a video.
Transcribe and refine the speech into exactly one clear, concise question.
Output only that question, then a newline, then exactly the three characters: ---
Do not output anything before the question or after the ---."""


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
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
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

    def stream_transcribe_and_refine(self, audio_base64: str) -> Generator[str, None, None]:
        """
        Send audio to Gemini and stream back transcribed/refined text (one question).
        Caller should buffer and detect delimiter "\\n---" to know when the refined question is complete.
        
        Args:
            audio_base64: Base64-encoded audio (e.g. WebM Opus from browser)
        
        Yields:
            Text chunks from the model
        """
        if "," in audio_base64:
            audio_base64 = audio_base64.split(",", 1)[1]
        audio_bytes = base64.b64decode(audio_base64)
        content_parts = [
            AUDIO_REFINE_PROMPT,
            {"mime_type": "audio/webm", "data": audio_bytes},
        ]
        try:
            response = self.model.generate_content(
                content_parts,
                stream=True,
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            print(f"Error streaming from Gemini (audio): {e}")
            import traceback
            print(traceback.format_exc())
            raise

