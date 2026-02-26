"""
Google Cloud Speech-to-Text service.
Uses Speech-to-Text V2 with Chirp 2 model when credentials are available;
falls back to V1 REST (API key) when only GEMINI_API_KEY is set.
"""
import os
import base64
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# V2: Chirp 2 model (better accuracy)
try:
    from google.cloud.speech_v2 import SpeechClient as SpeechClientV2
    from google.cloud.speech_v2.types import cloud_speech
    HAS_SPEECH_V2 = True
except ImportError:
    HAS_SPEECH_V2 = False

# V1: for API-key-only fallback
try:
    from google.cloud import speech_v1
    from google.oauth2 import service_account
    HAS_GOOGLE_CLOUD_LIB = True
except ImportError:
    HAS_GOOGLE_CLOUD_LIB = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# Chirp 2 is available in these regions; "global" uses default routing
CHIRP2_LOCATION = os.getenv("SPEECH_V2_LOCATION", "us-central1")


def _get_project_id(credentials_path: Optional[str]) -> Optional[str]:
    """Get project ID from env or from service account JSON."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        return project_id
    if not credentials_path or not os.path.exists(credentials_path):
        return None
    try:
        with open(credentials_path, "r") as f:
            data = json.load(f)
            return data.get("project_id")
    except Exception:
        return None


class SpeechService:
    """
    Service for Google Cloud Speech-to-Text.
    Prefers V2 API with Chirp 2 model when project + credentials are available;
    otherwise uses V1 REST with API key.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path and not os.path.isabs(credentials_path):
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            credentials_path = os.path.join(backend_dir, credentials_path)

        print(f"[SpeechService] Initializing... api_key={'***' if api_key else None}, credentials_path={credentials_path}")

        self.use_rest_api = False
        self.api_key = None
        self.client_v1 = None
        self.client_v2 = None
        self.project_id = None
        self.recognizer = None

        # Prefer V2 with Chirp 2 when we have project ID (from env or service account JSON)
        project_id = _get_project_id(credentials_path)
        if HAS_SPEECH_V2 and project_id:
            try:
                if credentials_path and os.path.exists(credentials_path):
                    if not HAS_GOOGLE_CLOUD_LIB:
                        raise ValueError("google-auth/service_account needed for V2")
                    credentials = service_account.Credentials.from_service_account_file(credentials_path)
                    self.client_v2 = SpeechClientV2(credentials=credentials)
                else:
                    self.client_v2 = SpeechClientV2()
                self.project_id = project_id
                self.recognizer = f"projects/{self.project_id}/locations/{CHIRP2_LOCATION}/recognizers/_"
                print(f"[SpeechService] Using Speech-to-Text V2 with Chirp 2 (location={CHIRP2_LOCATION})")
                return
            except Exception as e:
                print(f"[SpeechService] V2 init failed, falling back: {e}")

        # Fallback: API key with V1 REST
        if api_key:
            if not HAS_REQUESTS:
                raise ValueError("requests library not installed. Install with: pip install requests")
            if not project_id:
                print("[SpeechService] Using API key with V1 REST. For Chirp 2: add GOOGLE_CLOUD_PROJECT=your-project-id to backend/.env and set GOOGLE_APPLICATION_CREDENTIALS to a service account JSON path.")
            else:
                print("[SpeechService] Using API key with V1 REST (V2 init failed; check credentials for Chirp 2).")
            self.api_key = api_key
            self.use_rest_api = True
            return

        # Fallback: V1 client with service account
        if credentials_path and os.path.exists(credentials_path):
            if not HAS_GOOGLE_CLOUD_LIB:
                raise ValueError("google-cloud-speech not installed. pip install google-cloud-speech")
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client_v1 = speech_v1.SpeechClient(credentials=credentials)
            print("[SpeechService] Using Speech-to-Text V1 client (for Chirp 2, set GOOGLE_CLOUD_PROJECT)")
            return

        # ADC for V1
        if HAS_GOOGLE_CLOUD_LIB:
            try:
                self.client_v1 = speech_v1.SpeechClient()
                print("[SpeechService] Using V1 Application Default Credentials")
                return
            except Exception as e:
                pass
        raise ValueError(
            "No credentials found. Set GEMINI_API_KEY for V1 REST, or GOOGLE_CLOUD_PROJECT + "
            "GOOGLE_APPLICATION_CREDENTIALS for V2 Chirp 2."
        )

    def transcribe_audio(
        self,
        audio_data: bytes,
        language_code: str = "en-US",
        audio_format: str = "webm_opus",
    ) -> str:
        if self.client_v2 and self.recognizer:
            return self._transcribe_v2_chirp2(audio_data, language_code, audio_format)
        if self.use_rest_api:
            return self._transcribe_with_rest_api(audio_data, language_code, audio_format)
        return self._transcribe_with_client_library_v1(audio_data, language_code, audio_format)

    def _transcribe_v2_chirp2(
        self,
        audio_data: bytes,
        language_code: str,
        audio_format: str,
    ) -> str:
        """Transcribe using Speech-to-Text V2 with Chirp 2 model."""
        try:
            config = cloud_speech.RecognitionConfig(
                auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
                language_codes=[language_code],
                model="chirp_2",
            )
            request = cloud_speech.RecognizeRequest(
                recognizer=self.recognizer,
                config=config,
                content=audio_data,
            )
            response = self.client_v2.recognize(request=request)
            transcript = ""
            for result in response.results:
                if result.alternatives:
                    transcript += result.alternatives[0].transcript
            print(f"[SpeechService] V2 Chirp 2 result: '{transcript.strip()}'")
            return transcript.strip()
        except Exception as e:
            print(f"Error transcribing with V2 Chirp 2: {e}")
            import traceback
            print(traceback.format_exc())
            raise

    def _transcribe_with_rest_api(
        self,
        audio_data: bytes,
        language_code: str,
        audio_format: str,
    ) -> str:
        """Transcribe using V1 REST API with API key."""
        try:
            encoding_map = {
                "webm_opus": "WEBM_OPUS",
                "linear16": "LINEAR16",
                "flac": "FLAC",
            }
            encoding = encoding_map.get(audio_format, "WEBM_OPUS")
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            config = {
                "encoding": encoding,
                "languageCode": language_code,
                "enableAutomaticPunctuation": True,
            }
            if audio_format == "linear16":
                config["sampleRateHertz"] = 16000
            elif audio_format == "webm_opus":
                config["sampleRateHertz"] = 48000
            payload = {"config": config, "audio": {"content": audio_base64}}
            url = f"https://speech.googleapis.com/v1/speech:recognize?key={self.api_key}"
            print(f"[SpeechService] Calling V1 REST API: {url[:50]}...")
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            transcript = ""
            if "results" in result:
                for result_item in result["results"]:
                    if result_item.get("alternatives"):
                        transcript += result_item["alternatives"][0].get("transcript", "")
            print(f"[SpeechService] V1 REST result: '{transcript.strip()}'")
            return transcript.strip()
        except requests.exceptions.RequestException as e:
            print(f"Error calling V1 REST API: {e}")
            if getattr(e, "response", None) is not None:
                try:
                    print(f"Error response: {e.response.json()}")
                except Exception:
                    print(f"Error response text: {e.response.text}")
            import traceback
            print(traceback.format_exc())
            raise
        except Exception as e:
            print(f"Error transcribing with V1 REST: {e}")
            import traceback
            print(traceback.format_exc())
            raise

    def _transcribe_with_client_library_v1(
        self,
        audio_data: bytes,
        language_code: str,
        audio_format: str,
    ) -> str:
        """Transcribe using V1 client library (service account / ADC)."""
        try:
            encoding_map = {
                "webm_opus": speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                "linear16": speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
                "flac": speech_v1.RecognitionConfig.AudioEncoding.FLAC,
            }
            encoding = encoding_map.get(
                audio_format,
                speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            )
            config = speech_v1.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=16000 if audio_format == "linear16" else None,
                language_code=language_code,
                enable_automatic_punctuation=True,
            )
            audio = speech_v1.RecognitionAudio(content=audio_data)
            response = self.client_v1.recognize(config=config, audio=audio)
            transcript = ""
            for result in response.results:
                if result.alternatives:
                    transcript += result.alternatives[0].transcript
            return transcript.strip()
        except Exception as e:
            print(f"Error transcribing with V1 client: {e}")
            import traceback
            print(traceback.format_exc())
            raise

    def transcribe_base64_audio(
        self,
        base64_audio: str,
        language_code: str = "en-US",
        audio_format: str = "webm_opus",
    ) -> str:
        try:
            print(f"[SpeechService] Decoding base64 audio: length={len(base64_audio)}, format={audio_format}")
            if "," in base64_audio:
                base64_audio = base64_audio.split(",")[1]
            audio_data = base64.b64decode(base64_audio)
            print(f"[SpeechService] Decoded audio: {len(audio_data)} bytes")
            return self.transcribe_audio(audio_data, language_code, audio_format)
        except Exception as e:
            print(f"Error decoding base64 audio: {e}")
            import traceback
            print(traceback.format_exc())
            raise
