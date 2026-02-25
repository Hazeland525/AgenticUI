"""
Service to load the pseudo user profile from a JSON file.
"""
import json
import os
from typing import Any, Optional


class UserProfileService:
    """Loads and returns the single fake user profile."""

    def __init__(self):
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.profile_path = os.path.join(backend_dir, "data", "user_profile.json")

    def get_profile(self) -> Optional[dict[str, Any]]:
        """Load user profile from JSON. Returns None if file missing or invalid."""
        if not os.path.isfile(self.profile_path):
            return None
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
