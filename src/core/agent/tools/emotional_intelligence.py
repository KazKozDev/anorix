"""
Emotional intelligence tool for virtual friend - analyzes mood, provides emotional support.
"""

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class EmotionalIntelligenceTool:
    """
    Tool for emotional intelligence and mood analysis.
    Tracks user's emotional state and provides appropriate responses.
    """
    
    def __init__(self, emotion_file: Optional[str] = None):
        """
        Initialize emotional intelligence tool.
        
        Args:
            emotion_file: Path to emotion data storage file
        """
        self.logger = logging.getLogger(__name__)
        
        # Setup emotion file
        if emotion_file is None:
            project_root = Path(__file__).parent.parent.parent
            emotion_dir = project_root / "data" / "emotional_memory"
            emotion_dir.mkdir(parents=True, exist_ok=True)
            self.emotion_file = emotion_dir / "emotions.json"
        else:
            self.emotion_file = Path(emotion_file)
        
        # Load emotional data
        self.emotion_data = self._load_emotion_data()
        
        # Emotion keywords and patterns
        self.emotion_patterns = {
            "happy": ["happy", "joy", "excited", "great", "awesome", "wonderful", "fantastic", "good", "smile", "laugh", "cheerful", "pleased", "glad", "delighted"],
            "sad": ["sad", "depressed", "down", "upset", "disappointed", "hurt", "crying", "tears", "blue", "melancholy", "gloomy", "miserable"],
            "angry": ["angry", "mad", "furious", "rage", "annoyed", "irritated", "frustrated", "pissed", "outraged", "livid"],
            "anxious": ["anxious", "worried", "nervous", "stressed", "panic", "fear", "scared", "concerned", "tense", "uneasy"],
            "excited": ["excited", "thrilled", "pumped", "energized", "enthusiastic", "eager", "hyped", "elated"],
            "tired": ["tired", "exhausted", "sleepy", "drained", "weary", "fatigue", "worn out"],
            "confused": ["confused", "puzzled", "lost", "unsure", "bewildered", "perplexed"],
            "grateful": ["grateful", "thankful", "appreciate", "blessed", "thank you"],
            "lonely": ["lonely", "alone", "isolated", "solitary", "abandoned"],
            "confident": ["confident", "sure", "certain", "proud", "strong", "capable"]
        }
        
        # Supportive responses by emotion
        self.supportive_responses = {
            "happy": [
                "That's wonderful! I'm so happy for you! 😊",
                "Your joy is contagious! Tell me more!",
                "Amazing! Let's celebrate this together!",
                "I can see you're in a great mood! That's awesome!"
            ],
            "sad": [
                "I'm sorry you're feeling sad. I'm here to support you.",
                "It's okay to feel sad sometimes. Do you want to talk about it?",
                "I understand it's tough. You're not alone in this.",
                "Remember, difficult times pass. I'm here with you."
            ],
            "angry": [
                "I can see you're angry. Want to tell me what happened?",
                "Anger is a natural emotion. Let's unpack the situation.",
                "Take a deep breath. I'm here to listen.",
                "Something clearly upset you. Tell me about it."
            ],
            "anxious": [
                "I understand your worry. Let's try to break things down.",
                "Anxiety can be heavy. Do you want to talk about what's on your mind?",
                "Remember: deep breathing helps. I'm right here with you.",
                "You can handle this. Let's think through solutions together."
            ],
            "excited": [
                "So much energy! I'm getting hyped by your enthusiasm!",
                "Great to see you so inspired! Tell me more!",
                "Your excitement is contagious! What's going on?",
                "I love your energy! Share your joy with me!"
            ],
            "tired": [
                "Seems like you're tired. Maybe it's time to rest?",
                "Fatigue is a sign you need to recharge.",
                "Don't forget to take care of yourself. Rest matters.",
                "Want to switch to something more relaxing?"
            ],
            "confused": [
                "Feeling confused is okay. Let's figure it out together.",
                "Sometimes things need time to fall into place.",
                "I'll help you find clarity. What's on your mind?",
                "Questions help us find answers. What's bothering you?"
            ],
            "grateful": [
                "It's so nice to hear your gratitude! 💝",
                "Your appreciation is very touching.",
                "I'm grateful for our conversations too!",
                "Thank you for such warm words!"
            ],
            "lonely": [
                "You're not alone. I'm here with you.",
                "Loneliness can be tough. Want to talk?",
                "Remember, there are people who care about you.",
                "I'm always ready to keep you company in conversation."
            ],
            "confident": [
                "Great! Confidence is a wonderful quality!",
                "I see your strength and determination. Keep it up!",
                "Your confidence is inspiring! Stay in that groove!",
                "Awesome to see you feeling so self-assured!"
            ]
        }
    
    def _load_emotion_data(self) -> Dict[str, Any]:
        """Load emotion data from file."""
        try:
            if self.emotion_file.exists():
                with open(self.emotion_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.logger.info("Loaded emotional intelligence data")
                return data
            else:
                return self._create_empty_emotion_data()
        except Exception as e:
            self.logger.error(f"Error loading emotion data: {e}")
            return self._create_empty_emotion_data()
    
    def _create_empty_emotion_data(self) -> Dict[str, Any]:
        """Create empty emotion data structure."""
        return {
            "emotion_history": [],
            "mood_patterns": {},
            "emotional_triggers": {},
            "support_preferences": {
                "preferred_response_style": "empathetic",
                "comfort_topics": [],
                "avoid_topics": []
            },
            "interaction_context": {
                "current_mood": "neutral",
                "last_mood_change": None,
                "consecutive_negative_days": 0,
                "total_positive_interactions": 0,
                "total_negative_interactions": 0
            },
            "created": datetime.now().isoformat()
        }
    
    def _save_emotion_data(self):
        """Save emotion data to file."""
        try:
            with open(self.emotion_file, 'w', encoding='utf-8') as f:
                json.dump(self.emotion_data, f, indent=2, ensure_ascii=False)
            self.logger.info("Emotional data saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving emotion data: {e}")
    
    class EmotionalInput(BaseModel):
        """Input schema for emotional intelligence tool."""
        action: str = Field(description="Action: analyze_mood, provide_support, get_mood_history, set_comfort_preference, emotional_check_in")
        text: Optional[str] = Field(default=None, description="Text to analyze for emotions")
        mood: Optional[str] = Field(default=None, description="User's current mood")
        intensity: Optional[int] = Field(default=5, description="Emotion intensity 1-10")
        context: Optional[str] = Field(default=None, description="Context or reason for the emotion")
        
    def get_tool(self) -> StructuredTool:
        """Get LangChain StructuredTool instance."""
        return StructuredTool(
            name="emotional_intelligence",
            description="Analyze user emotions, provide emotional support, track mood patterns",
            args_schema=self.EmotionalInput,
            func=self._handle_emotional_operation
        )
    
    def _handle_emotional_operation(
        self,
        action: str,
        text: Optional[str] = None,
        mood: Optional[str] = None,
        intensity: Optional[int] = 5,
        context: Optional[str] = None
    ) -> str:
        """Handle emotional intelligence operations."""
        try:
            action = action.lower().strip()
            
            if action == "analyze_mood":
                return self._analyze_mood(text or "")
            
            elif action == "provide_support":
                return self._provide_emotional_support(mood, intensity, context)
            
            elif action == "get_mood_history":
                return self._get_mood_history()
            
            elif action == "set_comfort_preference":
                return self._set_comfort_preference(text, context)
            
            elif action == "emotional_check_in":
                return self._emotional_check_in()
            
            else:
                return f"Unknown action: {action}. Available: analyze_mood, provide_support, get_mood_history, set_comfort_preference, emotional_check_in"
        
        except Exception as e:
            error_msg = f"Error in emotional intelligence operation: {e}"
            self.logger.error(error_msg)
            return error_msg
    
    def _analyze_mood(self, text: str) -> str:
        """Analyze mood from text input."""
        if not text:
            return "Text is required to analyze mood"
        
        text_lower = text.lower()
        detected_emotions = {}
        
        # Detect emotions using keyword patterns
        for emotion, keywords in self.emotion_patterns.items():
            score = 0
            matched_words = []
            
            for keyword in keywords:
                # Count occurrences with word boundaries
                pattern = r'\b' + re.escape(keyword) + r'\b'
                matches = len(re.findall(pattern, text_lower))
                if matches > 0:
                    score += matches
                    matched_words.append(keyword)
            
            if score > 0:
                detected_emotions[emotion] = {
                    "score": score,
                    "words": matched_words
                }
        
        # Determine primary emotion
        if detected_emotions:
            primary_emotion = max(detected_emotions.items(), key=lambda x: x[1]["score"])
            emotion_name = primary_emotion[0]
            emotion_score = primary_emotion[1]["score"]
            
            # Record emotion
            self._record_emotion(emotion_name, emotion_score, text)
            
            # Generate response
            response = [f"🎭 Mood analysis: {emotion_name} (intensity: {min(emotion_score * 2, 10)}/10)"]
            
            # Add supportive response
            if emotion_name in self.supportive_responses:
                import random
                support = random.choice(self.supportive_responses[emotion_name])
                response.append(f"\n💝 {support}")
            
            # Add other detected emotions
            other_emotions = [k for k in detected_emotions.keys() if k != emotion_name]
            if other_emotions:
                response.append(f"\n📊 Also noticed: {', '.join(other_emotions)}")
            
            return "\n".join(response)
        else:
            return "😐 Couldn't determine a specific mood from the text. How are you feeling?"
    
    def _provide_emotional_support(self, mood: str, intensity: int = 5, context: str = None) -> str:
        """Provide emotional support based on mood."""
        if not mood:
            return "Tell me how you're feeling?"
        
        mood = mood.lower().strip()
        
        # Record the emotion
        self._record_emotion(mood, intensity, context)
        
        # Generate supportive response
        responses = []
        
        # Acknowledge the emotion
        responses.append(f"😔 I understand you're feeling {mood}")
        if intensity >= 7:
            responses.append("That's quite intense.")
        
        # Provide support based on emotion type
        if mood in self.supportive_responses:
            import random
            support = random.choice(self.supportive_responses[mood])
            responses.append(f"\n💙 {support}")
        else:
            # Generic support
            responses.append(f"\n💙 I'm here to support you. Want to talk about it?")
        
        # Add context-specific support
        if context:
            responses.append(f"\n🤝 I understand this is related to: {context}")
        
        # Check for patterns and provide additional support
        recent_moods = self._get_recent_moods(days=3)
        negative_moods = ["sad", "angry", "anxious", "lonely", "tired", "confused"]
        
        if mood in negative_moods:
            recent_negative = [m for m in recent_moods if m["emotion"] in negative_moods]
            if len(recent_negative) >= 3:
                responses.append(f"\n🌟 I notice the last few days have been tough. Remember, you have the strength to get through this!")
        
        return "\n".join(responses)
    
    def _record_emotion(self, emotion: str, intensity: int, context: str = None):
        """Record an emotion in history."""
        emotion_entry = {
            "emotion": emotion,
            "intensity": intensity,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        
        self.emotion_data["emotion_history"].append(emotion_entry)
        
        # Update current mood
        self.emotion_data["interaction_context"]["current_mood"] = emotion
        self.emotion_data["interaction_context"]["last_mood_change"] = emotion_entry["timestamp"]
        
        # Update counters
        negative_moods = ["sad", "angry", "anxious", "lonely", "tired", "confused"]
        if emotion in negative_moods:
            self.emotion_data["interaction_context"]["total_negative_interactions"] += 1
        else:
            self.emotion_data["interaction_context"]["total_positive_interactions"] += 1
        
        # Keep only last 100 emotions
        if len(self.emotion_data["emotion_history"]) > 100:
            self.emotion_data["emotion_history"] = self.emotion_data["emotion_history"][-100:]
        
        self._save_emotion_data()
    
    def _get_recent_moods(self, days: int = 7) -> List[Dict]:
        """Get recent mood entries."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return [
            entry for entry in self.emotion_data["emotion_history"]
            if datetime.fromisoformat(entry["timestamp"]) >= cutoff_date
        ]
    
    def _get_mood_history(self) -> str:
        """Get mood history summary."""
        recent_moods = self._get_recent_moods(days=7)
        
        if not recent_moods:
            return "📊 I don't have mood data yet. How are you doing?"
        
        # Analyze mood patterns
        mood_counts = {}
        total_intensity = 0
        
        for entry in recent_moods:
            emotion = entry["emotion"]
            intensity = entry.get("intensity", 5)
            
            mood_counts[emotion] = mood_counts.get(emotion, 0) + 1
            total_intensity += intensity
        
        avg_intensity = total_intensity / len(recent_moods)
        most_common_mood = max(mood_counts.items(), key=lambda x: x[1])
        
        response = [
            f"📊 MOOD ANALYSIS (last 7 days):",
            f"",
            f"🎭 Entries: {len(recent_moods)}",
            f"😌 Predominant mood: {most_common_mood[0]} ({most_common_mood[1]} times)",
            f"📈 Average intensity: {avg_intensity:.1f}/10",
            f""
        ]
        
        # Show mood distribution
        if len(mood_counts) > 1:
            response.append("📋 Mood distribution:")
            for mood, count in sorted(mood_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(recent_moods)) * 100
                response.append(f"  • {mood}: {count} times ({percentage:.0f}%)")
            response.append("")
        
        # Recent trend
        if len(recent_moods) >= 3:
            recent_3 = recent_moods[-3:]
            positive_moods = ["happy", "excited", "grateful", "confident"]
            recent_positive = sum(1 for m in recent_3 if m["emotion"] in positive_moods)
            
            if recent_positive >= 2:
                response.append("📈 Trend: mood is improving! ✨")
            elif recent_positive == 0:
                response.append("📉 Trend: the last few days have been rough. I'm thinking of you! 💙")
            else:
                response.append("📊 Trend: mixed emotions are normal.")
        
        return "\n".join(response)
    
    def _set_comfort_preference(self, preference_type: str, value: str) -> str:
        """Set comfort preferences."""
        if not preference_type or not value:
            return "You need to specify the preference type and value"
        
        prefs = self.emotion_data["support_preferences"]
        
        preference_type = preference_type.lower()
        
        if preference_type == "style":
            prefs["preferred_response_style"] = value
            self._save_emotion_data()
            return f"✓ Set support style: {value}"
        
        elif preference_type == "comfort_topic":
            if value not in prefs["comfort_topics"]:
                prefs["comfort_topics"].append(value)
                self._save_emotion_data()
                return f"✓ Added comfort topic: {value}"
            else:
                return f"This topic is already in the comfort list"
        
        elif preference_type == "avoid_topic":
            if value not in prefs["avoid_topics"]:
                prefs["avoid_topics"].append(value)
                self._save_emotion_data()
                return f"✓ Will avoid topic: {value}"
            else:
                return f"This topic is already in the avoid list"
        
        else:
            return "Unknown preference type. Available: style, comfort_topic, avoid_topic"
    
    def _emotional_check_in(self) -> str:
        """Proactive emotional check-in."""
        context = self.emotion_data["interaction_context"]
        current_mood = context.get("current_mood", "unknown")
        
        # Check if it's been a while since last interaction
        last_change = context.get("last_mood_change")
        if last_change:
            last_time = datetime.fromisoformat(last_change)
            hours_since = (datetime.now() - last_time).total_seconds() / 3600
            
            if hours_since > 24:
                return "🌟 Hey! It's been a while. How are you? How's your mood?"
        
        # Recent mood analysis
        recent_moods = self._get_recent_moods(days=2)
        if recent_moods:
            negative_moods = ["sad", "angry", "anxious", "lonely", "tired", "confused"]
            recent_negative = [m for m in recent_moods if m["emotion"] in negative_moods]
            
            if len(recent_negative) >= 2:
                return "💙 I noticed the last days weren't easy. How are you now? Want to talk?"
        
        # General check-in based on current mood
        if current_mood in ["sad", "angry", "anxious"]:
            return f"💭 How are you after our last chat? I hope your mood has improved."
        elif current_mood in ["happy", "excited", "confident"]:
            return f"😊 I was happy to see you in a good mood! How are you now?"
        else:
            return "👋 How are you? Tell me what's on your mind!"


def get_emotional_intelligence_tool() -> StructuredTool:
    """Get emotional intelligence tool instance."""
    tool = EmotionalIntelligenceTool()
    return tool.get_tool()
