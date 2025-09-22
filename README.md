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
- **Tools**: search, profile, facts, RAG, files

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
- `file_manager`: File management
- `web_search`: Internet search
- `arxiv`: Work with scientific articles
- `calendar_tool`: Calendar and event management
- `datetime_tool`: Date and time operations

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

### Calendar Tool Examples
```python
# Create a calendar event
agent.run("Create a team meeting on 2024-01-20 at 10:00 for 1 hour")

# Search for events
agent.run("Show me all appointments for tomorrow")

# List events by category
agent.run("Show me all work meetings this week")

# Update an event
agent.run("Change the dentist appointment to 2:00 PM")
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
├── data/                 # Data and databases
├── examples/             # Usage examples
├── main.py              # Interactive shell
└── requirements.txt     # Dependencies
```