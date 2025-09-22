"""
GoalTracker tool for creating and managing goals (отслеживание целей).
Structured LangChain tools with simple file persistence (JSON).
"""

import os
import json
import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


class GoalTrackerTool:
    """Goal management with structured tools and file persistence."""

    def __init__(self):
        self.name = "goal_tracker"
        self.description = (
            "Manage goals. Structured tools: goal_create, goal_list, goal_get, "
            "goal_update, goal_delete, goal_progress, goal_complete. Time format: 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD'."
        )
        self.goals: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
        # Persistence file
        self.storage_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "goals.json",
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
                    self.goals = data.get("goals", {})
                    self.next_id = int(data.get("next_id", 1))
        except Exception:
            self.goals = {}
            self.next_id = 1

    def _save(self):
        payload = {"goals": self.goals, "next_id": self.next_id}
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # ------------- Helpers -------------
    def _parse_dt(self, s: Optional[str]) -> Optional[datetime.datetime]:
        if not s:
            return None
        fmts = ["%Y-%m-%d %H:%M", "%Y-%m-%d", "%d-%m-%Y %H:%M", "%m/%d/%Y %H:%M"]
        for fmt in fmts:
            try:
                return datetime.datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    def _fmt_dt(self, dt: datetime.datetime, with_time: bool = True) -> str:
        return dt.strftime("%Y-%m-%d %H:%M" if with_time else "%Y-%m-%d")

    # ------------- Schemas -------------
    class CreateInput(BaseModel):
        title: str = Field(description="Goal title")
        description: Optional[str] = Field(default="", description="Goal description")
        target_date: Optional[str] = Field(default=None, description="Target date/time 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD'")
        priority: Optional[str] = Field(default="normal", description="Priority: low|normal|high|urgent")
        progress: Optional[float] = Field(default=0.0, description="Initial progress in percent (0-100)")

    class ListInput(BaseModel):
        status: Optional[str] = Field(default=None, description="Filter by status: active|completed|on_hold")
        priority: Optional[str] = Field(default=None, description="Filter by priority: low|normal|high|urgent")
        date: Optional[str] = Field(default=None, description="List goals with this target date 'YYYY-MM-DD'")
        start_date: Optional[str] = Field(default=None, description="Range start 'YYYY-MM-DD'")
        end_date: Optional[str] = Field(default=None, description="Range end 'YYYY-MM-DD'")

    class GetInput(BaseModel):
        goal_id: str = Field(description="Goal ID")

    class UpdateInput(BaseModel):
        goal_id: str = Field(description="Goal ID")
        title: Optional[str] = Field(default=None)
        description: Optional[str] = Field(default=None)
        target_date: Optional[str] = Field(default=None)
        priority: Optional[str] = Field(default=None)
        status: Optional[str] = Field(default=None, description="active|completed|on_hold")
        progress: Optional[float] = Field(default=None, description="Progress percent (0-100)")

    class DeleteInput(BaseModel):
        goal_id: str = Field(description="Goal ID")

    class ProgressInput(BaseModel):
        goal_id: str = Field(description="Goal ID")
        progress: float = Field(description="Set progress percent (0-100)")

    class CompleteInput(BaseModel):
        goal_id: str = Field(description="Goal ID")

    # ------------- Core ops -------------
    def st_create(
        self,
        title: str,
        description: Optional[str] = None,
        target_date: Optional[str] = None,
        priority: Optional[str] = None,
        progress: Optional[float] = None,
    ) -> str:
        gid = str(self.next_id)
        self.next_id += 1
        td = self._parse_dt(target_date) if target_date else None
        goal = {
            "id": gid,
            "title": title,
            "description": description or "",
            "priority": (priority or "normal").lower(),
            "status": "active",
            "progress": float(progress) if progress is not None else 0.0,
            "created_at": self._fmt_dt(datetime.datetime.now()),
            "target_date": self._fmt_dt(td) if td else "",
        }
        goal["progress"] = max(0.0, min(100.0, goal["progress"]))
        self.goals[gid] = goal
        self._save()
        return f"✅ Goal created: {title} (ID: {gid})"

    def st_list(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        items: List[Dict[str, Any]] = list(self.goals.values())
        if status:
            items = [g for g in items if g.get("status", "active").lower() == status.lower()]
        if priority:
            items = [g for g in items if g.get("priority", "normal").lower() == priority.lower()]
        if date:
            items = [g for g in items if g.get("target_date", "").startswith(date)]
        if start_date and end_date:
            try:
                sd = datetime.datetime.strptime(start_date + " 00:00", "%Y-%m-%d %H:%M")
                ed = datetime.datetime.strptime(end_date + " 23:59", "%Y-%m-%d %H:%M")
                items = [
                    g for g in items
                    if g.get("target_date")
                    and sd <= datetime.datetime.strptime(g["target_date"], "%Y-%m-%d %H:%M") <= ed
                ]
            except ValueError:
                return "❌ Invalid date format. Use YYYY-MM-DD"
        if not items:
            return "🎯 No goals found"
        # Sort: active first, then by nearest target date
        def sort_key(g):
            status_weight = 0 if g.get("status") == "active" else (1 if g.get("status") == "on_hold" else 2)
            td = g.get("target_date") or "9999-12-31 23:59"
            return (status_weight, td)
        items.sort(key=sort_key)
        pr_emoji = {"low": "🟢", "normal": "🟡", "high": "🟠", "urgent": "🔴"}
        out = ["🎯 Goals:", "=" * 40]
        for g in items:
            out.append(f"{pr_emoji.get(g.get('priority','normal'),'⚪')} [{g['id']}] {g['title']} ({g['status']}) — {g['progress']:.0f}%")
            if g.get("target_date"):
                out.append(f"   🗓️ Target: {g['target_date']}")
            if g.get("description"):
                out.append(f"   📝 {g['description']}")
            out.append("")
        return "\n".join(out)

    def st_get(self, goal_id: str) -> str:
        g = self.goals.get(goal_id)
        if not g:
            return f"❌ Goal '{goal_id}' not found"
        pr_emoji = {"low": "🟢", "normal": "🟡", "high": "🟠", "urgent": "🔴"}
        lines = [
            f"{pr_emoji.get(g.get('priority','normal'),'⚪')} [{g['id']}] {g['title']} ({g['status']}) — {g['progress']:.0f}%",
        ]
        if g.get("target_date"):
            lines.append(f"🗓️ Target: {g['target_date']}")
        if g.get("description"):
            lines.append(f"📝 {g['description']}")
        lines.append(f"📅 Created: {g.get('created_at','')}")
        return "\n".join(lines)

    def st_update(
        self,
        goal_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        target_date: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        progress: Optional[float] = None,
    ) -> str:
        g = self.goals.get(goal_id)
        if not g:
            return f"❌ Goal '{goal_id}' not found"
        if title is not None:
            g["title"] = title
        if description is not None:
            g["description"] = description
        if priority is not None:
            g["priority"] = priority.lower()
        if status is not None:
            g["status"] = status.lower()
        if progress is not None:
            try:
                g["progress"] = max(0.0, min(100.0, float(progress)))
            except Exception:
                return "❌ Invalid progress value"
        if target_date is not None:
            dt = self._parse_dt(target_date)
            if not dt:
                return "❌ Invalid target_date format. Use 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD'"
            g["target_date"] = self._fmt_dt(dt)
        self._save()
        return f"✅ Goal updated: {g['title']} (ID: {goal_id})"

    def st_delete(self, goal_id: str) -> str:
        g = self.goals.pop(goal_id, None)
        if not g:
            return f"❌ Goal '{goal_id}' not found"
        self._save()
        return f"✅ Goal deleted: {g['title']}"

    def st_progress(self, goal_id: str, progress: float) -> str:
        g = self.goals.get(goal_id)
        if not g:
            return f"❌ Goal '{goal_id}' not found"
        try:
            g["progress"] = max(0.0, min(100.0, float(progress)))
        except Exception:
            return "❌ Invalid progress value"
        # Auto-complete if reached 100
        if g["progress"] >= 100.0:
            g["status"] = "completed"
        self._save()
        return f"✅ Progress updated: {g['title']} — {g['progress']:.0f}%"

    def st_complete(self, goal_id: str) -> str:
        g = self.goals.get(goal_id)
        if not g:
            return f"❌ Goal '{goal_id}' not found"
        g["status"] = "completed"
        g["progress"] = max(g.get("progress", 0.0), 100.0)
        self._save()
        return f"✅ Goal completed: {g['title']}"

    # ------------- Structured tools -------------
    def get_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.st_create,
                name="goal_create",
                description="Create a goal (title, optional description, target_date, priority, progress).",
                args_schema=GoalTrackerTool.CreateInput,
            ),
            StructuredTool.from_function(
                func=self.st_list,
                name="goal_list",
                description="List goals with optional filters: status, priority, date or date range.",
                args_schema=GoalTrackerTool.ListInput,
            ),
            StructuredTool.from_function(
                func=self.st_get,
                name="goal_get",
                description="Get goal details by ID.",
                args_schema=GoalTrackerTool.GetInput,
            ),
            StructuredTool.from_function(
                func=self.st_update,
                name="goal_update",
                description="Update a goal by ID (title, description, target_date, priority, status, progress).",
                args_schema=GoalTrackerTool.UpdateInput,
            ),
            StructuredTool.from_function(
                func=self.st_delete,
                name="goal_delete",
                description="Delete a goal by ID.",
                args_schema=GoalTrackerTool.DeleteInput,
            ),
            StructuredTool.from_function(
                func=self.st_progress,
                name="goal_progress",
                description="Set progress percent (0-100) for a goal by ID; auto-completes at 100%.",
                args_schema=GoalTrackerTool.ProgressInput,
            ),
            StructuredTool.from_function(
                func=self.st_complete,
                name="goal_complete",
                description="Mark a goal as completed by ID.",
                args_schema=GoalTrackerTool.CompleteInput,
            ),
        ]
