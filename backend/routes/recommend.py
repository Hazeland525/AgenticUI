"""
Recommendation endpoint: uses user profile, collections summary, and Maps MCP
to return a shortlist of places (e.g. restaurants) with evidence-based reasoning.
"""
import json
import logging
import time
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.user_profile_service import UserProfileService
from services.storage import StorageService
from services.maps_service import MapsService
from services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

router = APIRouter()

# Lazy singletons
_gemini: Optional[GeminiService] = None
_maps: Optional[MapsService] = None


def get_gemini() -> GeminiService:
    global _gemini
    if _gemini is None:
        _gemini = GeminiService()
    return _gemini


def get_maps() -> MapsService:
    global _maps
    if _maps is None:
        _maps = MapsService()
    return _maps


class RecommendRequest(BaseModel):
    message: str


class RecommendResponse(BaseModel):
    places: list[dict[str, Any]]
    reasoning: str
    verbalSummary: Optional[str] = None


def _get_title_from_schema(ui_schema: dict) -> Optional[str]:
    """Extract first h1 text from UI schema."""
    for comp in (ui_schema or {}).get("components", []):
        c = (comp or {}).get("component") or {}
        if "Text" not in c:
            continue
        text_props = c["Text"]
        if text_props.get("usageHint") != "h1":
            continue
        text_val = text_props.get("text")
        if isinstance(text_val, str):
            return text_val
        if isinstance(text_val, dict) and "literalString" in text_val:
            return text_val["literalString"]
    return None


def _truncate_to_max_words(text: str, max_words: int = 40) -> str:
    """Keep at most max_words; add ellipsis if truncated."""
    text = (text or "").strip()
    if not text:
        return text
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def _build_collections_summary(items: list[dict]) -> str:
    """Build a short summary of saved items for the LLM (question + title)."""
    lines = []
    for i, item in enumerate(items[:30], 1):
        q = item.get("question") or ""
        title = _get_title_from_schema(item.get("uiSchema") or {}) or q
        if q or title:
            lines.append(f"- {title}" if title else f"- Q: {q}")
    return "\n".join(lines) if lines else "(No saved items)"


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    """
    Recommend places (e.g. restaurants) using user profile, collections, and Maps MCP.
    Returns 3 places and a short reasoning line based on profile + collections evidence(max 40 words).
    """
    try:
        t_start = time.perf_counter()
        profile_svc = UserProfileService()
        profile = profile_svc.get_profile()
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")

        location = (profile.get("location") or {})
        lat = location.get("latitude")
        lng = location.get("longitude")
        city = profile.get("city") or location.get("address") or "the user's city"
        name = profile.get("name") or "User"
        profession = profile.get("profession") or ""

        storage = StorageService()
        items = await storage.get_all_items()
        collections_summary = _build_collections_summary(items)

        gemini = get_gemini()
        maps_svc = get_maps()

        # Step 1: Interpret user message -> search query (include location in query or use bias)
        t0 = time.perf_counter()
        interpret_prompt = f"""You are helping plan a recommendation. The user said: "{request.message}"

User profile: name={name}, city={city}, profession={profession}.
User's saved collections (topics they care about):
{collections_summary}

Output a JSON object with exactly this shape (no markdown, no extra text):
{{ "textQuery": "<search query for places, e.g. 'restaurants in San Francisco' or 'date night restaurants in San Francisco'>", "intent": "restaurant_recommendation" }}

Rules: textQuery MUST include location (city/region) so the search is specific. Use the user's city from profile. Keep textQuery concise, one short phrase."""

        raw_interpret = await gemini.generate_content(interpret_prompt)
        t_interpret = time.perf_counter() - t0
        logger.info(f"[TIMING] Collections/recommend — interpret (LLM): {t_interpret:.2f}s")
        try:
            cleaned = raw_interpret.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines)
            interpret = json.loads(cleaned)
            text_query = interpret.get("textQuery") or f"restaurants in {city}"
        except json.JSONDecodeError as e:
            logger.warning("Interpret JSON failed, using fallback query: %s", e)
            text_query = f"restaurants in {city}"

        # Step 2: Call Maps MCP
        t1 = time.perf_counter()
        places_raw = maps_svc.search_places(
            text_query,
            latitude=lat,
            longitude=lng,
            radius_meters=5000,
            page_size=10,
        )
        t_maps = time.perf_counter() - t1
        logger.info(f"[TIMING] Collections/recommend — maps search: {t_maps:.2f}s")

        if not places_raw:
            return RecommendResponse(
                places=[],
                reasoning=_truncate_to_max_words(
                    f"We couldn't find any places matching \"{text_query}\" near {city}. Try being more specific or a different area."
                ),
                verbalSummary=None,
            )

        # Step 3: LLM picks exactly 3 places and writes one short reasoning line
        places_for_prompt = [
            {"name": p.get("name"), "placeUrl": p.get("placeUrl"), "address": p.get("address")}
            for p in places_raw[:10]
        ]
        select_prompt = f"""You are choosing exactly 3 places to recommend. The user said: "{request.message}"

User profile: name={name}, city={city}, profession={profession}.
User's saved collections (preferences/interests):
{collections_summary}

Candidate places from a map search (index 0-based):
{json.dumps(places_for_prompt, indent=2)}

Write the reasoning in a friendly, conversational tone as if curating for the person. Address them as "you" (not "the user"). The reasoning MUST reference at least one of: their city ({city}), their name, or a specific topic from their saved collections (e.g. "your interest in vegetables", "what you saved about Italian food"). Maximum 40 words.
Do NOT give meta-explanations like "selections are made as...", "data were not detailed", or "chosen to fulfill the request". Do NOT say the data lacked detail.
Good example: "Here are three spots I picked for you in {city}, based on your interest in vegetables and your saved collections."
Bad example: "These selections are made as the specific cuisine and proximity were not detailed in the provided data."

Output a JSON object with exactly this shape (no markdown, no extra text):
{{ "selectedIndices": [0, 1, 2], "reasoning": "<one short sentence, max 40 words, conversational, addressing the reader as you>" }}"""

        t2 = time.perf_counter()
        raw_select = await gemini.generate_content(select_prompt)
        t_select = time.perf_counter() - t2
        logger.info(f"[TIMING] Collections/recommend — select places (LLM): {t_select:.2f}s")
        try:
            cleaned = raw_select.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines)
            select = json.loads(cleaned)
            indices = (select.get("selectedIndices") or [0, 1, 2])[:3]
            reasoning = select.get("reasoning") or f"Here are three spots I picked for you near {city}, based on your preferences."
        except json.JSONDecodeError as e:
            logger.warning("Select JSON failed, using first 3: %s", e)
            indices = list(range(min(3, len(places_raw))))
            reasoning = f"Here are three spots I picked for you near {city}."

        # Build response list from selected indices (max 3)
        selected = []
        for i in indices:
            if 0 <= i < len(places_raw):
                selected.append(places_raw[i])
            if len(selected) >= 3:
                break
        selected = selected[:3]
        if not selected:
            selected = places_raw[:3]

        # Enrich each place with detailed info (photos, ratings, price level)
        t3 = time.perf_counter()
        enriched = []
        for place in selected:
            place_id = place.get("placeId", "")
            if place_id:
                details = maps_svc.get_place_details(place_id)
                # Merge details into place object
                place["rating"] = details.get("rating")
                place["priceLevel"] = details.get("priceLevel", "")
                place["photoUri"] = details.get("photoUri")
                # Use displayName from details if available
                if details.get("displayName"):
                    place["name"] = details["displayName"]
                # Use formattedAddress from details if available
                if details.get("formattedAddress"):
                    place["address"] = details["formattedAddress"]
                # Use googleMapsUri from details if available
                if details.get("googleMapsUri"):
                    place["placeUrl"] = details["googleMapsUri"]
            enriched.append(place)
        t_enrich = time.perf_counter() - t3
        logger.info(f"[TIMING] Collections/recommend — enrich places (details): {t_enrich:.2f}s")

        reasoning_short = _truncate_to_max_words(reasoning.strip())
        # Generate short verbal summary for TTS on Collections page
        verbal_summary: Optional[str] = None
        if enriched and reasoning_short:
            try:
                place_names = ", ".join(p.get("name") or "Unknown" for p in enriched[:3])
                prompt = (
                    f"Context: Recommending to {name} in {city}. Their saved collections: {collections_summary[:400]}. "
                    f"Recommended places: {place_names}. Written reasoning: {reasoning_short[:300]}\n\n"
                    "Turn this into one short, conversational sentence for a voice-over. Address the listener as 'you' (e.g. 'I picked these for you...', 'based on your interest in...'). "
                    "Do not say 'the user'. No quotes or labels, just the spoken line."
                )
                t4 = time.perf_counter()
                verbal_summary = await gemini.generate_text(prompt)
                t_verbal = time.perf_counter() - t4
                logger.info(f"[TIMING] Collections/recommend — verbal_summary (LLM): {t_verbal:.2f}s")
                if verbal_summary:
                    verbal_summary = verbal_summary.strip()
                logger.info(f"[VERBAL ANSWER] Collections: {verbal_summary!r}")
            except Exception as e:
                logger.warning("Verbal summary for recommend failed: %s", e)
        t_total = time.perf_counter() - t_start
        logger.info(f"[TIMING] Collections/recommend — TOTAL (backend): {t_total:.2f}s")
        return RecommendResponse(
            places=enriched,
            reasoning=reasoning_short,
            verbalSummary=verbal_summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Recommend failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
