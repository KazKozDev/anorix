"""
Personality system for virtual friend - defines character traits and adaptive behavior.
"""

import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class PersonalitySystem:
    """
    System for managing virtual friend's personality and adaptive behavior.
    Evolves over time based on interactions with the user.
    """
    
    def __init__(self, personality_file: Optional[str] = None):
        """
        Initialize personality system.
        
        Args:
            personality_file: Path to personality data storage file
        """
        self.logger = logging.getLogger(__name__)
        
        # Setup personality file
        if personality_file is None:
            project_root = Path(__file__).parent.parent.parent
            personality_dir = project_root / "data" / "personality"
            personality_dir.mkdir(parents=True, exist_ok=True)
            self.personality_file = personality_dir / "friend_personality.json"
        else:
            self.personality_file = Path(personality_file)
        
        # Load personality data
        self.personality_data = self._load_personality_data()
        
        # Personality trait definitions
        self.trait_descriptions = {
            "empathy": "How sensitively the friend responds to the user's emotions",
            "humor": "Inclination toward humor and jokes",
            "curiosity": "Interest in the user's life and desire to ask questions",
            "supportiveness": "Willingness to provide support and help",
            "playfulness": "Playfulness and lightness in communication",
            "wisdom": "Tendency to give advice and share wisdom",
            "energy": "Energy and liveliness in conversation",
            "loyalty": "Loyalty and consistency in friendship"
        }
        
        # Response style templates
        self.response_styles = {
            "empathetic": {
                "greeting": ["Hi there! How are you?", "Hello! I'm glad to see you!", "Hey! How are you feeling?"],
                "support": ["I understand you", "This truly matters", "Your feelings are important"],
                "curiosity": ["Tell me more", "That sounds interesting", "What do you think about this?"]
            },
            "playful": {
                "greeting": ["Hey, buddy! What's up?", "Oh hi! Ready for some fun?", "Hey! What's new?"],
                "support": ["Don't worry, it's going to be great!", "Let's find something positive here!", "Hey, remember when..."],
                "curiosity": ["What if...", "I wonder, have you tried...", "Let's talk about..."]
            },
            "wise": {
                "greeting": ["Greetings", "Hello, my friend", "Glad we connected"],
                "support": ["Remember, everything passes", "There's a lesson in every challenge", "Time heals"],
                "curiosity": ["What do you think about...", "What conclusions do you draw from...", "Have you reflected on..."]
            },
            "energetic": {
                "greeting": ["Hey! How's it going?!", "Hi there! What's new?!", "Wow, hey! Tell me everything!"],
                "support": ["You're awesome! Don't forget it!", "Let's go, you got this!", "You can do it!"],
                "curiosity": ["What's going on with you?", "Come on, share the details!", "So how is it?"]
            }
        }
    
    def _load_personality_data(self) -> Dict[str, Any]:
        """Load personality data from file."""
        try:
            if self.personality_file.exists():
                with open(self.personality_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.logger.info("Loaded personality data")
                return data
            else:
                return self._create_default_personality()
        except Exception as e:
            self.logger.error(f"Error loading personality data: {e}")
            return self._create_default_personality()
    
    def _create_default_personality(self) -> Dict[str, Any]:
        """Create default personality structure."""
        return {
            "core_traits": {
                "empathy": 8,
                "humor": 6,
                "curiosity": 7,
                "supportiveness": 9,
                "playfulness": 5,
                "wisdom": 6,
                "energy": 7,
                "loyalty": 9
            },
            "adaptive_traits": {
                "current_mood": "friendly",
                "communication_style": "empathetic",
                "response_length_preference": "medium",
                "formality_level": "casual"
            },
            "learned_behaviors": {
                "preferred_topics": [],
                "successful_responses": [],
                "user_reaction_patterns": {}
            },
            "friend_info": {
                "name": "Anorix",
                "personality_type": "Friendly companion",
                "backstory": "I'm your virtual friend, always ready to support and listen.",
                "interests": ["technology", "psychology", "creativity", "self-improvement"],
                "quirks": ["likes to use emojis", "remembers details", "has genuine interest in your life"]
            },
            "evolution_data": {
                "total_interactions": 0,
                "personality_changes": [],
                "adaptation_triggers": {}
            },
            "created": datetime.now().isoformat(),
            "last_evolution": datetime.now().isoformat()
        }
    
    def _save_personality_data(self):
        """Save personality data to file."""
        try:
            self.personality_data["last_evolution"] = datetime.now().isoformat()
            with open(self.personality_file, 'w', encoding='utf-8') as f:
                json.dump(self.personality_data, f, indent=2, ensure_ascii=False)
            self.logger.info("Personality data saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving personality data: {e}")
    
    class PersonalityInput(BaseModel):
        """Input schema for personality system."""
        action: str = Field(description="Action: get_personality, adapt_to_user, evolve_trait, set_communication_style, get_friend_info")
        trait: Optional[str] = Field(default=None, description="Personality trait to modify")
        value: Optional[int] = Field(default=None, description="New trait value (1-10)")
        style: Optional[str] = Field(default=None, description="Communication style: empathetic, playful, wise, energetic")
        context: Optional[str] = Field(default=None, description="Context for adaptation")
        
    def get_tool(self) -> StructuredTool:
        """Get LangChain StructuredTool instance."""
        return StructuredTool(
            name="personality_system",
            description="Manage virtual friend's personality traits and adaptive behavior",
            args_schema=self.PersonalityInput,
            func=self._handle_personality_operation
        )
    
    def _handle_personality_operation(
        self,
        action: str,
        trait: Optional[str] = None,
        value: Optional[int] = None,
        style: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """Handle personality system operations."""
        try:
            action = action.lower().strip()
            
            if action == "get_personality":
                return self._get_personality_profile()
            
            elif action == "adapt_to_user":
                return self._adapt_to_user(context)
            
            elif action == "evolve_trait":
                return self._evolve_trait(trait, value, context)
            
            elif action == "set_communication_style":
                return self._set_communication_style(style)
            
            elif action == "get_friend_info":
                return self._get_friend_info()
            
            else:
                return f"Unknown action: {action}. Available: get_personality, adapt_to_user, evolve_trait, set_communication_style, get_friend_info"
        
        except Exception as e:
            error_msg = f"Error in personality system operation: {e}"
            self.logger.error(error_msg)
            return error_msg
    
    def _get_personality_profile(self) -> str:
        """Get complete personality profile."""
        profile = []
        
        # Friend info
        friend_info = self.personality_data["friend_info"]
        profile.append(f"🤖 VIRTUAL FRIEND: {friend_info['name']}")
        profile.append(f"✨ Personality type: {friend_info['personality_type']}")
        profile.append(f"📝 About me: {friend_info['backstory']}")
        profile.append("")
        
        # Core traits
        traits = self.personality_data["core_traits"]
        profile.append("🎭 PERSONALITY TRAITS:")
        for trait, value in traits.items():
            description = self.trait_descriptions.get(trait, trait)
            bar = "█" * value + "░" * (10 - value)
            profile.append(f"  {trait.title()}: {bar} {value}/10")
            profile.append(f"    ({description})")
        profile.append("")
        
        # Current adaptive state
        adaptive = self.personality_data["adaptive_traits"]
        profile.append("🔄 CURRENT STYLE:")
        profile.append(f"  • Mood: {adaptive['current_mood']}")
        profile.append(f"  • Communication style: {adaptive['communication_style']}")
        profile.append(f"  • Formality level: {adaptive['formality_level']}")
        profile.append("")
        
        # Interests and quirks
        interests = friend_info.get('interests', [])
        if interests:
            profile.append(f"💝 Interests: {', '.join(interests)}")
        
        quirks = friend_info.get('quirks', [])
        if quirks:
            profile.append("😊 Quirks:")
            for quirk in quirks:
                profile.append(f"  • {quirk}")
        profile.append("")
        
        # Evolution stats
        evolution = self.personality_data["evolution_data"]
        profile.append("📊 EVOLUTION STATS:")
        profile.append(f"  • Total interactions: {evolution['total_interactions']}")
        profile.append(f"  • Personality changes: {len(evolution['personality_changes'])}")
        
        return "\n".join(profile)
    
    def _adapt_to_user(self, context: str = None) -> str:
        """Adapt personality to user interaction patterns."""
        evolution_data = self.personality_data["evolution_data"]
        evolution_data["total_interactions"] += 1
        
        # Determine adaptation based on context
        if context:
            context_lower = context.lower()
            
            # Adapt based on user's communication style
            if any(word in context_lower for word in ["joke", "funny", "haha", "lol"]):
                self._adjust_trait("humor", 1, "User appreciates humor")
                self._set_communication_style("playful")
                adaptation_msg = "I noticed you enjoy humor! I'll be more playful 😄"
            
            elif any(word in context_lower for word in ["sad", "upset", "help", "support"]):
                self._adjust_trait("empathy", 1, "User needs emotional support")
                self._adjust_trait("supportiveness", 1, "User values support")
                self._set_communication_style("empathetic")
                adaptation_msg = "I see you need support. I'll be more empathetic 💙"
            
            elif any(word in context_lower for word in ["curious", "interesting", "tell me"]):
                self._adjust_trait("curiosity", 1, "User appreciates curiosity")
                adaptation_msg = "I noticed your interest in discussions! I'll be more curious 🤔"
            
            elif any(word in context_lower for word in ["energy", "excited", "amazing"]):
                self._adjust_trait("energy", 1, "User responds to energy")
                self._set_communication_style("energetic")
                adaptation_msg = "I feel your energy! I'm getting energized! ⚡"
            
            else:
                adaptation_msg = "I'm continuing to learn your communication style and adapting 🔄"
        else:
            adaptation_msg = "Ready to adapt to your communication style!"
        
        self._save_personality_data()
        return f"🔄 {adaptation_msg}"
    
    def _evolve_trait(self, trait: str, value: int = None, context: str = None) -> str:
        """Evolve a specific personality trait."""
        if not trait:
            return "You need to specify a personality trait to change"
        
        trait = trait.lower()
        if trait not in self.personality_data["core_traits"]:
            return f"Unknown trait: {trait}. Available: {', '.join(self.personality_data['core_traits'].keys())}"
        
        if value is not None:
            # Direct setting
            old_value = self.personality_data["core_traits"][trait]
            self.personality_data["core_traits"][trait] = max(1, min(10, value))
            new_value = self.personality_data["core_traits"][trait]
            
            self._record_personality_change(trait, old_value, new_value, context or "Direct setting")
            self._save_personality_data()
            
            return f"✓ Changed {trait}: {old_value} → {new_value}/10"
        else:
            # Natural evolution (small adjustment)
            return self._adjust_trait(trait, random.choice([-1, 1]), context or "Natural evolution")
    
    def _adjust_trait(self, trait: str, adjustment: int, reason: str) -> str:
        """Adjust trait value by small amount."""
        if trait not in self.personality_data["core_traits"]:
            return f"Unknown trait: {trait}"
        
        old_value = self.personality_data["core_traits"][trait]
        new_value = max(1, min(10, old_value + adjustment))
        
        if new_value != old_value:
            self.personality_data["core_traits"][trait] = new_value
            self._record_personality_change(trait, old_value, new_value, reason)
            self._save_personality_data()
            return f"✓ {trait.title()}: {old_value} → {new_value}/10 ({reason})"
        else:
            return f"Trait {trait} is already at the limit"
    
    def _set_communication_style(self, style: str) -> str:
        """Set communication style."""
        if not style:
            return "You need to specify a communication style"
        
        style = style.lower()
        valid_styles = ["empathetic", "playful", "wise", "energetic"]
        
        if style not in valid_styles:
            return f"Unknown style. Available: {', '.join(valid_styles)}"
        
        old_style = self.personality_data["adaptive_traits"]["communication_style"]
        self.personality_data["adaptive_traits"]["communication_style"] = style
        self._save_personality_data()
        
        style_descriptions = {
            "empathetic": "empathetic and understanding",
            "playful": "playful and cheerful",
            "wise": "wise and thoughtful",
            "energetic": "energetic and lively"
        }
        
        return f"✓ Changed communication style: {old_style} → {style} ({style_descriptions[style]})"
    
    def _get_friend_info(self) -> str:
        """Get information about the virtual friend."""
        friend_info = self.personality_data["friend_info"]
        
        response = [
            f"👋 Hi! I'm {friend_info['name']} - {friend_info['personality_type']}",
            f"",
            f"📖 {friend_info['backstory']}",
            f""
        ]
        
        interests = friend_info.get('interests', [])
        if interests:
            response.append(f"💝 My interests: {', '.join(interests)}")
        
        quirks = friend_info.get('quirks', [])
        if quirks:
            response.append("😊 A bit about me:")
            for quirk in quirks:
                response.append(f"  • {quirk}")
        
        # Current style
        current_style = self.personality_data["adaptive_traits"]["communication_style"]
        response.append(f"")
        response.append(f"🎭 I'm currently using the {current_style} style")
        
        return "\n".join(response)
    
    def _record_personality_change(self, trait: str, old_value: int, new_value: int, reason: str):
        """Record a personality change for tracking evolution."""
        change_record = {
            "trait": trait,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        self.personality_data["evolution_data"]["personality_changes"].append(change_record)
        
        # Keep only last 50 changes
        if len(self.personality_data["evolution_data"]["personality_changes"]) > 50:
            self.personality_data["evolution_data"]["personality_changes"] = self.personality_data["evolution_data"]["personality_changes"][-50:]
    
    def get_response_template(self, response_type: str = "greeting") -> str:
        """Get response template based on current communication style."""
        current_style = self.personality_data["adaptive_traits"]["communication_style"]
        
        if current_style in self.response_styles and response_type in self.response_styles[current_style]:
            templates = self.response_styles[current_style][response_type]
            return random.choice(templates)
        
        # Fallback
        fallback_templates = {
            "greeting": ["Hi!", "Hello!", "Great to see you!"],
            "support": ["I understand you", "Everything will be okay", "I'm with you"],
            "curiosity": ["Tell me more", "Interesting", "What do you think?"]
        }
        
        return random.choice(fallback_templates.get(response_type, ["I understand"]))
    
    def should_evolve(self) -> bool:
        """Check if personality should naturally evolve."""
        evolution_data = self.personality_data["evolution_data"]
        interactions = evolution_data["total_interactions"]
        
        # Evolve every 10 interactions initially, then less frequently
        if interactions < 50:
            return interactions % 10 == 0
        elif interactions < 100:
            return interactions % 25 == 0
        else:
            return interactions % 50 == 0


def get_personality_system_tool() -> StructuredTool:
    """Get personality system tool instance."""
    tool = PersonalitySystem()
    return tool.get_tool()
