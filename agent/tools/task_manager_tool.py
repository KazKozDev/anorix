"""
TaskManager tool for creating and managing to-do lists (списки дел).
Structured LangChain tools with simple file persistence (JSON).
"""

import os
import json
import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


class TaskManagerTool:
    """Task management with structured tools and file persistence."""

    def __init__(self):
        self.name = "task_manager"
        self.description = (
            "Manage tasks (to-do). Structured tools: task_create, task_list, task_get, "
            "task_update, task_delete, task_complete, task_reopen. Time format: 'YYYY-MM-DD HH:MM' or date 'YYYY-MM-DD'."
        )
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
        # Persistence file
        self.storage_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "tasks.json",
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
                    self.tasks = data.get("tasks", {})
                    self.next_id = int(data.get("next_id", 1))
        except Exception:
            self.tasks = {}
            self.next_id = 1

    def _save(self):
        payload = {"tasks": self.tasks, "next_id": self.next_id}
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
        title: str = Field(description="Task title")
        description: Optional[str] = Field(default="", description="Task description")
        due: Optional[str] = Field(default=None, description="Due date/time 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD'")
        priority: Optional[str] = Field(default="normal", description="Priority: low|normal|high|urgent")
        tags: Optional[List[str]] = Field(default=None, description="List of tags")

    class ListInput(BaseModel):
        status: Optional[str] = Field(default=None, description="Filter by status: pending|done")
        priority: Optional[str] = Field(default=None, description="Filter by priority: low|normal|high|urgent")
        tag: Optional[str] = Field(default=None, description="Filter by a tag")
        date: Optional[str] = Field(default=None, description="Specific date 'YYYY-MM-DD' for due")
        start_date: Optional[str] = Field(default=None, description="Range start 'YYYY-MM-DD'")
        end_date: Optional[str] = Field(default=None, description="Range end 'YYYY-MM-DD'")

    class GetInput(BaseModel):
        task_id: str = Field(description="Task ID")

    class UpdateInput(BaseModel):
        task_id: str = Field(description="Task ID")
        title: Optional[str] = Field(default=None)
        description: Optional[str] = Field(default=None)
        due: Optional[str] = Field(default=None)
        priority: Optional[str] = Field(default=None)
        tags: Optional[List[str]] = Field(default=None)
        status: Optional[str] = Field(default=None, description="pending|done")

    class DeleteInput(BaseModel):
        task_id: str = Field(description="Task ID")

    class CompleteInput(BaseModel):
        task_id: str = Field(description="Task ID")

    class ReopenInput(BaseModel):
        task_id: str = Field(description="Task ID")

    # ------------- Core ops -------------
    def st_create(
        self,
        title: str,
        description: Optional[str] = None,
        due: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        tid = str(self.next_id)
        self.next_id += 1
        due_dt = self._parse_dt(due) if due else None
        task = {
            "id": tid,
            "title": title,
            "description": description or "",
            "priority": (priority or "normal").lower(),
            "status": "pending",
            "tags": tags or [],
            "created_at": self._fmt_dt(datetime.datetime.now()),
            "due": self._fmt_dt(due_dt) if due_dt else "",
        }
        self.tasks[tid] = task
        self._save()
        return f"✅ Task created: {title} (ID: {tid})"

    def st_list(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        items: List[Dict[str, Any]] = list(self.tasks.values())
        if status:
            items = [t for t in items if t.get("status", "pending").lower() == status.lower()]
        if priority:
            items = [t for t in items if t.get("priority", "normal").lower() == priority.lower()]
        if tag:
            items = [t for t in items if tag in (t.get("tags") or [])]
        if date:
            items = [t for t in items if t.get("due", "").startswith(date)]
        if start_date and end_date:
            try:
                sd = datetime.datetime.strptime(start_date + " 00:00", "%Y-%m-%d %H:%M")
                ed = datetime.datetime.strptime(end_date + " 23:59", "%Y-%m-%d %H:%M")
                items = [
                    t for t in items
                    if t.get("due")
                    and sd <= datetime.datetime.strptime(t["due"], "%Y-%m-%d %H:%M") <= ed
                ]
            except ValueError:
                return "❌ Invalid date format. Use YYYY-MM-DD"
        if not items:
            return "📝 No tasks found"
        items.sort(key=lambda x: (x.get("status") != "pending", x.get("due") or "9999-12-31 23:59"))
        out = ["📝 Tasks:", "=" * 40]
        pr_emoji = {"low": "🟢", "normal": "🟡", "high": "🟠", "urgent": "🔴"}
        for t in items:
            out.append(f"{pr_emoji.get(t.get('priority','normal'),'⚪')} [{t['id']}] {t['title']} ({t['status']})")
            if t.get("due"):
                out.append(f"   ⏰ Due: {t['due']}")
            if t.get("tags"):
                out.append(f"   🏷️ Tags: {', '.join(t['tags'])}")
            if t.get("description"):
                out.append(f"   📝 {t['description']}")
            out.append("")
        return "\n".join(out)

    def st_get(self, task_id: str) -> str:
        t = self.tasks.get(task_id)
        if not t:
            return f"❌ Task '{task_id}' not found"
        pr_emoji = {"low": "🟢", "normal": "🟡", "high": "🟠", "urgent": "🔴"}
        lines = [
            f"{pr_emoji.get(t.get('priority','normal'),'⚪')} [{t['id']}] {t['title']} ({t['status']})",
        ]
        if t.get("due"):
            lines.append(f"⏰ Due: {t['due']}")
        if t.get("tags"):
            lines.append(f"🏷️ Tags: {', '.join(t['tags'])}")
        if t.get("description"):
            lines.append(f"📝 {t['description']}")
        lines.append(f"📅 Created: {t.get('created_at','')}")
        return "\n".join(lines)

    def st_update(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> str:
        t = self.tasks.get(task_id)
        if not t:
            return f"❌ Task '{task_id}' not found"
        if title is not None:
            t["title"] = title
        if description is not None:
            t["description"] = description
        if priority is not None:
            t["priority"] = priority.lower()
        if tags is not None:
            t["tags"] = tags
        if status is not None:
            t["status"] = status.lower()
        if due is not None:
            dt = self._parse_dt(due)
            if not dt:
                return "❌ Invalid due format. Use 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD'"
            t["due"] = self._fmt_dt(dt)
        self._save()
        return f"✅ Task updated: {t['title']} (ID: {task_id})"

    def st_delete(self, task_id: str) -> str:
        t = self.tasks.pop(task_id, None)
        if not t:
            return f"❌ Task '{task_id}' not found"
        self._save()
        return f"✅ Task deleted: {t['title']}"

    def st_complete(self, task_id: str) -> str:
        t = self.tasks.get(task_id)
        if not t:
            return f"❌ Task '{task_id}' not found"
        t["status"] = "done"
        self._save()
        return f"✅ Task completed: {t['title']}"

    def st_reopen(self, task_id: str) -> str:
        t = self.tasks.get(task_id)
        if not t:
            return f"❌ Task '{task_id}' not found"
        t["status"] = "pending"
        self._save()
        return f"✅ Task reopened: {t['title']}"

    # ------------- Structured tools -------------
    def get_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.st_create,
                name="task_create",
                description="Create a task (title, optional description, due, priority, tags).",
                args_schema=TaskManagerTool.CreateInput,
            ),
            StructuredTool.from_function(
                func=self.st_list,
                name="task_list",
                description="List tasks with optional filters: status, priority, tag, date or date range.",
                args_schema=TaskManagerTool.ListInput,
            ),
            StructuredTool.from_function(
                func=self.st_get,
                name="task_get",
                description="Get task details by ID.",
                args_schema=TaskManagerTool.GetInput,
            ),
            StructuredTool.from_function(
                func=self.st_update,
                name="task_update",
                description="Update a task by ID (title, description, due, priority, tags, status).",
                args_schema=TaskManagerTool.UpdateInput,
            ),
            StructuredTool.from_function(
                func=self.st_delete,
                name="task_delete",
                description="Delete a task by ID.",
                args_schema=TaskManagerTool.DeleteInput,
            ),
            StructuredTool.from_function(
                func=self.st_complete,
                name="task_complete",
                description="Mark a task as done by ID.",
                args_schema=TaskManagerTool.CompleteInput,
            ),
            StructuredTool.from_function(
                func=self.st_reopen,
                name="task_reopen",
                description="Reopen a completed task by ID (set status to pending).",
                args_schema=TaskManagerTool.ReopenInput,
            ),
        ]
