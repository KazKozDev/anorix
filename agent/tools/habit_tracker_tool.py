"""
HabitTracker tool for forming and tracking habits (формирование привычек).
Structured LangChain tools with JSON file persistence.
"""

import os
import json
import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


class HabitTrackerTool:
    """Habit tracking with structured tools and file persistence."""

    def __init__(self):
        self.name = "habit_tracker"
        self.description = (
            "Manage habits. Structured tools: habit_create, habit_list, habit_get, "
            "habit_update, habit_delete, habit_log, habit_unlog, habit_streak, habit_stats."
        )
        self.habits: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
        # Persistence file
        self.storage_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "habits.json",
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
                    self.habits = data.get("habits", {})
                    self.next_id = int(data.get("next_id", 1))
        except Exception:
            self.habits = {}
            self.next_id = 1

    def _save(self):
        payload = {"habits": self.habits, "next_id": self.next_id}
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # ------------- Helpers -------------
    def _parse_date(self, s: Optional[str]) -> Optional[datetime.date]:
        if not s:
            return None
        fmts = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"]
        for fmt in fmts:
            try:
                return datetime.datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        return None

    def _today(self) -> datetime.date:
        return datetime.date.today()

    def _date_str(self, d: datetime.date) -> str:
        return d.strftime("%Y-%m-%d")

    # ------------- Schemas -------------
    class CreateInput(BaseModel):
        name: str = Field(description="Habit name (e.g., 'Drink water')")
        description: Optional[str] = Field(default="", description="Habit description")
        frequency: Optional[str] = Field(default="daily", description="Frequency: daily|weekly|weekdays|custom")
        start_date: Optional[str] = Field(default=None, description="Start date 'YYYY-MM-DD'")
        target_streak: Optional[int] = Field(default=None, description="Target streak in days")
        reminder_time: Optional[str] = Field(default=None, description="Daily reminder time 'HH:MM' (optional)")
        tags: Optional[List[str]] = Field(default=None, description="Tags for filtering")

    class ListInput(BaseModel):
        tag: Optional[str] = Field(default=None, description="Filter by tag")
        active_only: Optional[bool] = Field(default=False, description="List only active habits")

    class GetInput(BaseModel):
        habit_id: str = Field(description="Habit ID")

    class UpdateInput(BaseModel):
        habit_id: str = Field(description="Habit ID")
        name: Optional[str] = Field(default=None)
        description: Optional[str] = Field(default=None)
        frequency: Optional[str] = Field(default=None)
        start_date: Optional[str] = Field(default=None)
        target_streak: Optional[int] = Field(default=None)
        reminder_time: Optional[str] = Field(default=None)
        tags: Optional[List[str]] = Field(default=None)
        status: Optional[str] = Field(default=None, description="active|paused|archived")

    class DeleteInput(BaseModel):
        habit_id: str = Field(description="Habit ID")

    class LogInput(BaseModel):
        habit_id: str = Field(description="Habit ID")
        date: Optional[str] = Field(default=None, description="Date to log 'YYYY-MM-DD' (defaults to today)")

    class UnlogInput(BaseModel):
        habit_id: str = Field(description="Habit ID")
        date: Optional[str] = Field(default=None, description="Date to unlog 'YYYY-MM-DD' (defaults to today)")

    class StreakInput(BaseModel):
        habit_id: str = Field(description="Habit ID")

    class StatsInput(BaseModel):
        habit_id: str = Field(description="Habit ID")
        start_date: Optional[str] = Field(default=None, description="Range start 'YYYY-MM-DD'")
        end_date: Optional[str] = Field(default=None, description="Range end 'YYYY-MM-DD'")

    # ------------- Core ops -------------
    def st_create(
        self,
        name: str,
        description: Optional[str] = None,
        frequency: Optional[str] = None,
        start_date: Optional[str] = None,
        target_streak: Optional[int] = None,
        reminder_time: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        hid = str(self.next_id)
        self.next_id += 1
        sd = self._parse_date(start_date) if start_date else self._today()
        habit = {
            "id": hid,
            "name": name,
            "description": description or "",
            "frequency": (frequency or "daily").lower(),
            "status": "active",
            "target_streak": int(target_streak) if target_streak is not None else None,
            "reminder_time": reminder_time or "",
            "start_date": self._date_str(sd),
            "tags": tags or [],
            "created_at": self._date_str(self._today()),
            "logs": [],  # list of YYYY-MM-DD strings
        }
        self.habits[hid] = habit
        self._save()
        return f"✅ Habit created: {name} (ID: {hid})"

    def st_list(self, tag: Optional[str] = None, active_only: Optional[bool] = False) -> str:
        items = list(self.habits.values())
        if tag:
            items = [h for h in items if tag in (h.get("tags") or [])]
        if active_only:
            items = [h for h in items if h.get("status", "active") == "active"]
        if not items:
            return "🧩 No habits found"
        items.sort(key=lambda h: h.get("name", ""))
        out = ["🧩 Habits:", "=" * 40]
        for h in items:
            out.append(f"[{h['id']}] {h['name']} ({h.get('status','active')}) — freq: {h.get('frequency','daily')}")
            if h.get("target_streak"):
                out.append(f"   🎯 Target streak: {h['target_streak']} days")
            if h.get("reminder_time"):
                out.append(f"   ⏰ Reminder: {h['reminder_time']}")
            if h.get("tags"):
                out.append(f"   🏷️ Tags: {', '.join(h['tags'])}")
            out.append("")
        return "\n".join(out)

    def st_get(self, habit_id: str) -> str:
        h = self.habits.get(habit_id)
        if not h:
            return f"❌ Habit '{habit_id}' not found"
        lines = [
            f"[{h['id']}] {h['name']} ({h.get('status','active')}) — freq: {h.get('frequency','daily')}",
            f"📅 Start: {h.get('start_date','')}",
            f"🧮 Logged days: {len(h.get('logs', []))}",
        ]
        if h.get("target_streak"):
            lines.append(f"🎯 Target streak: {h['target_streak']} days")
        if h.get("reminder_time"):
            lines.append(f"⏰ Reminder: {h['reminder_time']}")
        if h.get("tags"):
            lines.append(f"🏷️ Tags: {', '.join(h['tags'])}")
        if h.get("description"):
            lines.append(f"📝 {h['description']}")
        return "\n".join(lines)

    def st_update(
        self,
        habit_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        frequency: Optional[str] = None,
        start_date: Optional[str] = None,
        target_streak: Optional[int] = None,
        reminder_time: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> str:
        h = self.habits.get(habit_id)
        if not h:
            return f"❌ Habit '{habit_id}' not found"
        if name is not None:
            h["name"] = name
        if description is not None:
            h["description"] = description
        if frequency is not None:
            h["frequency"] = frequency.lower()
        if start_date is not None:
            sd = self._parse_date(start_date)
            if not sd:
                return "❌ Invalid start_date format. Use 'YYYY-MM-DD'"
            h["start_date"] = self._date_str(sd)
        if target_streak is not None:
            try:
                h["target_streak"] = int(target_streak)
            except Exception:
                return "❌ Invalid target_streak"
        if reminder_time is not None:
            h["reminder_time"] = reminder_time
        if tags is not None:
            h["tags"] = tags
        if status is not None:
            h["status"] = status.lower()
        self._save()
        return f"✅ Habit updated: {h['name']} (ID: {habit_id})"

    def st_delete(self, habit_id: str) -> str:
        h = self.habits.pop(habit_id, None)
        if not h:
            return f"❌ Habit '{habit_id}' not found"
        self._save()
        return f"✅ Habit deleted: {h['name']}"

    def st_log(self, habit_id: str, date: Optional[str] = None) -> str:
        h = self.habits.get(habit_id)
        if not h:
            return f"❌ Habit '{habit_id}' not found"
        d = self._parse_date(date) if date else self._today()
        dstr = self._date_str(d)
        logs = set(h.get("logs", []))
        logs.add(dstr)
        h["logs"] = sorted(list(logs))
        self._save()
        return f"✅ Logged {h['name']} on {dstr}"

    def st_unlog(self, habit_id: str, date: Optional[str] = None) -> str:
        h = self.habits.get(habit_id)
        if not h:
            return f"❌ Habit '{habit_id}' not found"
        d = self._parse_date(date) if date else self._today()
        dstr = self._date_str(d)
        logs = set(h.get("logs", []))
        if dstr in logs:
            logs.remove(dstr)
            h["logs"] = sorted(list(logs))
            self._save()
            return f"✅ Unlogged {h['name']} on {dstr}"
        return f"ℹ️ No log found for {dstr}"

    def _current_streak(self, dates: List[str]) -> int:
        if not dates:
            return 0
        # Count consecutive days ending today
        days = set(dates)
        count = 0
        cur = self._today()
        while self._date_str(cur) in days:
            count += 1
            cur -= datetime.timedelta(days=1)
        return count

    def st_streak(self, habit_id: str) -> str:
        h = self.habits.get(habit_id)
        if not h:
            return f"❌ Habit '{habit_id}' not found"
        streak = self._current_streak(h.get("logs", []))
        tgt = h.get("target_streak")
        extra = f" / {tgt} target" if tgt else ""
        return f"🏆 Current streak for {h['name']}: {streak}{extra}"

    def st_stats(self, habit_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        h = self.habits.get(habit_id)
        if not h:
            return f"❌ Habit '{habit_id}' not found"
        logs = [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in h.get("logs", [])]
        if start_date:
            sd = self._parse_date(start_date)
        else:
            sd = min(logs) if logs else self._today()
        if end_date:
            ed = self._parse_date(end_date)
        else:
            ed = self._today()
        if not sd or not ed:
            return "❌ Invalid date range"
        total_days = (ed - sd).days + 1
        hit_days = len([d for d in logs if sd <= d <= ed])
        ratio = (hit_days / total_days * 100.0) if total_days > 0 else 0.0
        return (
            f"📈 Stats for {h['name']} from {self._date_str(sd)} to {self._date_str(ed)}:\n"
            f"   Days done: {hit_days}/{total_days} ({ratio:.1f}%)"
        )

    # ------------- Structured tools -------------
    def get_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.st_create,
                name="habit_create",
                description="Create a habit (name, optional description, frequency, start_date, target_streak, reminder_time, tags).",
                args_schema=HabitTrackerTool.CreateInput,
            ),
            StructuredTool.from_function(
                func=self.st_list,
                name="habit_list",
                description="List habits, optional filters: tag, active_only.",
                args_schema=HabitTrackerTool.ListInput,
            ),
            StructuredTool.from_function(
                func=self.st_get,
                name="habit_get",
                description="Get habit details by ID.",
                args_schema=HabitTrackerTool.GetInput,
            ),
            StructuredTool.from_function(
                func=self.st_update,
                name="habit_update",
                description="Update a habit by ID (name, description, frequency, start_date, target_streak, reminder_time, tags, status).",
                args_schema=HabitTrackerTool.UpdateInput,
            ),
            StructuredTool.from_function(
                func=self.st_delete,
                name="habit_delete",
                description="Delete a habit by ID.",
                args_schema=HabitTrackerTool.DeleteInput,
            ),
            StructuredTool.from_function(
                func=self.st_log,
                name="habit_log",
                description="Log a habit done for a specific date (defaults to today).",
                args_schema=HabitTrackerTool.LogInput,
            ),
            StructuredTool.from_function(
                func=self.st_unlog,
                name="habit_unlog",
                description="Remove a logged day for a habit (defaults to today).",
                args_schema=HabitTrackerTool.UnlogInput,
            ),
            StructuredTool.from_function(
                func=self.st_streak,
                name="habit_streak",
                description="Show current streak for a habit.",
                args_schema=HabitTrackerTool.StreakInput,
            ),
            StructuredTool.from_function(
                func=self.st_stats,
                name="habit_stats",
                description="Show stats for a habit over a date range (defaults to logs range to today).",
                args_schema=HabitTrackerTool.StatsInput,
            ),
        ]
