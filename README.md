<div align="center">
	<img width="330" alt="an" src="https://github.com/user-attachments/assets/088d0699-7337-4f64-bf04-96278867bd06" />
</div><br>

Intelligent local virtual friend & assistant with persistent memory, tool calling, and productivity management built on LangChain and Ollama. 

Anorix AI Agent is designed for those seeking a reliable virtual friend and personal assistant that remembers your conversations, understands your needs, and helps with daily life. This project is perfect for people who want an intelligent companion for chatting, planning tasks, and achieving goals — a friend who's always there and never forgets the important moments of your life.
## Features

### Core Capabilities
- **LLM Integration**: Uses Ollama with local models (gpt-oss:20b)
- **Tool Calling**: 16+ specialized tools for various tasks
- **Memory System**: Three-layer persistent memory across sessions
- **Productivity Suite**: Complete calendar, tasks, goals, and habits management

### Memory Architecture
- **Short-term**: Active conversation context
- **Long-term**: SQLite database for conversation history
- **Smart Memory**: Vector-based document search with RAG

### Available Tools
- `memory_search` - Search past conversations
- `profile_tool` - User profile management
- `facts_save` - Store important facts
- `conversation_history` - Access chat history
- `file_manager` - File operations (read/write/directory)
- `web_search` - Internet search
- `webscraper` - Web page content extraction
- `arxiv` - Scientific paper search and access
- `calculator` - Mathematical calculations
- `datetime_tool` - Date/time operations
- `http_download` - Download files from URLs

### Productivity Tools
- **Calendar**: Create, search, update events with natural language
- **Reminders**: Set reminders with priorities and due dates
- **Tasks**: Full task management with tags, priorities, completion tracking
- **Goals**: Goal setting with progress tracking and completion
- **Habits**: Habit tracking with streaks and statistics

## Installation

### Prerequisites
- Python 3.9+
- Ollama server

### Quick Setup
```bash
# Clone the repository
git clone https://github.com/KazKozDev/anorix.git
cd anorix

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download model 
ollama pull gpt-oss:20b

# Start Ollama server
ollama serve

# Install Python dependencies
pip install -r requirements.txt

# Run virtual friend
python main.py
```

**Available commands:**
- `help` - Show help
- `memory` - Memory statistics
- `profile` - Show user profile
- `search <text>` - Search in memory
- `new_session` - Start new session
- `clear` - Clear screen
- `quit` - Exit

### Natural Language Examples

**Calendar Management:**
```python
agent.run("Schedule team meeting tomorrow 2-3pm in conference room A")
agent.run("What do I have scheduled for next week?")
agent.run("Move the dentist appointment to Thursday 3pm")
agent.run("Cancel all meetings on Friday")
```

**Task Management:**
```python
agent.run("Add task: finish quarterly report by Friday, high priority")
agent.run("Show me all pending tasks with high priority")
agent.run("Mark task 3 as completed")
agent.run("Update task 5 due date to next Monday")
```

**Goal Tracking:**
```python
agent.run("Create goal: lose 10kg by December, current progress 20%")
agent.run("Update my weight loss goal to 35% complete")
agent.run("Show all goals that are behind schedule")
```

**Habit Tracking:**
```python
agent.run("Track new habit: drink 8 glasses of water daily")
agent.run("Log today's water intake")
agent.run("Show my current streak for exercise habit")
agent.run("Display habit statistics for this month")
```

**Research & Information:**
```python
agent.run("Search for recent papers on machine learning")
agent.run("Download and summarize this PDF: https://example.com/paper.pdf")
agent.run("What's the latest news about AI developments?")
agent.run("Calculate compound interest on $1000 at 5% for 10 years")
```

## Architecture

```
anorix/
├── agent/                           # Core agent system
│   ├── core.py                      # Main OllamaAgent class
│   ├── tool_manager.py              # Tool registration and management
│   ├── callbacks.py                 # LLM callback handlers
│   ├── memory/                      # Memory system
│   │   ├── memory_manager.py
│   │   ├── smart_memory.py
│   │   └── conversation_storage.py
│   ├── rag/                         # Retrieval-Augmented Generation
│   │   ├── rag_manager.py
│   │   ├── document_processor.py
│   │   └── vector_store.py
│   └── tools/                       # Individual tools (16 tools)
├── config/                          # Configuration files
├── data/                            # Data storage (gitignored)
│   ├── conversations.db             # SQLite conversation history
│   ├── vector_db/                   # ChromaDB vector storage
│   └── rag_documents/               # RAG document storage
├── examples/                        # Usage examples
├── tests/                           # Test suite
├── main.py                          # Interactive shell entry point
└── requirements.txt                 # Python dependencies
```

## Memory System Details

### Three-Layer Architecture
1. **Conversation Buffer** - Immediate context for current session
2. **Long-term Storage** - SQLite database with full conversation history
3. **Smart Memory** - Vector embeddings for semantic search across documents

### Memory Features
- Automatic conversation saving between sessions
- User profile extraction and updates
- Important fact detection and storage
- Document indexing for RAG queries
- Semantic search across all stored content


## License

MIT License - see LICENSE file for details.
