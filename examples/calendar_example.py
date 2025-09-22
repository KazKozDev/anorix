#!/usr/bin/env python3
"""
Example usage of CalendarTool.
Demonstrates how to use the calendar tool for event management.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.tools.calendar_tool import CalendarTool


def demonstrate_calendar_tool():
    """Demonstrate CalendarTool functionality."""
    print("🗓️ CalendarTool Demonstration")
    print("=" * 50)

    # Create calendar tool
    calendar = CalendarTool()

    try:
        # Example 1: Create a work meeting
        print("\n📅 Example 1: Creating a work meeting")
        result = calendar._run(
            action="create",
            title="Team Standup",
            description="Daily team synchronization meeting",
            start_time="2024-01-20 09:00",
            end_time="2024-01-20 09:30",
            location="Virtual (Zoom)",
            category="work",
            priority="normal"
        )
        print(result)

        # Example 2: Create a personal appointment
        print("\n📅 Example 2: Creating a personal appointment")
        result = calendar._run(
            action="create",
            title="Dentist Appointment",
            description="Regular dental checkup",
            start_time="2024-01-22 14:00",
            end_time="2024-01-22 15:00",
            location="Downtown Dental Clinic",
            category="health",
            priority="high"
        )
        print(result)

        # Example 3: Create a reminder
        print("\n📅 Example 3: Creating a reminder")
        result = calendar._run(
            action="create",
            title="Pay utility bills",
            description="Monthly electricity and internet bills",
            start_time="2024-01-25 10:00",
            end_time="2024-01-25 10:15",
            category="personal",
            priority="urgent"
        )
        print(result)

        # Example 4: List all events
        print("\n📋 Example 4: Listing all events")
        result = calendar._run(action="list")
        print(result)

        # Example 5: Search for events
        print("\n🔍 Example 5: Searching for 'appointment'")
        result = calendar._run(action="search", search_text="appointment")
        print(result)

        # Example 6: List events for a specific date
        print("\n📅 Example 6: Listing events for January 20, 2024")
        result = calendar._run(action="list", date="2024-01-20")
        print(result)

        # Example 7: Update an event
        print("\n✏️ Example 7: Updating the dentist appointment")
        event_id = "2"  # ID of the dentist appointment
        result = calendar._run(
            action="update",
            event_id=event_id,
            location="Premium Dental Center",
            priority="normal"
        )
        print(result)

        # Example 8: Get specific event
        print("\n👀 Example 8: Getting the updated appointment")
        result = calendar._run(action="get", event_id=event_id)
        print(result)

        # Example 9: List events by date range
        print("\n📅 Example 9: Listing events from Jan 20 to Jan 25, 2024")
        result = calendar._run(
            action="list",
            start_date="2024-01-20",
            end_date="2024-01-25"
        )
        print(result)

        # Example 10: Delete a reminder
        print("\n🗑️ Example 10: Deleting the reminder")
        result = calendar._run(action="delete", event_id="3")
        print(result)

        # Final list
        print("\n📋 Final calendar state:")
        result = calendar._run(action="list")
        print(result)

        print("\n🎉 CalendarTool demonstration completed successfully!")
        print("\n💡 Available actions:")
        print("   • create - Create new calendar event")
        print("   • get - Retrieve specific event by ID")
        print("   • update - Update existing event")
        print("   • delete - Delete event by ID")
        print("   • search - Search events by text")
        print("   • list - List events (all or filtered by date/range)")

    except Exception as e:
        print(f"❌ Error in demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demonstrate_calendar_tool()
