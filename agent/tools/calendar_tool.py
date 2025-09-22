"""
Calendar tool for calendar management and scheduling.
"""

import os
import datetime
import json
import logging
from typing import Optional, Dict, Any
from langchain_core.tools import Tool, StructuredTool
from pydantic import BaseModel, Field


class CalendarInput(BaseModel):
    """Input schema for calendar tool."""
    command: str = Field(description="Calendar command (create:title:description:start:end:location, list, search:text, get:id, update:id:title:description, delete:id)")


class CreateEventInput(BaseModel):
    """Input schema for create event."""
    title: str = Field(description="Event title")
    description: str = Field(description="Event description")
    start_time: str = Field(description="Event start time (YYYY-MM-DD HH:MM)")
    end_time: str = Field(description="Event end time (YYYY-MM-DD HH:MM)")
    location: str = Field(description="Event location")


class SearchEventInput(BaseModel):
    """Input schema for search event."""
    text: str = Field(description="Search text")


class GetEventInput(BaseModel):
    """Input schema for get event."""
    id: str = Field(description="Event ID")


class UpdateEventInput(BaseModel):
    """Input schema for update event."""
    id: str = Field(description="Event ID")
    title: str = Field(description="Event title")
    description: str = Field(description="Event description")
    start_time: str = Field(description="Event start time (YYYY-MM-DD HH:MM)")
    end_time: str = Field(description="Event end time (YYYY-MM-DD HH:MM)")
    location: str = Field(description="Event location")


class DeleteEventInput(BaseModel):
    """Input schema for delete event."""
    id: str = Field(description="Event ID")


class CalendarTool:
    """Calendar management tool for events and scheduling."""

    def __init__(self):
        """Initialize calendar tool."""
        self.name = "calendar"
        self.description = (
            "Manage calendar events and appointments. "
            "Commands: "
            "'create:title|description|start|end|location' - create new event, "
            "'list' - list all events, "
            "'search:text' - search events by text, "
            "'get:id' - get event by ID, "
            "'update:id:title|description|start|end|location' - update event, "
            "'delete:id' - delete event."
        )
        self.events: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
        # File-based persistence
        self.storage_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "calendar_events.json")
        self._ensure_storage_dir()
        self._load_events()

    def _ensure_storage_dir(self):
        """Ensure the storage directory exists."""
        try:
            storage_dir = os.path.dirname(self.storage_path)
            os.makedirs(storage_dir, exist_ok=True)
        except Exception as e:
            logging.getLogger(__name__).warning(f"CalendarTool: could not create storage directory: {e}")

    def _load_events(self):
        """Load events from the storage file if present."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.events = data.get("events", {})
                    self.next_id = int(data.get("next_id", 1))
        except Exception as e:
            logging.getLogger(__name__).warning(f"CalendarTool: failed to load events: {e}")

    def _save_events(self):
        """Persist events to the storage file."""
        try:
            payload = {"events": self.events, "next_id": self.next_id}
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.getLogger(__name__).warning(f"CalendarTool: failed to save events: {e}")

    def _parse_datetime(self, date_str: str) -> Optional[datetime.datetime]:
        """Parse datetime string."""
        try:
            # Try YYYY-MM-DD HH:MM format first
            return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                # Try YYYY-MM-DD format
                return datetime.datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                try:
                    # Try MM/DD/YYYY HH:MM format
                    return datetime.datetime.strptime(date_str, "%m/%d/%Y %H:%M")
                except ValueError:
                    try:
                        # Try DD-MM-YYYY HH:MM format
                        return datetime.datetime.strptime(date_str, "%d-%m-%Y %H:%M")
                    except ValueError:
                        return None

    def _format_datetime(self, dt: datetime.datetime) -> str:
        """Format datetime for display."""
        return dt.strftime("%Y-%m-%d %H:%M")

    def create_event(self, params: str) -> str:
        """Create a new calendar event."""
        try:
            parts = params.split("|")
            if len(parts) < 4:
                return "❌ Error: create command requires title, description, start time, end time"

            title = parts[0]
            description = parts[1] if len(parts) > 1 else ""
            start_time = parts[2]
            end_time = parts[3]
            location = parts[4] if len(parts) > 4 else ""

            # Parse times
            start_dt = self._parse_datetime(start_time)
            end_dt = self._parse_datetime(end_time)

            if not start_dt or not end_dt:
                return "❌ Error: Invalid date format. Use YYYY-MM-DD HH:MM"

            if start_dt >= end_dt:
                return "❌ Error: End time must be after start time"

            # Create event
            event_id = str(self.next_id)
            self.next_id += 1

            event = {
                "id": event_id,
                "title": title,
                "description": description,
                "start_time": self._format_datetime(start_dt),
                "end_time": self._format_datetime(end_dt),
                "location": location,
                "created_at": self._format_datetime(datetime.datetime.now())
            }

            self.events[event_id] = event
            self._save_events()
            return f"✅ Event created: {title} (ID: {event_id})"

        except Exception as e:
            return f"❌ Error creating event: {str(e)}"

    def list_events(self) -> str:
        """List all calendar events."""
        if not self.events:
            return "📅 No events found"

        result = ["📅 Calendar Events:"]
        result.append("=" * 40)

        for event in sorted(self.events.values(), key=lambda x: x["start_time"]):
            result.append(f"[{event['id']}] {event['title']}")
            result.append(f"   📅 {event['start_time']} - {event['end_time']}")
            if event['description']:
                result.append(f"   📝 {event['description']}")
            if event['location']:
                result.append(f"   📍 {event['location']}")
            result.append("")

        return "\n".join(result)

    def search_events(self, search_text: str) -> str:
        """Search events by text."""
        if not search_text:
            return "❌ Error: search command requires text"

        matches = []
        for event in self.events.values():
            search_fields = [
                event.get("title", ""),
                event.get("description", ""),
                event.get("location", "")
            ]

            if any(search_text.lower() in field.lower() for field in search_fields):
                matches.append(event)

        if not matches:
            return f"🔍 No events found containing '{search_text}'"

        result = [f"🔍 Search results for '{search_text}':"]
        result.append("=" * 40)

        for event in matches:
            result.append(f"[{event['id']}] {event['title']}")
            result.append(f"   📅 {event['start_time']} - {event['end_time']}")
            if event['description']:
                result.append(f"   📝 {event['description']}")
            result.append("")

        return "\n".join(result)

    def get_event(self, event_id: str) -> str:
        """Get specific event by ID."""
        if not event_id:
            return "❌ Error: get command requires event ID"

        event = self.events.get(event_id)
        if not event:
            return f"❌ Event with ID '{event_id}' not found"

        result = [
            f"📅 Event Details (ID: {event['id']}):",
            "=" * 40,
            f"📝 Title: {event['title']}",
            f"📅 Start: {event['start_time']}",
            f"📅 End: {event['end_time']}",
            f"📍 Location: {event['location'] or 'Not specified'}",
            f"📝 Description: {event['description'] or 'No description'}",
            f"📅 Created: {event['created_at']}"
        ]

        return "\n".join(result)

    def update_event(self, params: str) -> str:
        """Update an existing event."""
        try:
            # Split by | but handle the ID separately
            parts = params.split("|", 5)  # Split into maximum 6 parts
            if len(parts) < 2:
                return "❌ Error: update command requires ID and at least one field"

            event_id = parts[0]
            print(f"DEBUG: event_id = '{event_id}', params = '{params}'")

            # The remaining parts might contain | in the title, so join them back
            remaining = "|".join(parts[1:]) if len(parts) > 1 else ""
            if not remaining:
                return "❌ Error: update command requires at least one field to update"

            event = self.events.get(event_id)
            if not event:
                return f"❌ Event with ID '{event_id}' not found"

            # For now, just update title and description
            update_parts = remaining.split("|", 1)
            title = update_parts[0] if update_parts[0] else None
            description = update_parts[1] if len(update_parts) > 1 else None

            # Update fields
            if title:
                event["title"] = title
            if description:
                event["description"] = description

            self._save_events()
            return f"✅ Event updated: {event['title']} (ID: {event_id})"

        except Exception as e:
            return f"❌ Error updating event: {str(e)}"

    def delete_event(self, event_id: str) -> str:
        """Delete an event."""
        if not event_id:
            return "❌ Error: delete command requires event ID"

        event = self.events.pop(event_id, None)
        if not event:
            return f"❌ Event with ID '{event_id}' not found"
        self._save_events()
        return f"✅ Event deleted: {event['title']}"

    def get_calendar_info(self, command: str) -> str:
        """
        Execute calendar command.

        Args:
            command: Calendar command string

        Returns:
            Result of calendar operation
        """
        try:
            if not command:
                return "❌ Error: Empty command"

            command = command.strip()

            if command == "list":
                return self.list_events()

            elif command.startswith("create:"):
                params = command[7:]  # Remove "create:"
                return self.create_event(params)

            elif command.startswith("update:"):
                params = command[7:]  # Remove "update:"
                # Support both colon and pipe separators after the ID
                # Expected: update:<id>:<title>|<description>|<start>|<end>|<location>
                # Normalize to: <id>|<title>|<description>|...
                if ":" in params:
                    event_id, rest = params.split(":", 1)
                    params = f"{event_id}|{rest}"
                return self.update_event(params)

            elif command.startswith("search:"):
                search_text = command[7:]  # Remove "search:"
                return self.search_events(search_text)

            elif command.startswith("get:"):
                event_id = command[4:]  # Remove "get:"
                return self.get_event(event_id)

            elif command.startswith("delete:"):
                event_id = command[7:]  # Remove "delete:"
                return self.delete_event(event_id)

            else:
                return (
                    "Available calendar commands:\n"
                    "- list - show all events\n"
                    "- create:title|description|start|end|location - create event\n"
                    "- search:text - search events by text\n"
                    "- get:id - get event details\n"
                    "- update:id:title|description|start|end|location - update event\n"
                    "- delete:id - delete event\n\n"
                    "Date format: YYYY-MM-DD HH:MM"
                )

        except Exception as e:
            return f"❌ Error executing calendar command: {str(e)}"

    # ---------------- StructuredTool input schemas -----------------

    class CreateEventInput(BaseModel):
        title: str = Field(description="Event title")
        description: Optional[str] = Field(default="", description="Event description")
        start_time: str = Field(description="Start time in 'YYYY-MM-DD HH:MM' (24h)")
        end_time: str = Field(description="End time in 'YYYY-MM-DD HH:MM' (24h)")
        location: Optional[str] = Field(default="", description="Event location")

    class ListEventsInput(BaseModel):
        date: Optional[str] = Field(default=None, description="Specific date 'YYYY-MM-DD'")
        start_date: Optional[str] = Field(default=None, description="Start date 'YYYY-MM-DD'")
        end_date: Optional[str] = Field(default=None, description="End date 'YYYY-MM-DD'")

    class SearchEventsInput(BaseModel):
        search_text: str = Field(description="Text to search for in events")

    class GetEventInput(BaseModel):
        event_id: str = Field(description="Event ID")

    class UpdateEventInput(BaseModel):
        event_id: str = Field(description="Event ID")
        title: Optional[str] = Field(default=None, description="New title")
        description: Optional[str] = Field(default=None, description="New description")
        start_time: Optional[str] = Field(default=None, description="New start time 'YYYY-MM-DD HH:MM'")
        end_time: Optional[str] = Field(default=None, description="New end time 'YYYY-MM-DD HH:MM'")
        location: Optional[str] = Field(default=None, description="New location")

    class DeleteEventInput(BaseModel):
        event_id: str = Field(description="Event ID")

    # ---------------- StructuredTool function wrappers --------------

    def st_create_event(self, title: str, description: Optional[str], start_time: str, end_time: str, location: Optional[str]) -> str:
        """Structured create event wrapper for the agent."""
        # Use direct logic (avoid parsing string params)
        start_dt = self._parse_datetime(start_time)
        end_dt = self._parse_datetime(end_time)
        if not start_dt or not end_dt:
            return "❌ Error: Invalid date format. Use YYYY-MM-DD HH:MM"
        if start_dt >= end_dt:
            return "❌ Error: End time must be after start time"

        event_id = str(self.next_id)
        self.next_id += 1

        event = {
            "id": event_id,
            "title": title,
            "description": description or "",
            "start_time": self._format_datetime(start_dt),
            "end_time": self._format_datetime(end_dt),
            "location": location or "",
            "created_at": self._format_datetime(datetime.datetime.now())
        }
        self.events[event_id] = event
        self._save_events()
        return f"✅ Event created: {title} (ID: {event_id})"

    def st_list_events(self, date: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        # Reuse existing list logic by filtering here
        events = list(self.events.values())
        if date:
            events = [e for e in events if e["start_time"].startswith(date)]
        if start_date and end_date:
            try:
                start_dt = datetime.datetime.strptime(start_date + " 00:00", "%Y-%m-%d %H:%M")
                end_dt = datetime.datetime.strptime(end_date + " 23:59", "%Y-%m-%d %H:%M")
                events = [e for e in events if start_dt <= datetime.datetime.strptime(e["start_time"], "%Y-%m-%d %H:%M") <= end_dt]
            except ValueError:
                return "❌ Invalid date format. Use YYYY-MM-DD"
        if not events:
            return "📅 No events found"
        events.sort(key=lambda x: x["start_time"])
        out = ["📅 Calendar Events:", "=" * 40]
        for e in events:
            out.append(f"[{e['id']}] {e['title']}")
            out.append(f"   📅 {e['start_time']} - {e['end_time']}")
            if e.get('description'):
                out.append(f"   📝 {e['description']}")
            if e.get('location'):
                out.append(f"   📍 {e['location']}")
            out.append("")
        return "\n".join(out)

    def st_search_events(self, search_text: str) -> str:
        return self.search_events(search_text)

    def st_get_event(self, event_id: str) -> str:
        return self.get_event(event_id)

    def st_update_event(self, event_id: str, title: Optional[str] = None, description: Optional[str] = None, start_time: Optional[str] = None, end_time: Optional[str] = None, location: Optional[str] = None) -> str:
        event = self.events.get(event_id)
        if not event:
            return f"❌ Event with ID '{event_id}' not found"
        if title:
            event["title"] = title
        if description:
            event["description"] = description
        if start_time:
            sdt = self._parse_datetime(start_time)
            if not sdt:
                return "❌ Error: Invalid start time format. Use YYYY-MM-DD HH:MM"
            event["start_time"] = self._format_datetime(sdt)
        if end_time:
            edt = self._parse_datetime(end_time)
            if not edt:
                return "❌ Error: Invalid end time format. Use YYYY-MM-DD HH:MM"
            event["end_time"] = self._format_datetime(edt)
        if start_time or end_time:
            sdt = self._parse_datetime(event["start_time"]) 
            edt = self._parse_datetime(event["end_time"]) 
            if sdt and edt and sdt >= edt:
                return "❌ Error: End time must be after start time"
        if location:
            event["location"] = location
        self._save_events()
        return f"✅ Event updated: {event['title']} (ID: {event_id})"

    def st_delete_event(self, event_id: str) -> str:
        ev = self.events.pop(event_id, None)
        if not ev:
            return f"❌ Event with ID '{event_id}' not found"
        self._save_events()
        return f"✅ Event deleted: {ev['title']}"

    def get_tools(self) -> list[StructuredTool]:
        """Return a list of StructuredTools for LangChain tool calling."""
        return [
            StructuredTool.from_function(
                func=self.st_create_event,
                name="calendar_create",
                description="Create a calendar event. Provide title, start_time (YYYY-MM-DD HH:MM), end_time (YYYY-MM-DD HH:MM), optional description and location.",
                args_schema=CalendarTool.CreateEventInput
            ),
            StructuredTool.from_function(
                func=self.st_list_events,
                name="calendar_list",
                description="List calendar events. Optionally filter by a date or a date range (start_date, end_date).",
                args_schema=CalendarTool.ListEventsInput
            ),
            StructuredTool.from_function(
                func=self.st_search_events,
                name="calendar_search",
                description="Search calendar events by text in title/description/location.",
                args_schema=CalendarTool.SearchEventsInput
            ),
            StructuredTool.from_function(
                func=self.st_get_event,
                name="calendar_get",
                description="Get event details by ID.",
                args_schema=CalendarTool.GetEventInput
            ),
            StructuredTool.from_function(
                func=self.st_update_event,
                name="calendar_update",
                description="Update an event's fields by ID. Any of title, description, start_time, end_time, location may be provided.",
                args_schema=CalendarTool.UpdateEventInput
            ),
            StructuredTool.from_function(
                func=self.st_delete_event,
                name="calendar_delete",
                description="Delete an event by ID.",
                args_schema=CalendarTool.DeleteEventInput
            ),
        ]

    def get_tool(self) -> StructuredTool:
        """Backward-compatible single command tool (still available)."""
        return StructuredTool.from_function(
            func=self.get_calendar_info,
            name=self.name,
            description=self.description,
            args_schema=CalendarInput
        )
