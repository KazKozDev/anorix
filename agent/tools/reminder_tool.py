"""
Reminder tool for creating and managing reminders (напоминания).
Follows the same architecture as CalendarTool: structured tools + file persistence.
"""

import os
import json
import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


class ReminderTool:
    """Reminder management with structured LangChain tools and file persistence."""

    def __init__(self):
        self.name = "reminder"
        self.description = (
            "Manage reminders. Structured tools available: reminder_create, reminder_list, "
            "reminder_get, reminder_update, reminder_delete. Time format: 'YYYY-MM-DD HH:MM'."
        )
        self.reminders: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
        # Persistence file
        self.storage_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "reminders.json",
        )
        self._ensure_storage_dir()
        self._load()

    # ------------- Persistence -------------
    def _ensure_storage_dir(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

    def _load(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.reminders = data.get("reminders", {})
                    self.next_id = int(data.get("next_id", 1))
        except Exception:
            # On any failure keep empty in-memory state
            self.reminders = {}
            self.next_id = 1

    def _save(self):
        payload = {"reminders": self.reminders, "next_id": self.next_id}
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # ------------- Helpers -------------
    def _parse_dt(self, s: str) -> Optional[datetime.datetime]:
        if not s:
            return None
        fmts = ["%Y-%m-%d %H:%M", "%Y-%m-%d", "%d-%m-%Y %H:%M", "%m/%d/%Y %H:%M"]
        for fmt in fmts:
            try:
                return datetime.datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    def _fmt_dt(self, dt: datetime.datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M")

    # ------------- Schemas -------------
    class CreateInput(BaseModel):
        title: str = Field(description="Reminder title")
        due_time: str = Field(description="Due time in 'YYYY-MM-DD HH:MM'")
        description: Optional[str] = Field(default="", description="Reminder description")
        priority: Optional[str] = Field(default="normal", description="Priority: low|normal|high|urgent")

    class ListInput(BaseModel):
        date: Optional[str] = Field(default=None, description="Specific date 'YYYY-MM-DD'")
        start_date: Optional[str] = Field(default=None, description="Range start 'YYYY-MM-DD'")
        end_date: Optional[str] = Field(default=None, description="Range end 'YYYY-MM-DD'")
        status: Optional[str] = Field(default=None, description="Filter by status: pending|done")

    class GetInput(BaseModel):
        reminder_id: str = Field(description="Reminder ID")

    class UpdateInput(BaseModel):
        reminder_id: str = Field(description="Reminder ID")
        title: Optional[str] = Field(default=None)
        due_time: Optional[str] = Field(default=None)
        description: Optional[str] = Field(default=None)
        priority: Optional[str] = Field(default=None)
        status: Optional[str] = Field(default=None, description="pending|done")

    class DeleteInput(BaseModel):
        reminder_id: str = Field(description="Reminder ID")

    # ------------- Core ops -------------
    def st_create(self, title: str, due_time: str, description: Optional[str] = None, priority: Optional[str] = None) -> str:
        dt = self._parse_dt(due_time)
        if not dt:
            return "❌ Invalid due_time format. Use 'YYYY-MM-DD HH:MM'"
        rid = str(self.next_id)
        self.next_id += 1
        reminder = {
            "id": rid,
            "title": title,
            "description": description or "",
            "priority": (priority or "normal").lower(),
            "status": "pending",
            "due_time": self._fmt_dt(dt),
            "created_at": self._fmt_dt(datetime.datetime.now()),
        }
        self.reminders[rid] = reminder
        self._save()
        return f"✅ Reminder created: {title} (ID: {rid}) for {reminder['due_time']}"

    def st_list(
        self,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        items: List[Dict[str, Any]] = list(self.reminders.values())
        if status:
            items = [r for r in items if r.get("status", "pending") == status]
        if date:
            items = [r for r in items if r["due_time"].startswith(date)]
        if start_date and end_date:
            try:
                sd = datetime.datetime.strptime(start_date + " 00:00", "%Y-%m-%d %H:%M")
                ed = datetime.datetime.strptime(end_date + " 23:59", "%Y-%m-%d %H:%M")
                items = [r for r in items if sd <= datetime.datetime.strptime(r["due_time"], "%Y-%m-%d %H:%M") <= ed]
            except ValueError:
                return "❌ Invalid date format. Use YYYY-MM-DD"
        if not items:
            return "🔔 No reminders found"
        items.sort(key=lambda x: x["due_time"])
        out = ["🔔 Reminders:", "=" * 40]
        pr_emoji = {"low": "🟢", "normal": "🟡", "high": "🟠", "urgent": "🔴"}
        for r in items:
            out.append(f"{pr_emoji.get(r.get('priority','normal'),'⚪')} [{r['id']}] {r['title']} ({r['status']})")
            out.append(f"   ⏰ {r['due_time']}")
            if r.get("description"):
                out.append(f"   📝 {r['description']}")
            out.append("")
        return "\n".join(out)

    def st_get(self, reminder_id: str) -> str:
        r = self.reminders.get(reminder_id)
        if not r:
            return f"❌ Reminder '{reminder_id}' not found"
        pr_emoji = {"low": "🟢", "normal": "🟡", "high": "🟠", "urgent": "🔴"}
        return "\n".join([
            f"{pr_emoji.get(r.get('priority','normal'),'⚪')} [{r['id']}] {r['title']} ({r['status']})",
            f"⏰ Due: {r['due_time']}",
            f"📝 {r.get('description') or 'No description'}",
            f"⭐ Priority: {r.get('priority','normal')}",
            f"📅 Created: {r.get('created_at','')}",
        ])

    def st_update(
        self,
        reminder_id: str,
        title: Optional[str] = None,
        due_time: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        r = self.reminders.get(reminder_id)
        if not r:
            return f"❌ Reminder '{reminder_id}' not found"
        if title:
            r["title"] = title
        if description is not None:
            r["description"] = description
        if priority:
            r["priority"] = priority.lower()
        if status:
            r["status"] = status.lower()
        if due_time:
            dt = self._parse_dt(due_time)
            if not dt:
                return "❌ Invalid due_time format. Use 'YYYY-MM-DD HH:MM'"
            r["due_time"] = self._fmt_dt(dt)
        self._save()
        return f"✅ Reminder updated: {r['title']} (ID: {reminder_id})"

    def st_delete(self, reminder_id: str) -> str:
        r = self.reminders.pop(reminder_id, None)
        if not r:
            return f"❌ Reminder '{reminder_id}' not found"
        self._save()
        return f"✅ Reminder deleted: {r['title']}"

    # ------------- Structured tools -------------
    def get_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.st_create,
                name="reminder_create",
                description="Create a reminder (title, due_time 'YYYY-MM-DD HH:MM', optional description, priority).",
                args_schema=ReminderTool.CreateInput,
            ),
            StructuredTool.from_function(
                func=self.st_list,
                name="reminder_list",
                description="List reminders. Optional filters: date or (start_date & end_date), status.",
                args_schema=ReminderTool.ListInput,
            ),
            StructuredTool.from_function(
                func=self.st_get,
                name="reminder_get",
                description="Get reminder details by ID.",
                args_schema=ReminderTool.GetInput,
            ),
            StructuredTool.from_function(
                func=self.st_update,
                name="reminder_update",
                description="Update a reminder by ID (title, due_time, description, priority, status).",
                args_schema=ReminderTool.UpdateInput,
            ),
            StructuredTool.from_function(
                func=self.st_delete,
                name="reminder_delete",
                description="Delete a reminder by ID.",
                args_schema=ReminderTool.DeleteInput,
            ),
        ]
