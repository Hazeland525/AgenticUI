"""
Maps service using Google Maps Grounding Lite MCP (search_places).
Calls https://mapstools.googleapis.com/mcp with JSON-RPC tools/call.
Uses API key authentication only (matching Gemini CLI pattern).
"""
import os
import logging
from typing import Any, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MCP_URL = "https://mapstools.googleapis.com/mcp"


class MapsService:
    """Call Grounding Lite MCP search_places and return normalized place list."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in .env")
        else:
            logger.info("Maps service initialized with API key")

    def search_places(
        self,
        text_query: str,
        *,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_meters: Optional[int] = 5000,
        language_code: str = "en",
        region_code: Optional[str] = None,
        page_size: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Call MCP search_places and return a list of places.
        Each place: { "name", "placeId", "placeUrl", "address", "location" }.
        """
        if not self.api_key:
            logger.error("No API key available for Maps MCP")
            return []

        arguments: dict[str, Any] = {
            "textQuery": text_query,
            "languageCode": language_code,
            "pageSize": page_size,
        }
        if region_code:
            arguments["regionCode"] = region_code
        if latitude is not None and longitude is not None:
            arguments["locationBias"] = {
                "circle": {
                    "center": {"latitude": latitude, "longitude": longitude},
                    "radiusMeters": radius_meters or 5000,
                }
            }

        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "search_places",
                "arguments": arguments,
            },
        }

        # Use API key only (matching Gemini CLI pattern that worked)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Goog-Api-Key": self.api_key,
        }
        
        logger.info(f"Calling Maps MCP with API key for query: {text_query}")

        try:
            resp = requests.post(MCP_URL, json=body, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.error("Maps MCP request failed: %s", e)
            if hasattr(e, "response") and e.response is not None:
                logger.error("Response body: %s", e.response.text[:500])
            return []
        except Exception as e:
            logger.error("Maps MCP error: %s", e)
            return []

        # MCP response: result.content[] often has type "text" with JSON string = SearchTextResponse
        # SearchTextResponse: { "places": [ PlaceView ], "summary": "...", "nextPageToken": "..." }
        result = data.get("result") or {}
        content = result.get("content")
        places_out: list[dict[str, Any]] = []

        if isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    continue
                # Part may be { "type": "text", "text": "{\"places\": [...], ...}" }
                if "text" in part:
                    try:
                        import json as _json
                        parsed = _json.loads(part["text"])
                        if "places" in parsed:
                            for p in parsed.get("places", []):
                                places_out.append(self._normalize_place(p))
                            break
                    except (_json.JSONDecodeError, TypeError):
                        pass
                if "places" in part:
                    for p in part.get("places", []):
                        places_out.append(self._normalize_place(p))
                    break
        elif isinstance(content, dict) and "text" in content:
            try:
                import json as _json
                parsed = _json.loads(content["text"])
                if "places" in parsed:
                    for p in parsed.get("places", []):
                        places_out.append(self._normalize_place(p))
            except (_json.JSONDecodeError, TypeError):
                pass

        if not places_out and isinstance(result, dict) and "places" in result:
            for p in result.get("places", []):
                places_out.append(self._normalize_place(p))

        return places_out[:10]

    def get_place_details(self, place_id: str) -> dict[str, Any]:
        """
        Fetch detailed place information from Places API (New).
        Returns: { "displayName", "formattedAddress", "rating", "priceLevel", 
                   "photoUri", "googleMapsUri" }
        """
        if not self.api_key:
            logger.error("No API key available for Places API")
            return {}
        
        if not place_id:
            return {}

        # Places API (New) endpoint
        url = f"https://places.googleapis.com/v1/places/{place_id}"
        
        # Request specific fields to minimize costs and response size
        params = {
            "fields": "id,displayName,formattedAddress,rating,priceLevel,photos,googleMapsUri"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
        }
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            # Extract photo URL from first photo if available
            photo_uri = None
            photos = data.get("photos", [])
            if photos and len(photos) > 0:
                photo_name = photos[0].get("name", "")
                if photo_name:
                    # Construct photo URL with max height
                    photo_uri = f"https://places.googleapis.com/v1/{photo_name}/media?maxHeightPx=400&key={self.api_key}"
            
            return {
                "displayName": data.get("displayName", {}).get("text", ""),
                "formattedAddress": data.get("formattedAddress", ""),
                "rating": data.get("rating"),
                "priceLevel": data.get("priceLevel", ""),
                "photoUri": photo_uri,
                "googleMapsUri": data.get("googleMapsUri", ""),
            }
        except requests.RequestException as e:
            logger.warning("Places API request failed for %s: %s", place_id, e)
            if hasattr(e, "response") and e.response is not None:
                logger.warning("Response: %s", e.response.text[:300])
            return {}
        except Exception as e:
            logger.warning("Places API error for %s: %s", place_id, e)
            return {}

    def _normalize_place(self, p: dict[str, Any]) -> dict[str, Any]:
        """Normalize MCP PlaceView (place, id, googleMapsLinks, location) to our shape."""
        place_id = p.get("id") or p.get("placeId") or ""
        raw_place = p.get("place") or ""
        name = (
            p.get("displayName")
            or p.get("name")
            or (raw_place.replace("places/", "", 1) if raw_place else place_id)
        )
        if not name:
            name = place_id or "Place"
        links = p.get("googleMapsLinks") or p.get("googleMapsLink") or {}
        if isinstance(links, dict):
            place_url = links.get("placeUrl") or links.get("url") or ""
        else:
            place_url = ""
        if not place_url and place_id:
            place_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
        location = p.get("location") or {}
        address = p.get("formattedAddress") or p.get("address") or ""
        return {
            "name": name,
            "placeId": place_id,
            "placeUrl": place_url,
            "address": address,
            "location": location,
        }
