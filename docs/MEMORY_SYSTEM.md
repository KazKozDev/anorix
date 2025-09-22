# 🧠 Three-Layer Memory System

## Overview

The LangChain Ollama Agent now includes a sophisticated three-layer memory system that enables persistent conversation memory, user profiling, fact storage, and semantic search capabilities.

## Architecture

### 1. 🧠 Short-term Memory (RAM)
- **Purpose**: Current conversation context
- **Storage**: In-memory buffer
- **Capacity**: 10 messages (configurable)
- **Use case**: Understanding "here and now" context

### 2. 💾 Long-term Memory (SQL Database)
- **Purpose**: Persistent structured data storage
- **Storage**: SQLite database (`data/conversations.db`)
- **Contents**: All conversations, user profile, facts, statistics
- **Use case**: Reliable long-term storage and structured queries

### 3. 🔍 Smart Memory (Vector Database)
- **Purpose**: Semantic search capabilities
- **Storage**: ChromaDB (`data/vector_db/`)
- **Contents**: Conversation embeddings for similarity search
- **Use case**: Finding related conversations by meaning, not just keywords

## Memory Tools

### 🔍 MemorySearchTool
Search through conversation history using semantic or text search.

```python
# Usage in conversation
"Search for our previous discussion about Python programming"
```

**Parameters**:
- `query`: Search query
- `method`: "semantic", "text", or "both"
- `limit`: Maximum results (default: 5)

### 👤 ProfileTool
Manage user profile information and preferences.

```python
# Get profile
agent.run("Get my profile information")

# Update profile
agent.run("Update my profile: name = John, language = Python")
```

**Actions**:
- `get`: Retrieve full profile
- `update`: Modify profile fields
- `summary`: Get profile overview

### 📝 FactsSaveTool
Save and retrieve important facts and knowledge.

```python
# Save a fact
agent.run("Save this fact: category=programming, fact='Python is great for data science'")

# Get facts
agent.run("Show me all facts about programming")
```

**Features**:
- Categorized fact storage
- Confidence levels (0.0-1.0)
- Source tracking
- Fact retrieval by category

### 📜 ConversationHistoryTool
View conversation history from specific time periods.

```python
# Get recent history
agent.run("Show me our conversation history from the last 3 days")

# Filter by role
agent.run("Show me only my messages from today")
```

**Filters**:
- Time period (days)
- Session ID
- Message role (user/assistant/system)
- Result limit

## Configuration

### Memory System Config (`config/memory_config.yaml`)

```yaml
memory:
  enabled: true

  short_term:
    max_messages: 10
    auto_context: true

  long_term:
    db_path: "data/conversations.db"
    auto_save: true

  smart_memory:
    enabled: true
    db_path: "data/vector_db"
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"

memory_tools:
  enabled: true
  tools: [memory_search, profile_tool, facts_save, conversation_history]
```

## Usage Examples

### Basic Usage

```python
from agent import OllamaAgent

# Initialize with memory system
agent = OllamaAgent(
    model_name="gpt-oss:20b",
    memory_config_path="config/memory_config.yaml"
)

# The agent automatically saves conversations and can reference them
response = agent.run("Hello, I'm working on a Python project")
response = agent.run("What was I just working on?")  # Will remember Python project
```

### Advanced Memory Operations

```python
# Search previous conversations
results = agent.search_memories("Python project", method="semantic", limit=5)

# Get user profile
profile = agent.get_user_profile()

# Save important facts
agent.save_fact("projects", "Working on AI chatbot", "conversation", 0.9)

# Get conversation history
history = agent.memory_manager.get_conversation_history(days=7)
```

### Memory Statistics

```python
# Get comprehensive memory stats
stats = agent.get_memory_stats()

print(f"Short-term: {stats['short_term']['current_messages']} messages")
print(f"Long-term: {stats['long_term']['conversations_count']} total conversations")
print(f"Smart memory: {stats['smart_memory']['total_documents']} indexed documents")
```

## Data Storage

### Directory Structure
```
data/
├── conversations.db          # SQL database
├── vector_db/               # ChromaDB vector storage
│   ├── chroma.sqlite3
│   └── ...
└── README.md
```

### Database Schema

**Conversations Table**:
- id, session_id, role, content, timestamp, metadata

**User Profile Table**:
- key, value, updated_at

**Facts Table**:
- id, category, fact, source, confidence, created_at

**Statistics Table**:
- id, metric_name, metric_value, date, metadata

## Integration with Existing Agent

The memory system is seamlessly integrated with the existing LangChain agent:

1. **Automatic Message Storage**: All conversations are automatically saved to all three memory layers
2. **Tool Integration**: Memory tools are automatically loaded when memory manager is available
3. **Backward Compatibility**: Existing agent functionality remains unchanged
4. **Optional**: Memory system can be disabled in configuration

## Performance Considerations

### Memory Usage
- **Short-term**: Minimal impact (small in-memory buffer)
- **Long-term**: SQLite is lightweight and efficient
- **Smart memory**: ChromaDB handles large vector collections efficiently

### Configuration Tuning
```yaml
performance:
  cache:
    enabled: true
    max_size_mb: 100
    ttl_seconds: 3600

  batch:
    size: 50
    async_processing: true
```

## Testing

Run the memory system test:

```bash
python test_memory_system.py
```

This will test:
- Memory manager initialization
- All three memory layers
- Memory tools functionality
- Agent integration

## Error Handling

The memory system is designed to be robust:

- **Graceful Degradation**: If memory system fails to initialize, agent continues without memory features
- **Error Logging**: All memory operations are logged for debugging
- **Backup Storage**: Multiple storage layers provide redundancy
- **Recovery**: SQLite database can be repaired if corrupted

## Dependencies

Additional requirements for memory system:

```txt
# Already included in requirements.txt
chromadb==0.4.15
sentence-transformers>=2.6.0
scikit-learn>=1.3.0  # For clustering features
```

## Future Enhancements

Planned features:

1. **Memory Compression**: Automatic old conversation summarization
2. **Privacy Controls**: Encryption and anonymization options
3. **Memory Insights**: Analytics and conversation patterns
4. **Import/Export**: Backup and restore memory data
5. **Distributed Memory**: Multi-agent memory sharing

## Troubleshooting

### Common Issues

1. **ChromaDB Installation Issues**:
   ```bash
   pip install --upgrade chromadb sentence-transformers
   ```

2. **Database Permissions**:
   ```bash
   chmod 664 data/conversations.db
   ```

3. **Memory Tool Not Available**:
   - Check `memory_config.yaml` settings
   - Verify memory manager initialization in logs
   - Ensure all dependencies are installed

### Debug Mode

Enable detailed memory logging:

```yaml
logging:
  level: "DEBUG"
  detailed: true
  log_operations: true
```

## Security and Privacy

### Data Protection
- SQLite database stored locally
- No data sent to external services
- Optional encryption support (future feature)

### Privacy Settings
```yaml
privacy:
  anonymize: false  # Enable to remove PII
  retention_days: 0  # Auto-delete old data (0 = keep forever)
  encrypt_data: false  # Enable encryption at rest
```

---

🎉 The three-layer memory system transforms your agent into a truly intelligent assistant that learns, remembers, and grows smarter with every conversation!