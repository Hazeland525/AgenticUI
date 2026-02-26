"""
Agent executor - FastAPI route handler for agent endpoints.
Similar to A2UI's agent_executor.py pattern.
"""
import asyncio
import json
import logging
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from agent import Agent
from services.image_search import ImageSearchService
from services.gemini_service import GeminiService
from services.speech_service import SpeechService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize agent instance (singleton pattern)
_agent_instance: Optional[Agent] = None
_image_search_service: Optional[ImageSearchService] = None
_gemini_service: Optional[GeminiService] = None
_speech_service: Optional[SpeechService] = None


def get_agent() -> Agent:
    """Get or create agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = Agent()
    return _agent_instance


def get_image_search_service() -> ImageSearchService:
    """Get or create image search service instance"""
    global _image_search_service
    if _image_search_service is None:
        _image_search_service = ImageSearchService()
    return _image_search_service


def get_gemini_service() -> GeminiService:
    """Get or create Gemini service instance"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service


def get_speech_service() -> SpeechService:
    """Get or create speech service instance"""
    global _speech_service
    if _speech_service is None:
        _speech_service = SpeechService()
    return _speech_service


class AskRequest(BaseModel):
    """Request model for /ask endpoint"""
    question: str
    videoTime: Optional[float] = None
    videoDuration: Optional[float] = None
    transcriptSnippet: Optional[str] = None
    videoFrame: Optional[str] = None  # Base64 encoded image data


class AskResponse(BaseModel):
    """Response model for /ask endpoint"""
    uiSchema: dict
    verbalSummary: Optional[str] = None  # Short summary for TTS only, not displayed in UI


async def _execute_ask(
    question: str,
    video_frame: Optional[str] = None,
    video_time: Optional[float] = None,
    video_duration: Optional[float] = None,
    transcript_snippet: Optional[str] = None,
) -> AskResponse:
    """Shared logic: generate UI schema, image search, verbal summary, return AskResponse."""
    t_start = time.perf_counter()
    agent = get_agent()
    t0 = time.perf_counter()
    ui_response = await agent.generate_ui_schema(
        question=question,
        video_time=video_time,
        video_duration=video_duration,
        transcript_snippet=transcript_snippet,
        video_frame=video_frame,
    )
    t_schema = time.perf_counter() - t0
    logger.info(f"[TIMING] _execute_ask — generate_ui_schema: {t_schema:.2f}s")
    ui_schema_dict = ui_response.model_dump()
    answer_context = _extract_answer_context(ui_schema_dict)
    logger.info(f"Extracted answer context: {answer_context[:200]}...")
    image_search = get_image_search_service()
    gemini = get_gemini_service()
    logger.info(f"[IMAGE SEARCH] question={question!r} answer_context={answer_context[:150]!r}...")
    t_parallel_start = time.perf_counter()

    async def run_image_search():
        return await image_search.search_image(question=question, answer_context=answer_context)

    async def run_verbal_summary():
        if not answer_context or not answer_context.strip():
            return None
        try:
            prompt = (
                f"The user asked: \"{question}\"\n\n"
                f"Here is the full answer content:\n{answer_context[:3000]}\n\n"
                "In 1-2 short, conversational sentences, summarize this for a quick voice-over. "
                "Do not read the full answer. Reply with only the spoken summary, no quotes or labels."
            )
            out = await gemini.generate_text(prompt)
            return out.strip() if out else None
        except Exception as e:
            logger.warning(f"Failed to generate verbal summary: {e}")
            return None

    selected_image, verbal_summary = await asyncio.gather(run_image_search(), run_verbal_summary())
    t_parallel = time.perf_counter() - t_parallel_start
    logger.info(f"[TIMING] _execute_ask — image_search + verbal_summary: {t_parallel:.2f}s")
    if verbal_summary:
        logger.info(f"[VERBAL ANSWER] {verbal_summary!r}")
    replaced_any_image = False
    if selected_image:
        logger.info(f"[IMAGE SEARCH] result=OK id={selected_image['id']!r} category={selected_image['category']!r}")
        image_data_url = image_search.get_image_as_data_url(selected_image["path"])
        if image_data_url:
            for component in ui_schema_dict.get("components", []):
                comp_def = component.get("component", {})
                if "Image" not in comp_def:
                    continue
                image_props = comp_def["Image"]
                url_value = image_props.get("url") or image_props.get("imageUrl")
                if isinstance(url_value, dict) and "literalString" in url_value:
                    url_str = url_value["literalString"]
                elif isinstance(url_value, str):
                    url_str = url_value
                else:
                    continue
                if not (any(p in url_str for p in ["example.com", "youtube.com", "placeholder", "VIDEO_FRAME_PLACEHOLDER", "imgur.com"])
                        or url_str.startswith("http://") or url_str.startswith("https://")):
                    continue
                image_props["url"] = {"literalString": image_data_url}
                if "imageUrl" in image_props:
                    del image_props["imageUrl"]
                replaced_any_image = True
        else:
            logger.warning(f"Failed to load image file: {selected_image['path']}")
        # If we have a matched image but the LLM didn't include any Image component, inject a hero
        if image_data_url and not replaced_any_image:
            _inject_hero_image(ui_schema_dict, image_data_url)
    else:
        logger.warning("[IMAGE SEARCH] result=null")
        _remove_placeholder_images(ui_schema_dict)
    _truncate_schema_body_text(ui_schema_dict)
    t_total = time.perf_counter() - t_start
    logger.info(f"[TIMING] _execute_ask — TOTAL: {t_total:.2f}s")
    return AskResponse(uiSchema=ui_schema_dict, verbalSummary=verbal_summary)


@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Handle question requests and return UI schema."""
    try:
        return await _execute_ask(
            question=request.question,
            video_frame=request.videoFrame,
            video_time=request.videoTime,
            video_duration=request.videoDuration,
            transcript_snippet=request.transcriptSnippet,
        )
    except Exception as e:
        logger.error(f"Error in /ask endpoint: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


class AskWithVoiceRequest(BaseModel):
    """Request model for /ask-with-voice endpoint (SSE stream)."""
    audio_data: str  # Base64 encoded audio (WebM Opus)
    videoFrame: Optional[str] = None
    videoTime: Optional[float] = None
    videoDuration: Optional[float] = None
    transcriptSnippet: Optional[str] = None


def _sse_message(event: str, data: dict) -> str:
    """Format one SSE message (event + data line)."""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/ask-with-voice")
async def ask_with_voice(request: AskWithVoiceRequest):
    """
    Audio → Gemini Call 1 (stream transcribe+refine) → as soon as refined question is available,
    fire Call 2 (main ask with image) in parallel. Stream transcript chunks via SSE, then send result.
    """
    async def event_stream():
        queue = asyncio.Queue()
        loop = asyncio.get_event_loop()
        refined_question = None
        call2_started = False

        def run_stream():
            try:
                gemini = get_gemini_service()
                for chunk in gemini.stream_transcribe_and_refine(request.audio_data):
                    loop.call_soon_threadsafe(queue.put_nowait, ("chunk", chunk))
            except Exception as e:
                logger.exception("ask-with-voice stream failed")
                loop.call_soon_threadsafe(queue.put_nowait, ("error", str(e)))
            loop.call_soon_threadsafe(queue.put_nowait, ("stream_done", None))

        async def run_call2():
            nonlocal refined_question
            try:
                result = await _execute_ask(
                    question=refined_question or "",
                    video_frame=request.videoFrame,
                    video_time=request.videoTime,
                    video_duration=request.videoDuration,
                    transcript_snippet=request.transcriptSnippet,
                )
                loop.call_soon_threadsafe(queue.put_nowait, ("result", result.model_dump()))
            except Exception as e:
                logger.exception("ask-with-voice call2 failed")
                loop.call_soon_threadsafe(queue.put_nowait, ("error", str(e)))

        loop.run_in_executor(None, run_stream)
        buffer = ""
        try:
            while True:
                event_type, payload = await queue.get()
                if event_type == "chunk":
                    buffer += payload
                    yield _sse_message("transcript_chunk", {"text": payload})
                    if "\n---" in buffer and not call2_started:
                        call2_started = True
                        refined_question = buffer.split("\n---")[0].strip()
                        if refined_question:
                            asyncio.create_task(run_call2())
                        else:
                            loop.call_soon_threadsafe(
                                queue.put_nowait,
                                ("error", "Empty refined question"),
                            )
                elif event_type == "stream_done":
                    if not call2_started:
                        refined_question = (buffer.strip().split("\n---")[0].strip() or buffer.strip()) if buffer.strip() else ""
                        if refined_question:
                            call2_started = True
                            asyncio.create_task(run_call2())
                        else:
                            loop.call_soon_threadsafe(queue.put_nowait, ("error", "No question from audio"))
                    break
                elif event_type == "result":
                    yield _sse_message("result", payload)
                    return
                elif event_type == "error":
                    yield _sse_message("error", {"message": payload})
                    return
            while True:
                event_type, payload = await queue.get()
                if event_type == "result":
                    yield _sse_message("result", payload)
                    return
                if event_type == "error":
                    yield _sse_message("error", {"message": payload})
                    return
        except asyncio.CancelledError:
            raise

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _inject_hero_image(ui_schema_dict: dict, image_data_url: str) -> None:
    """
    When image search found a match but the LLM didn't include any Image component,
    inject a hero Image so the frontend can show it as the sidebar background.
    """
    hero_id = "hero-image"
    components = ui_schema_dict.get("components", [])
    root_id = ui_schema_dict.get("root")
    if not root_id:
        logger.warning("[IMAGE SEARCH] Cannot inject hero: no root in schema")
        return
    # Add the hero Image component
    components.append({
        "id": hero_id,
        "component": {
            "Image": {
                "url": {"literalString": image_data_url},
                "usageHint": "hero",
            }
        },
    })
    # Prepend hero to root's children so it's first (sidebar uses first hero for background)
    for comp in components:
        if comp.get("id") != root_id:
            continue
        comp_def = comp.get("component", {})
        for key in ("Column", "Row"):
            if key not in comp_def:
                continue
            children = comp_def[key].get("children")
            if isinstance(children, dict) and "explicitList" in children:
                children["explicitList"].insert(0, hero_id)
                logger.info(f"[IMAGE SEARCH] Injected hero image into root {root_id!r}")
                return
            if isinstance(children, list):
                comp_def[key]["children"] = {"explicitList": [hero_id] + children}
                logger.info(f"[IMAGE SEARCH] Injected hero image into root {root_id!r}")
                return
        break
    else:
        logger.warning(f"[IMAGE SEARCH] Cannot inject hero: root component {root_id!r} not found or has no children")


def _truncate_schema_body_text(ui_schema_dict: dict, max_chars: int = 200) -> None:
    """
    Truncate Text components with usageHint 'body' to at most ~2 lines (max_chars).
    Modifies ui_schema_dict in place.
    """
    for component in ui_schema_dict.get("components", []):
        comp_def = component.get("component", {})
        if "Text" not in comp_def:
            continue
        text_props = comp_def["Text"]
        if text_props.get("usageHint") != "body":
            continue
        text_value = text_props.get("text")
        if not isinstance(text_value, dict) or "literalString" not in text_value:
            continue
        s = text_value["literalString"]
        if not isinstance(s, str) or len(s) <= max_chars:
            continue
        lines = s.strip().splitlines()
        two_lines = "\n".join(lines[:2]).strip()
        if len(two_lines) > max_chars:
            two_lines = two_lines[: max_chars - 3].rstrip() + "..."
        text_value["literalString"] = two_lines


def _get_literal_str(val, max_len: int = 60) -> str:
    """Extract literal string from text value (str or dict with literalString); truncate for display."""
    if isinstance(val, str):
        s = val
    elif isinstance(val, dict) and "literalString" in val:
        s = str(val["literalString"])
    else:
        return ""
    return (s[:max_len] + "…") if len(s) > max_len else s


def _ui_schema_summary_for_log(ui_schema_dict: dict) -> str:
    """Return a short, human-readable summary of the UI schema (intent + components + content)."""
    lines = []
    meta = ui_schema_dict.get("meta") or {}
    intent = meta.get("intent", "—")
    root = ui_schema_dict.get("root", "—")
    lines.append(f"intent: {intent}  |  root: {root}")
    lines.append("")
    for comp in ui_schema_dict.get("components", []):
        cid = comp.get("id", "?")
        comp_def = comp.get("component", {})
        if not comp_def:
            lines.append(f"  • {cid}: (empty)")
            continue
        # Single key is the type (Card, Text, Image, Column, Row, Button, ...)
        comp_type = next(iter(comp_def.keys()), "?")
        props = comp_def.get(comp_type, {})
        if comp_type == "Text":
            text_val = props.get("text", "")
            usage = props.get("usageHint", "")
            content = _get_literal_str(text_val)
            lines.append(f"  • {cid} (Text {usage}): \"{content}\"")
        elif comp_type == "Image":
            lines.append(f"  • {cid} (Image): [Image]")
        elif comp_type == "Card":
            child = props.get("child", "—")
            lines.append(f"  • {cid} (Card): child → {child}")
        elif comp_type in ("Column", "Row"):
            children = props.get("children", {})
            if isinstance(children, dict) and "explicitList" in children:
                ids = children["explicitList"]
            elif isinstance(children, list):
                ids = children
            else:
                ids = []
            lines.append(f"  • {cid} ({comp_type}): children → {ids}")
        elif comp_type == "Button":
            child = props.get("child", "—")
            lines.append(f"  • {cid} (Button): child → {child}")
        elif comp_type == "List":
            children = props.get("children", {})
            if isinstance(children, dict) and "explicitList" in children:
                ids = children["explicitList"]
            else:
                ids = []
            lines.append(f"  • {cid} (List): {ids}")
        elif comp_type == "StepCarousel":
            steps = props.get("steps", [])
            lines.append(f"  • {cid} (StepCarousel): steps → {steps}")
        else:
            lines.append(f"  • {cid} ({comp_type})")
    return "\n".join(lines)


def _schema_for_logging(ui_schema_dict: dict) -> dict:
    """Return a copy of the schema with image data replaced by [Image: id] for shorter logs."""
    import copy
    d = copy.deepcopy(ui_schema_dict)
    for comp in d.get("components", []):
        cid = comp.get("id", "?")
        comp_def = comp.get("component", {})
        if "Image" not in comp_def:
            continue
        img = comp_def["Image"]
        for key in ("url", "imageUrl"):
            if key not in img:
                continue
            val = img[key]
            if isinstance(val, dict) and "literalString" in val:
                s = val["literalString"]
                if s and (str(s).startswith("data:image") or len(str(s)) > 200):
                    img[key] = {"literalString": f"[Image: {cid}]"}
            elif isinstance(val, str) and (val.startswith("data:image") or len(val) > 200):
                img[key] = f"[Image: {cid}]"
    return d


def _is_placeholder_image_url(url_value) -> bool:
    """Return True if url_value is a placeholder URL (to be replaced from library)."""
    if not isinstance(url_value, dict) or "literalString" not in url_value:
        return False
    url_str = url_value["literalString"]
    return (
        any(p in url_str for p in ["example.com", "youtube.com", "placeholder", "VIDEO_FRAME_PLACEHOLDER", "imgur.com"])
        or url_str.startswith("http://")
        or url_str.startswith("https://")
    )


def _remove_placeholder_images(ui_schema_dict: dict) -> None:
    """
    When no image is available from the local library, remove Image components
    that have placeholder URLs and update parent children lists so the UI
    does not show a broken/placeholder hero.
    """
    components = ui_schema_dict.get("components", [])
    removed_ids = set()
    for comp in components:
        comp_def = comp.get("component", {})
        if "Image" not in comp_def:
            continue
        url_value = comp_def["Image"].get("url")
        if _is_placeholder_image_url(url_value):
            removed_ids.add(comp.get("id"))
    if not removed_ids:
        return
    # Remove those components from the list
    ui_schema_dict["components"] = [c for c in components if c.get("id") not in removed_ids]
    # Remove their IDs from any parent's children.explicitList
    for comp in ui_schema_dict["components"]:
        comp_def = comp.get("component", {})
        for key in ("Column", "Row"):
            if key not in comp_def:
                continue
            children = comp_def[key].get("children", {})
            explicit_list = children.get("explicitList", [])
            if not explicit_list:
                continue
            new_list = [cid for cid in explicit_list if cid not in removed_ids]
            if new_list != explicit_list:
                children["explicitList"] = new_list
                logger.info(f"Removed placeholder image refs from {comp.get('id')}: {removed_ids & set(explicit_list)}")
    logger.info(f"No library image found; removed placeholder Image components: {removed_ids}")


def _extract_answer_context(ui_schema_dict: dict) -> str:
    """
    Extract text content from UI schema to use as answer context for image search.
    
    Args:
        ui_schema_dict: The UI schema dictionary
    
    Returns:
        Concatenated text content from all Text components
    """
    text_parts = []
    
    def extract_text_from_component(component: dict):
        """Recursively extract text from components"""
        comp_def = component.get("component", {})
        
        # Extract text from Text components
        if "Text" in comp_def:
            text_props = comp_def["Text"]
            text_value = text_props.get("text", {})
            if isinstance(text_value, dict) and "literalString" in text_value:
                text_parts.append(text_value["literalString"])
        
        # Recursively check child components
        if "Card" in comp_def:
            child_id = comp_def["Card"].get("child")
            if child_id:
                child_comp = next(
                    (c for c in ui_schema_dict.get("components", []) if c.get("id") == child_id),
                    None
                )
                if child_comp:
                    extract_text_from_component(child_comp)
        
        if "Column" in comp_def or "Row" in comp_def:
            children = comp_def.get("Column", comp_def.get("Row", {})).get("children", {})
            child_ids = children.get("explicitList", [])
            for child_id in child_ids:
                child_comp = next(
                    (c for c in ui_schema_dict.get("components", []) if c.get("id") == child_id),
                    None
                )
                if child_comp:
                    extract_text_from_component(child_comp)
    
    # Start from root component
    root_id = ui_schema_dict.get("root")
    if root_id:
        root_comp = next(
            (c for c in ui_schema_dict.get("components", []) if c.get("id") == root_id),
            None
        )
        if root_comp:
            extract_text_from_component(root_comp)
    
    # If no text found, extract from all components
    if not text_parts:
        for component in ui_schema_dict.get("components", []):
            extract_text_from_component(component)
    
    return " ".join(text_parts) if text_parts else "No text content found"


class RefineSpeechRequest(BaseModel):
    """Request model for /refine-speech endpoint"""
    raw_speech: str


class RefineSpeechResponse(BaseModel):
    """Response model for /refine-speech endpoint"""
    refined_question: str


@router.post("/refine-speech", response_model=RefineSpeechResponse)
async def refine_speech(request: RefineSpeechRequest):
    """
    Refine and clean up raw speech input.
    Removes mumbling, filler words, and reframes the question to be clearer.
    """
    try:
        gemini_service = get_gemini_service()
        
        prompt = f"""You are a speech-to-text refinement assistant. Your task is to clean up and refine raw speech input that may contain:
- Filler words (um, uh, like, you know)
- Mumbling or unclear words
- Repetitions
- Incomplete thoughts
- Casual speech patterns

Raw speech input: "{request.raw_speech}"

Please:
1. Remove filler words and mumbling
2. Fix any unclear words based on context
3. Complete incomplete thoughts if possible
4. Reframe as a clear, concise question
5. Keep the original intent and meaning

Return ONLY the refined question, nothing else. Do not add explanations or markdown."""

        refined = await gemini_service.generate_text(prompt)
        
        # Clean up the response (remove quotes, extra whitespace)
        refined_question = refined.strip().strip('"').strip("'")
        
        logger.info(f"Refined speech: '{request.raw_speech}' -> '{refined_question}'")
        
        return RefineSpeechResponse(refined_question=refined_question)
        
    except Exception as e:
        logger.error(f"Error refining speech: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to refine speech: {str(e)}")


class SpeechToTextRequest(BaseModel):
    """Request model for /speech-to-text endpoint"""
    audio_data: str  # Base64-encoded audio data
    language_code: Optional[str] = "en-US"
    audio_format: Optional[str] = "webm_opus"  # webm_opus, linear16, or flac


class SpeechToTextResponse(BaseModel):
    """Response model for /speech-to-text endpoint"""
    transcript: str


@router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(request: SpeechToTextRequest):
    """
    Convert speech audio to text using Google Cloud Speech-to-Text API.
    """
    try:
        logger.info(f"Received speech-to-text request: language={request.language_code}, format={request.audio_format}, audio_data_length={len(request.audio_data)}")
        
        # Log audio data info (first 100 chars for debugging)
        logger.info(f"Audio data preview: {request.audio_data[:100]}...")
        
        speech_service = get_speech_service()
        logger.info("Speech service initialized successfully")
        
        transcript = speech_service.transcribe_base64_audio(
            request.audio_data,
            request.language_code,
            request.audio_format
        )
        
        logger.info(f"Transcribed audio: '{transcript}'")
        
        return SpeechToTextResponse(transcript=transcript)
        
    except Exception as e:
        logger.error(f"Error transcribing speech: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Traceback: {error_traceback}")
        # Include more details in the error response for debugging
        error_detail = f"Failed to transcribe speech: {str(e)}"
        if "credentials" in str(e).lower() or "authentication" in str(e).lower():
            error_detail += " (Check GOOGLE_APPLICATION_CREDENTIALS or GEMINI_API_KEY in .env)"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/test-speech-api")
async def test_speech_api():
    """Test if speech API key is working"""
    import os
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY not found in .env", "status": "missing_key"}
    
    try:
        import requests
        # Simple test - just check if we can make a request (will fail but show if API key format is valid)
        url = f"https://speech.googleapis.com/v1/speech:recognize?key={api_key}"
        # Make a minimal test request
        test_payload = {
            "config": {
                "encoding": "WEBM_OPUS",
                "languageCode": "en-US"
            },
            "audio": {
                "content": "dGVzdA=="  # base64 for "test" - minimal test
            }
        }
        response = requests.post(url, json=test_payload, timeout=10)
        
        # Even if it fails, we can see the response
        return {
            "status": "api_key_found",
            "api_key_length": len(api_key),
            "api_key_preview": api_key[:10] + "..." if len(api_key) > 10 else api_key,
            "response_status": response.status_code,
            "response_text": response.text[:200] if hasattr(response, 'text') else str(response)
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "request_error",
            "error": str(e),
            "api_key_found": True,
            "api_key_length": len(api_key) if api_key else 0
        }
    except ImportError:
        return {"error": "requests library not installed. Run: pip install requests", "status": "missing_library"}
    except Exception as e:
        return {"error": str(e), "status": "unknown_error", "api_key_found": api_key is not None}
