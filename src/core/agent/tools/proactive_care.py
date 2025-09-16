"""
Proactive care tool for virtual friend - reminders, check-ins, and caring functions.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class ProactiveCare:
    """
    Tool for proactive caring functions like reminders, check-ins, and helpful suggestions.
    """
    
    def __init__(self, care_file: Optional[str] = None):
        """
        Initialize proactive care tool.
        
        Args:
            care_file: Path to care data storage file
        """
        self.logger = logging.getLogger(__name__)
        
        # Setup care file
        if care_file is None:
            project_root = Path(__file__).parent.parent.parent
            care_dir = project_root / "data" / "proactive_care"
            care_dir.mkdir(parents=True, exist_ok=True)
            self.care_file = care_dir / "care_data.json"
        else:
            self.care_file = Path(care_file)
        
        # Load care data
        self.care_data = self._load_care_data()
        
        # Caring message templates
        self.care_messages = {
            "check_in": [
                "Hi! How are you? It's been a while! 😊",
                "I was thinking of you. How's your mood?",
                "What's new? Tell me how your day went!",
                "Hey! I'm curious what's going on with you?",
                "Yo! How's life? Share the news!"
            ],
            "reminder": [
                "Reminder: {reminder_text}",
                "Hey, did you forget about {reminder_text}?",
                "Time for: {reminder_text} ⏰",
                "Friendly reminder: {reminder_text}",
                "Ping! {reminder_text} 📝"
            ],
            "encouragement": [
                "You're doing great! Keep it up! 💪",
                "I believe in you! You've got this!",
                "You're handling this wonderfully! 🌟",
                "Remember: you're stronger than you think!",
                "Every day you're getting better! ✨"
            ],
            "care": [
                "Don't forget to take care of yourself! 💙",
                "Drink water, rest, be kind to yourself!",
                "Remember: your health comes first!",
                "Time for a break! You deserve rest.",
                "Do something nice for yourself today! 🎁"
            ],
            "celebration": [
                "Congratulations! This calls for a celebration! 🎉",
                "Hooray! I'm so happy for you! 🥳",
                "Fantastic! You earned it! 🌟",
                "Wow! What an achievement! I'm proud of you!",
                "Awesome! Let's celebrate this! 🎊"
            ]
        }
        
        # Helpful suggestions by category
        self.suggestions = {
            "productivity": [
                "Try the Pomodoro technique for focus",
                "Make a to-do list for tomorrow in the evening",
                "Take short breaks every hour",
                "Start your day with the most important task"
            ],
            "wellness": [
                "A walk in fresh air can lift your mood",
                "Try meditation or breathing exercises",
                "Drink a glass of water — hydration matters!",
                "Stretch or do a light warm-up"
            ],
            "learning": [
                "Learn something new for 10 minutes a day",
                "Read an article on an interesting topic",
                "Watch an educational video",
                "Talk to someone about a new topic"
            ],
            "social": [
                "Message an old friend — they'll be glad!",
                "Call your loved ones and share updates",
                "Find a new community based on your interests",
                "Help someone — it can lift your mood"
            ]
        }
    
    def _load_care_data(self) -> Dict[str, Any]:
        """Load care data from file."""
        try:
            if self.care_file.exists():
                with open(self.care_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.logger.info("Loaded proactive care data")
                return data
            else:
                return self._create_empty_care_data()
        except Exception as e:
            self.logger.error(f"Error loading care data: {e}")
            return self._create_empty_care_data()
    
    def _create_empty_care_data(self) -> Dict[str, Any]:
        """Create empty care data structure."""
        return {
            "reminders": [],
            "check_in_schedule": {
                "frequency_hours": 24,
                "last_check_in": None,
                "missed_check_ins": 0
            },
            "care_history": [],
            "user_preferences": {
                "reminder_style": "friendly",
                "check_in_frequency": "daily",
                "preferred_care_types": ["encouragement", "reminders", "wellness"]
            },
            "celebration_calendar": [],
            "wellness_tracking": {
                "last_wellness_check": None,
                "wellness_reminders_sent": 0
            },
            "created": datetime.now().isoformat()
        }
    
    def _save_care_data(self):
        """Save care data to file."""
        try:
            with open(self.care_file, 'w', encoding='utf-8') as f:
                json.dump(self.care_data, f, indent=2, ensure_ascii=False)
            self.logger.info("Care data saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving care data: {e}")
    
    class ProactiveCareInput(BaseModel):
        """Input schema for proactive care tool."""
        action: str = Field(description="Action: set_reminder, check_in, send_encouragement, wellness_check, celebrate, get_care_status")
        content: Optional[str] = Field(default=None, description="Content for reminder or message")
        reminder_time: Optional[str] = Field(default=None, description="Time for reminder (YYYY-MM-DD HH:MM)")
        care_type: Optional[str] = Field(default=None, description="Type of care: encouragement, wellness, reminder, celebration")
        repeat_frequency: Optional[str] = Field(default=None, description="Frequency: daily, weekly, monthly")
        
    def get_tool(self) -> StructuredTool:
        """Get LangChain StructuredTool instance."""
        return StructuredTool(
            name="proactive_care",
            description="Manage reminders, check-ins, encouragement, and caring functions for the user",
            args_schema=self.ProactiveCareInput,
            func=self._handle_care_operation
        )
    
    def _handle_care_operation(
        self,
        action: str,
        content: Optional[str] = None,
        reminder_time: Optional[str] = None,
        care_type: Optional[str] = None,
        repeat_frequency: Optional[str] = None
    ) -> str:
        """Handle proactive care operations."""
        try:
            action = action.lower().strip()
            
            if action == "set_reminder":
                return self._set_reminder(content, reminder_time, repeat_frequency)
            
            elif action == "check_in":
                return self._proactive_check_in()
            
            elif action == "send_encouragement":
                return self._send_encouragement(content)
            
            elif action == "wellness_check":
                return self._wellness_check()
            
            elif action == "celebrate":
                return self._celebrate(content)
            
            elif action == "get_care_status":
                return self._get_care_status()
            
            else:
                return f"Unknown action: {action}. Available: set_reminder, check_in, send_encouragement, wellness_check, celebrate, get_care_status"
        
        except Exception as e:
            error_msg = f"Error in proactive care operation: {e}"
            self.logger.error(error_msg)
            return error_msg
    
    def _set_reminder(self, content: str, reminder_time: str = None, frequency: str = None) -> str:
        """Set a new reminder."""
        if not content:
            return "You need to provide reminder text"
        
        # Parse reminder time
        if reminder_time:
            try:
                reminder_datetime = datetime.fromisoformat(reminder_time)
            except:
                try:
                    # Try parsing just date
                    reminder_datetime = datetime.strptime(reminder_time, "%Y-%m-%d")
                except:
                    return "Invalid time format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM"
        else:
            # Default to tomorrow
            reminder_datetime = datetime.now() + timedelta(days=1)
        
        reminder = {
            "id": len(self.care_data["reminders"]) + 1,
            "content": content,
            "reminder_time": reminder_datetime.isoformat(),
            "frequency": frequency,
            "created": datetime.now().isoformat(),
            "active": True,
            "times_triggered": 0
        }
        
        self.care_data["reminders"].append(reminder)
        self._save_care_data()
        
        time_str = reminder_datetime.strftime("%Y-%m-%d at %H:%M")
        return f"✓ Set reminder: '{content}' for {time_str}"
    
    def _proactive_check_in(self) -> str:
        """Perform proactive check-in with user."""
        schedule = self.care_data["check_in_schedule"]
        now = datetime.now()
        
        # Update last check-in time
        schedule["last_check_in"] = now.isoformat()
        
        # Record check-in
        check_in_record = {
            "timestamp": now.isoformat(),
            "type": "proactive_check_in",
            "message_sent": True
        }
        self.care_data["care_history"].append(check_in_record)
        
        self._save_care_data()
        
        # Choose appropriate check-in message
        import random
        check_in_msg = random.choice(self.care_messages["check_in"])
        
        # Add personalized touch based on time of day
        hour = now.hour
        if 6 <= hour < 12:
            time_greeting = "Good morning! "
        elif 12 <= hour < 18:
            time_greeting = "Good afternoon! "
        elif 18 <= hour < 22:
            time_greeting = "Good evening! "
        else:
            time_greeting = "Good night! "
        
        return f"💙 {time_greeting}{check_in_msg}"
    
    def _send_encouragement(self, custom_message: str = None) -> str:
        """Send encouragement message."""
        if custom_message:
            message = f"💪 {custom_message}"
        else:
            import random
            message = random.choice(self.care_messages["encouragement"])
        
        # Record encouragement
        encouragement_record = {
            "timestamp": datetime.now().isoformat(),
            "type": "encouragement",
            "message": message,
            "custom": bool(custom_message)
        }
        self.care_data["care_history"].append(encouragement_record)
        self._save_care_data()
        
        return message
    
    def _wellness_check(self) -> str:
        """Perform wellness check and provide suggestions."""
        wellness = self.care_data["wellness_tracking"]
        wellness["last_wellness_check"] = datetime.now().isoformat()
        wellness["wellness_reminders_sent"] += 1
        
        import random
        
        # Choose wellness message and suggestion
        wellness_msg = random.choice(self.care_messages["care"])
        suggestion = random.choice(self.suggestions["wellness"])
        
        response = f"🌱 {wellness_msg}\n\n💡 Tip: {suggestion}"
        
        # Record wellness check
        wellness_record = {
            "timestamp": datetime.now().isoformat(),
            "type": "wellness_check",
            "suggestion": suggestion
        }
        self.care_data["care_history"].append(wellness_record)
        self._save_care_data()
        
        return response
    
    def _celebrate(self, achievement: str = None) -> str:
        """Celebrate user's achievement."""
        import random
        celebration_msg = random.choice(self.care_messages["celebration"])
        
        if achievement:
            response = f"🎉 {celebration_msg}\n\n🏆 Celebrating: {achievement}!"
        else:
            response = f"🎉 {celebration_msg}"
        
        # Record celebration
        celebration_record = {
            "timestamp": datetime.now().isoformat(),
            "type": "celebration",
            "achievement": achievement or "General celebration"
        }
        self.care_data["care_history"].append(celebration_record)
        
        # Add to celebration calendar
        self.care_data["celebration_calendar"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "achievement": achievement or "Celebration",
            "timestamp": datetime.now().isoformat()
        })
        
        self._save_care_data()
        return response
    
    def _get_care_status(self) -> str:
        """Get status of proactive care activities."""
        status = []
        
        # Active reminders
        active_reminders = [r for r in self.care_data["reminders"] if r["active"]]
        status.append(f"📋 Active reminders: {len(active_reminders)}")
        
        if active_reminders:
            next_reminder = min(active_reminders, key=lambda x: x["reminder_time"])
            next_time = datetime.fromisoformat(next_reminder["reminder_time"])
            status.append(f"⏰ Next: {next_reminder['content']} ({next_time.strftime('%m/%d at %H:%M')})")
        # Check-in info
        schedule = self.care_data["check_in_schedule"]
        if schedule["last_check_in"]:
            last_check = datetime.fromisoformat(schedule["last_check_in"])
            hours_since = (datetime.now() - last_check).total_seconds() / 3600
            status.append(f"💭 Last chat: {hours_since:.1f} hours ago")
        
        # Care statistics
        care_history = self.care_data["care_history"]
        if care_history:
            recent_care = [c for c in care_history if 
                          (datetime.now() - datetime.fromisoformat(c["timestamp"])).days < 7]
            status.append(f"💙 Caring actions this week: {len(recent_care)}")
        
        # Celebrations
        celebrations = self.care_data["celebration_calendar"]
        if celebrations:
            recent_celebrations = [c for c in celebrations if 
                                 (datetime.now() - datetime.strptime(c["date"], "%Y-%m-%d")).days < 30]
            status.append(f"🎉 Celebrations this month: {len(recent_celebrations)}")
        
        if not status:
            status.append("No active care yet. Let's fix that! 😊")
        
        return "🏥 CARE STATUS:\n\n" + "\n".join(status)
    
    def check_pending_reminders(self) -> List[str]:
        """Check for pending reminders."""
        now = datetime.now()
        pending_messages = []
        
        for reminder in self.care_data["reminders"]:
            if not reminder["active"]:
                continue
                
            reminder_time = datetime.fromisoformat(reminder["reminder_time"])
            if now >= reminder_time:
                import random
                message_template = random.choice(self.care_messages["reminder"])
                message = message_template.format(reminder_text=reminder["content"])
                pending_messages.append(message)
                
                # Update reminder
                reminder["times_triggered"] += 1
                
                # Handle frequency
                if reminder.get("frequency"):
                    if reminder["frequency"] == "daily":
                        reminder["reminder_time"] = (reminder_time + timedelta(days=1)).isoformat()
                    elif reminder["frequency"] == "weekly":
                        reminder["reminder_time"] = (reminder_time + timedelta(weeks=1)).isoformat()
                    elif reminder["frequency"] == "monthly":
                        reminder["reminder_time"] = (reminder_time + timedelta(days=30)).isoformat()
                    else:
                        reminder["active"] = False
                else:
                    reminder["active"] = False
        
        if pending_messages:
            self._save_care_data()
        
        return pending_messages
    
    def should_check_in(self) -> bool:
        """Check if it's time for proactive check-in."""
        schedule = self.care_data["check_in_schedule"]
        
        if not schedule["last_check_in"]:
            return True
        
        last_check = datetime.fromisoformat(schedule["last_check_in"])
        hours_since = (datetime.now() - last_check).total_seconds() / 3600
        frequency_hours = schedule.get("frequency_hours", 24)
        
        return hours_since >= frequency_hours
    
    def get_helpful_suggestion(self, category: str = None) -> str:
        """Get a helpful suggestion."""
        if category and category in self.suggestions:
            suggestions = self.suggestions[category]
        else:
            # Random category
            import random
            category = random.choice(list(self.suggestions.keys()))
            suggestions = self.suggestions[category]
        
        suggestion = random.choice(suggestions)
        return f"💡 Tip for {category}: {suggestion}"


def get_proactive_care_tool() -> StructuredTool:
    """Get proactive care tool instance."""
    tool = ProactiveCare()
    return tool.get_tool()
