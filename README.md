
<img width="1024" height="367" alt="Anor" src="https://github.com/user-attachments/assets/a799392a-b7f2-400c-830e-2b3e8e7550ae" />

# Anorix AI Agent

An interactive AI agent with memory system that uses Ollama LLM to process queries while preserving conversation context.

## Installation

### Requirements
- Python 3.9+
- Ollama server (http://localhost:11434)
- Ollama models (gpt-oss:20b and others)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Start Ollama
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull gpt-oss:20b
ollama serve
```

## Launch

### Interactive Shell
```bash
python main.py
```

### Launch Parameters
```bash
python main.py --model gpt-oss:20b --verbose --new-session
```

- `--model`: Ollama model name
- `--verbose`: Verbose output
- `--new-session`: Start new session instead of continuing the last one

## Architecture

### Main Components

- **OllamaAgent**: Agent core with Ollama LLM integration
- **MemoryManager**: Three-layer memory system
  - Short-term: Active conversation
  - Long-term: Conversation database
  - Smart: Vector search through documents
- **ToolManager**: Tool and RAG management
- **Tools**: search, profile, facts, RAG, files, calendar, reminders, tasks, goals, habits

### Memory System

Automatically saves:
- Conversations between sessions
- User profile
- Important facts
- Documents for search

### Tools

- `memory_search`: Search through past conversations
- `profile_tool`: Manage user profile
- `facts_save`: Save facts
- `conversation_history`: Conversation history
- `rag_management`: RAG operations
- `file_manager`: File read/write and directory operations (structured)
- `web_search`: Internet search
- `arxiv`: Work with scientific articles
- `datetime_tool`: Date and time operations

Calendar and productivity suite (structured tools with persistence):
- `calendar_create`, `calendar_list`, `calendar_search`, `calendar_get`, `calendar_update`, `calendar_delete`
- `reminder_create`, `reminder_list`, `reminder_get`, `reminder_update`, `reminder_delete`
- `task_create`, `task_list`, `task_get`, `task_update`, `task_delete`, `task_complete`, `task_reopen`
- `goal_create`, `goal_list`, `goal_get`, `goal_update`, `goal_delete`, `goal_progress`, `goal_complete`
- `habit_create`, `habit_list`, `habit_get`, `habit_update`, `habit_delete`, `habit_log`, `habit_unlog`, `habit_streak`, `habit_stats`

## Configuration

- `config/memory_config.yaml`: Memory settings
- `data/conversations.db`: Conversation database
- `data/vector_db`: Vector database for RAG

## Usage

### Commands in Interactive Shell
- `help`: Show help
- `memory`: Memory statistics
- `profile`: Show profile
- `search <text>`: Search in memory
- `new_session`: New session
- `clear`: Clear screen
- `quit`: Exit

### Programmatic Interface
```python
from agent import OllamaAgent

agent = OllamaAgent(model_name="gpt-oss:20b")
response = agent.run("Your query")
```

### Calendar Examples
The agent can map natural-language requests to structured calendar tools.

```python
# Create a calendar event (the LLM will compute end time for 1 hour)
agent.run("Create a team meeting on 2025-09-23 at 10:00 for 1 hour in Zoom")

# List today's/tomorrow's events
agent.run("What do I have today?")
agent.run("Show me appointments for tomorrow")

# Search and update
agent.run("Search for 'meeting' in my calendar")
agent.run("Move the dentist appointment to 14:30")
```

### Reminder Examples
```python
# Create a reminder
agent.run("Remind me tomorrow at 09:00 to call John. Priority high")

# List, update, delete
agent.run("List my reminders for this week")
agent.run("Mark reminder 2 as done")
agent.run("Delete reminder 5")
```

### Task Manager Examples
```python
# Create and list tasks
agent.run("Create a task 'Prepare Q3 report' due 2025-09-25 with tags finance, q3")
agent.run("Show pending tasks with high priority")

# Update, complete, reopen
agent.run("Update task 3 — change due date to 2025-09-26")
agent.run("Complete task 3")
agent.run("Reopen task 3")
```

### Goal Tracker Examples
```python
# Create and track goals
agent.run("Create a goal 'Learn Rust' with target 2025-12-31, priority high, progress 10%")
agent.run("Set goal 2 progress to 55%")
agent.run("Complete goal 2")
```

### Habit Tracker Examples
```python
# Create and log habits
agent.run("Create a habit 'Drink water' with reminder 09:00 and target streak 21 days")
agent.run("Log habit 2 today")
agent.run("Show current streak for habit 2")
agent.run("Show habit 2 stats for September 2025")
```

## Project Structure

```
anorix/
├── agent/                 # Agent core
│   ├── core.py           # Main agent class
│   ├── memory/           # Memory system
│   ├── rag/              # RAG components
│   ├── tools/            # Tools
│   └── tool_manager.py   # Tool management
├── config/               # Configuration
├── data/                 # Local data and databases (gitignored)
├── examples/             # Usage examples
├── main.py              # Interactive shell
└── requirements.txt     # Dependencies
```
