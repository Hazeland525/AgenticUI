"""
Text-to-speech route using ElevenLabs API.
Keeps ELEVENLABS_API_KEY server-side; returns audio for playback.
"""
import os
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter()

# Default voice: Rachel (change via ELEVENLABS_VOICE_ID in .env)
DEFAULT_VOICE_ID = "tnSpp4vdxKPjI9w0GnoV"
ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


class TTSRequest(BaseModel):
    text: str


@router.post("/text-to-speech")
def text_to_speech(request: TTSRequest):
    """
    Convert text to speech via ElevenLabs. Returns audio/mpeg.
    Used for verbal summary playback (TTS only, not displayed in UI).
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logger.warning("ELEVENLABS_API_KEY not set; TTS disabled")
        raise HTTPException(status_code=503, detail="TTS not configured (missing ELEVENLABS_API_KEY)")

    voice_id = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID).strip() or DEFAULT_VOICE_ID
    text = (request.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    try:
        import requests
    except ImportError:
        raise HTTPException(status_code=500, detail="requests library required for TTS")

    url = ELEVENLABS_URL.format(voice_id=voice_id)
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    payload = {"text": text}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"ElevenLabs TTS error: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                err_body = e.response.text
            except Exception:
                err_body = ""
            raise HTTPException(
                status_code=e.response.status_code if hasattr(e, "response") else 502,
                detail=err_body or str(e),
            )
        raise HTTPException(status_code=502, detail=str(e))

    return Response(
        content=resp.content,
        media_type="audio/mpeg",
    )
