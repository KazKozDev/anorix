#!/usr/bin/env python3
"""
Test script for CalendarTool.
Tests calendar event creation, retrieval, update, and search functionality.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.tools.calendar_tool import CalendarTool, CalendarInput


def test_calendar_tool():
    """Test CalendarTool functionality."""
    print("🗓️ Testing CalendarTool")
    print("=" * 50)

    # Create calendar tool instance
    calendar = CalendarTool()

    try:
        # Test 1: Create event
        print("\n1️⃣ Creating test event...")
        result = calendar._run(
            action="create",
            title="Team Meeting",
            description="Weekly team sync",
            start_time="2024-01-15 10:00",
            end_time="2024-01-15 11:00",
            location="Conference Room A",
            category="work",
            priority="high"
        )
        print(result)

        # Test 2: Create another event
        print("\n2️⃣ Creating second event...")
        result = calendar._run(
            action="create",
            title="Doctor Appointment",
            description="Annual checkup",
            start_time="2024-01-16 14:30",
            end_time="2024-01-16 15:30",
            location="Medical Center",
            category="health",
            priority="normal"
        )
        print(result)

        # Test 3: List all events
        print("\n3️⃣ Listing all events...")
        result = calendar._run(action="list")
        print(result)

        # Test 4: Search events
        print("\n4️⃣ Searching for 'meeting'...")
        result = calendar._run(action="search", search_text="meeting")
        print(result)

        # Test 5: Get specific event
        print("\n5️⃣ Getting event by ID...")
        # Get the first event ID from the events dict
        event_id = list(calendar.events.keys())[0]
        result = calendar._run(action="get", event_id=event_id)
        print(result)

        # Test 6: Update event
        print("\n6️⃣ Updating event...")
        result = calendar._run(
            action="update",
            event_id=event_id,
            title="Updated Team Meeting",
            location="Conference Room B"
        )
        print(result)

        # Test 7: List events for specific date
        print("\n7️⃣ Listing events for 2024-01-15...")
        result = calendar._run(action="list", date="2024-01-15")
        print(result)

        # Test 8: Delete event
        print("\n8️⃣ Deleting event...")
        result = calendar._run(action="delete", event_id=event_id)
        print(result)

        print("\n✅ CalendarTool test completed successfully!")

    except Exception as e:
        print(f"❌ Error testing CalendarTool: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_calendar_tool()
