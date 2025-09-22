"""
Profile Tool - getting and managing user profile.
Manages user profile information and preferences.
"""

import logging
import json
from typing import Type, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from ..memory.memory_manager import MemoryManager


class ProfileInput(BaseModel):
    """Input schema for profile tool."""
    action: str = Field(
        description="Action to perform: 'get' (retrieve profile), 'update' (modify profile), or 'summary' (get profile summary)"
    )
    key: Optional[str] = Field(
        default=None,
        description="Profile key to update (required for 'update' action)"
    )
    value: Optional[str] = Field(
        default=None,
        description="New value for the profile key (required for 'update' action)"
    )


class ProfileTool(BaseTool):
    """
    Tool for managing user profile information.
    Stores and retrieves user preferences, personal information, and settings.
    """

    name: str = "profile_tool"
    description: str = (
        "Update and manage user profile information. Use this tool when the user shares personal information "
        "such as their name, location, profession, age, or other personal details. "
        "Actions: 'get' to retrieve profile, 'update' to add/update information, 'summary' to get overview. "
        "Example: If user says 'I live in Moscow', use action='update', key='city', value='Moscow'."
    )
    args_schema: Type[BaseModel] = ProfileInput
    memory_manager: Optional[MemoryManager] = None

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        """
        Initialize profile tool.

        Args:
            memory_manager: Memory manager instance
        """
        super().__init__()
        if memory_manager is None:
            raise ValueError("memory_manager is required for ProfileTool")
        self.memory_manager = memory_manager

    def _run(self, action: str, key: Optional[str] = None, value: Optional[str] = None) -> str:
        """
        Execute profile operation.

        Args:
            action: Action to perform
            key: Profile key (for update)
            value: New value (for update)

        Returns:
            Result of the operation
        """
        try:
            if self.memory_manager is None:
                return "Memory manager not available"

            if action == "get":
                return self._get_full_profile()
            elif action == "update":
                return self._update_profile(key, value)
            elif action == "summary":
                return self._get_profile_summary()
            else:
                return f"Invalid action '{action}'. Use 'get', 'update', or 'summary'."

        except Exception as e:
            logging.error(f"Profile tool failed: {e}")
            return f"Error accessing profile: {str(e)}"

    def _get_full_profile(self) -> str:
        """Get complete user profile."""
        profile = self.memory_manager.get_user_profile()

        if not profile:
            return "👤 User profile is empty. Use the update action to add information."

        formatted_profile = ["👤 User Profile:"]
        formatted_profile.append("=" * 30)

        for key, value in profile.items():
            # Format key nicely
            display_key = key.replace("_", " ").title()

            # Handle different value types
            if isinstance(value, dict):
                display_value = json.dumps(value, indent=2)
            elif isinstance(value, list):
                display_value = ", ".join(str(item) for item in value)
            else:
                display_value = str(value)

            formatted_profile.append(f"{display_key}: {display_value}")

        formatted_profile.append("=" * 30)
        formatted_profile.append(f"Total fields: {len(profile)}")

        return "\\n".join(formatted_profile)

    def _update_profile(self, key: Optional[str], value: Optional[str]) -> str:
        """Update profile field."""
        if not key:
            return "Key is required for profile update. Specify which field to update."

        if value is None:
            return f"Value is required for updating profile field '{key}'."

        # Try to parse value as JSON if it looks like structured data
        parsed_value = value
        if value.startswith(("{", "[")) or value.lower() in ("true", "false", "null"):
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                # Keep as string if JSON parsing fails
                pass
        elif value.isdigit():
            parsed_value = int(value)
        elif value.replace(".", "").isdigit():
            try:
                parsed_value = float(value)
            except ValueError:
                pass

        # Update profile
        success = self.memory_manager.update_user_profile(key, parsed_value)

        if success:
            return f"✅ Profile updated: {key} = {parsed_value}"
        else:
            return f"❌ Failed to update profile field '{key}'"

    def _get_profile_summary(self) -> str:
        """Get profile summary."""
        profile = self.memory_manager.get_user_profile()

        if not profile:
            return "👤 No profile information available."

        summary_lines = ["👤 Profile Summary:"]

        # Count different types of information
        personal_info = 0
        preferences = 0
        settings = 0
        other = 0

        personal_keys = ["name", "age", "location", "occupation", "email", "phone"]
        preference_keys = ["language", "timezone", "theme", "notifications"]
        setting_keys = ["privacy", "security", "api_key", "config"]

        for key in profile.keys():
            key_lower = key.lower()
            if any(pk in key_lower for pk in personal_keys):
                personal_info += 1
            elif any(pk in key_lower for pk in preference_keys):
                preferences += 1
            elif any(sk in key_lower for sk in setting_keys):
                settings += 1
            else:
                other += 1

        summary_lines.append(f"📋 Total fields: {len(profile)}")
        if personal_info > 0:
            summary_lines.append(f"👤 Personal info: {personal_info} fields")
        if preferences > 0:
            summary_lines.append(f"⚙️ Preferences: {preferences} fields")
        if settings > 0:
            summary_lines.append(f"🔧 Settings: {settings} fields")
        if other > 0:
            summary_lines.append(f"📝 Other: {other} fields")

        # Show some key fields if available
        key_fields = []
        for key in ["name", "language", "timezone", "location"]:
            if key in profile:
                key_fields.append(f"{key}: {profile[key]}")

        if key_fields:
            summary_lines.append("")
            summary_lines.append("🔑 Key information:")
            summary_lines.extend(f"  • {field}" for field in key_fields)

        return "\\n".join(summary_lines)

    async def _arun(self, action: str, key: Optional[str] = None, value: Optional[str] = None) -> str:
        """Async version of profile tool."""
        return self._run(action, key, value)