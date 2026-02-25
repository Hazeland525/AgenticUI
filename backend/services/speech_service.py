"""
Google Cloud Speech-to-Text service.
Supports both service account JSON and API key authentication.
"""
import os
import base64
from typing import Optional
from dotenv import load_dotenv
import json

load_dotenv()

# Try to import google-cloud-speech (for service account auth)
try:
    from google.cloud import speech_v1
    from google.oauth2 import service_account
    HAS_GOOGLE_CLOUD_LIB = True
except ImportError:
    HAS_GOOGLE_CLOUD_LIB = False

# Import requests for REST API calls
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class SpeechService:
    """
    Service for Google Cloud Speech-to-Text API.
    Supports both service account (via client library) and API key (via REST API).
    """
    
    def __init__(self):
        # Prioritize API key over service account credentials
        api_key = os.getenv("GEMINI_API_KEY")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        print(f"[SpeechService] Initializing... api_key={'***' if api_key else None}, credentials_path={credentials_path}")
        
        self.use_rest_api = False
        self.api_key = None
        self.client = None
        
        if api_key:
            # Use API key with REST API
            if not HAS_REQUESTS:
                raise ValueError("requests library not installed. Install with: pip install requests")
            
            print("[SpeechService] Using API key with REST API")
            self.api_key = api_key
            self.use_rest_api = True
            self.client = None
            print("[SpeechService] Successfully initialized with API key (REST API mode)")
        elif credentials_path:
            # Use service account JSON file (only if API key not available)
            if not HAS_GOOGLE_CLOUD_LIB:
                raise ValueError("google-cloud-speech library not installed. Install with: pip install google-cloud-speech")
            
            # Handle both absolute and relative paths
            if not os.path.isabs(credentials_path):
                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                credentials_path = os.path.join(backend_dir, credentials_path)
            
            print(f"[SpeechService] Using service account from: {credentials_path}")
            if os.path.exists(credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
                self.client = speech_v1.SpeechClient(credentials=credentials)
                print("[SpeechService] Successfully initialized with service account")
            else:
                raise ValueError(f"Service account file not found: {credentials_path}")
        else:
            # Fallback: Try Application Default Credentials
            if not HAS_GOOGLE_CLOUD_LIB:
                raise ValueError(
                    "No credentials found and google-cloud-speech not installed. "
                    "Set GEMINI_API_KEY for REST API mode."
                )
            
            print("[SpeechService] Trying Application Default Credentials as fallback")
            try:
                self.client = speech_v1.SpeechClient()
                print("[SpeechService] Successfully initialized with Application Default Credentials")
            except Exception as e:
                raise ValueError(
                    "No credentials found. Set GEMINI_API_KEY for REST API mode. "
                    f"Error: {e}"
                )
    
    def transcribe_audio(self, audio_data: bytes, language_code: str = "en-US", audio_format: str = "webm_opus") -> str:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes
            language_code: Language code (default: en-US)
            audio_format: Audio format - "webm_opus", "linear16", or "flac" (default: webm_opus)
        
        Returns:
            Transcribed text
        """
        if self.use_rest_api:
            return self._transcribe_with_rest_api(audio_data, language_code, audio_format)
        else:
            return self._transcribe_with_client_library(audio_data, language_code, audio_format)
    
    def _transcribe_with_rest_api(self, audio_data: bytes, language_code: str, audio_format: str) -> str:
        """Transcribe using REST API with API key"""
        try:
            # Map format string to Google Cloud encoding
            encoding_map = {
                "webm_opus": "WEBM_OPUS",
                "linear16": "LINEAR16",
                "flac": "FLAC",
            }
            
            encoding = encoding_map.get(audio_format, "WEBM_OPUS")
            
            # Encode audio to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Build request payload
            config = {
                "encoding": encoding,
                "languageCode": language_code,
                "enableAutomaticPunctuation": True,
            }
            
            # Add sample rate - required for WEBM_OPUS and LINEAR16
            if audio_format == "linear16":
                config["sampleRateHertz"] = 16000
            elif audio_format == "webm_opus":
                # WEBM_OPUS typically uses 48000 Hz, but can also be 16000, 24000, etc.
                # We'll use 48000 as it's the most common for WebM Opus
                config["sampleRateHertz"] = 48000
            
            payload = {
                "config": config,
                "audio": {
                    "content": audio_base64
                }
            }
            
            # Make REST API call
            url = f"https://speech.googleapis.com/v1/speech:recognize?key={self.api_key}"
            print(f"[SpeechService] Calling REST API: {url[:50]}...")
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract transcript
            transcript = ""
            if "results" in result:
                for result_item in result["results"]:
                    if "alternatives" in result_item and len(result_item["alternatives"]) > 0:
                        transcript += result_item["alternatives"][0].get("transcript", "")
            
            print(f"[SpeechService] REST API transcription result: '{transcript}'")
            return transcript.strip()
            
        except requests.exceptions.RequestException as e:
            print(f"Error calling REST API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"Error response: {error_detail}")
                except:
                    print(f"Error response text: {e.response.text}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise
        except Exception as e:
            print(f"Error transcribing with REST API: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _transcribe_with_client_library(self, audio_data: bytes, language_code: str, audio_format: str) -> str:
        """Transcribe using Google Cloud client library (service account)"""
        try:
            # Map format string to Google Cloud encoding enum
            encoding_map = {
                "webm_opus": speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                "linear16": speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
                "flac": speech_v1.RecognitionConfig.AudioEncoding.FLAC,
            }
            
            encoding = encoding_map.get(audio_format, speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS)
            
            # Configure recognition
            config = speech_v1.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=16000 if audio_format == "linear16" else None,  # Only needed for LINEAR16
                language_code=language_code,
                enable_automatic_punctuation=True,
            )
            
            audio = speech_v1.RecognitionAudio(content=audio_data)
            
            # Perform the transcription
            response = self.client.recognize(config=config, audio=audio)
            
            # Extract transcript
            transcript = ""
            for result in response.results:
                if result.alternatives:
                    transcript += result.alternatives[0].transcript
            
            return transcript.strip()
            
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
    def transcribe_base64_audio(self, base64_audio: str, language_code: str = "en-US", audio_format: str = "webm_opus") -> str:
        """
        Transcribe base64-encoded audio data to text.
        
        Args:
            base64_audio: Base64-encoded audio string
            language_code: Language code (default: en-US)
            audio_format: Audio format - "webm_opus", "linear16", or "flac" (default: webm_opus)
        
        Returns:
            Transcribed text
        """
        try:
            print(f"[SpeechService] Decoding base64 audio: length={len(base64_audio)}, format={audio_format}")
            # Handle data URL format (data:audio/webm;base64,...) if present
            if ',' in base64_audio:
                base64_audio = base64_audio.split(',')[1]
            audio_data = base64.b64decode(base64_audio)
            print(f"[SpeechService] Decoded audio: {len(audio_data)} bytes")
            return self.transcribe_audio(audio_data, language_code, audio_format)
        except Exception as e:
            print(f"Error decoding base64 audio: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise
