import json
import os
from langchain_core.tools import tool



class MemoryModule:
    """
    Persistent memory storage for user profile.
    Distinct from conversation memory (which lives in the coordinator).
    """

    def __init__(self, path="data/user_profile.json"):
        self.path = path

        # State flags used by the Coordinator
        self.expecting_user_info = False
        self.expecting_task_description = False

        # Load or initialize profile
        self.profile = self._load()

    # --------------------------------------------------------------
    # INTERNAL METHODS
    # --------------------------------------------------------------

    def _load(self):
        """Load user profile if exists, otherwise return empty dict."""
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}


    def save(self):
        """Persist current profile to file."""
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.profile, f, indent=4, ensure_ascii=False)

    # --------------------------------------------------------------
    # PROFILE LOGIC
    # --------------------------------------------------------------

    def is_empty(self):
        """Check if user profile contains no information."""
        return self.profile == {} or len(self.profile.keys()) == 0

    @tool
    def update_profile(self, fields: dict):
        """
        Update known user profile fields.
        Only updates keys present in the dictionary.
        """
        for key, value in fields.items():
            if value is not None and value != "":
                self.profile[key] = value

    def get(self, key=None, default=None):
        if key is None:
            return self.profile
        return self.profile.get(key, default)

    # --------------------------------------------------------------
    # DEBUG / UTILS
    # --------------------------------------------------------------

    def clear(self):
        """Erase user profile and all flags (useful for development)."""
        self.profile = {}
        self.expecting_user_info = False
        self.expecting_task_description = False
        self.save()
