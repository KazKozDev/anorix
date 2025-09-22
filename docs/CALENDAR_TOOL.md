# CalendarTool Documentation

## Overview
CalendarTool is a comprehensive calendar management tool that allows users to create, manage, and search calendar events. It supports full CRUD operations and integrates with the agent's memory system for persistence.

## Features
- ✅ Create calendar events with title, description, time, location, category, and priority
- ✅ Retrieve specific events by ID
- ✅ Update existing events
- ✅ Delete events
- ✅ Search events by text content
- ✅ List events by date or date range
- ✅ Automatic event persistence through memory system
- ✅ Priority-based event organization
- ✅ Category-based event filtering

## Usage Examples

### Creating Events
```
Create a team meeting on 2024-01-20 at 10:00 for 1 hour
Create a dentist appointment for tomorrow at 2:00 PM
Schedule a call with John at Conference Room A
```

### Searching Events
```
Show me all appointments for tomorrow
Find events containing "meeting"
Search for "doctor" in my calendar
```

### Managing Events
```
Change the dentist appointment to 2:00 PM
Update the meeting location to Conference Room B
Delete the reminder for paying bills
```

### Listing Events
```
Show me all events for January 20, 2024
List all work meetings this week
What do I have scheduled from Jan 20 to Jan 25?
```

## Event Properties
- **Title**: Required event name/summary
- **Description**: Optional detailed description
- **Start Time**: Required start date/time (YYYY-MM-DD HH:MM format)
- **End Time**: Required end date/time (YYYY-MM-DD HH:MM format)
- **Location**: Optional location information
- **Category**: Event category (work, personal, health, etc.)
- **Priority**: Event priority (low, normal, high, urgent)

## Supported Formats
- Date/Time: `YYYY-MM-DD HH:MM`, `YYYY-MM-DD`, `DD-MM-YYYY HH:MM`
- Categories: Any text-based category
- Priorities: low, normal, high, urgent
- Search: Full-text search across title, description, location, and category

## Integration
CalendarTool integrates seamlessly with the agent's natural language processing and can understand various ways users might express calendar operations. It also works with the DateTimeTool for complex temporal queries.
