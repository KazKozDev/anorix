## Anorix – Local AI Friend & Assistant

Local AI system built with LangChain and Ollama that combines:
- **Conversational friend** with memory and evolving personality
- **Assistant** with LangChain tool architecture (search, code, math, files, APIs)

### Features

- **Voice chat** with WebRTC audio (Whisper STT, Bark TTS)
- **Dictation support** - local transcription into input field
- **RAG system** with document search via vector database
- **Web search** capabilities
- **Personal memory** - remembers preferences and history
- **Comprehensive toolset** (math, code analysis, files, etc.)
- **Long-term memory** with RAG (FAISS / pgvector)
- **LangChain-based** orchestration and tools
- **Fully local deployment**, no external dependencies

### Quick Start

### Install dependencies
```bash
# Full install (with voice features)
pip install -r requirements.txt

```

### Run (2 ways)
```bash
# Web UI (recommended)
./bin/web_server  # open http://127.0.0.1:5000

# CLI chat
./bin/cli_chat
```

**Requirements:** Python 3.8+, Ollama, FFmpeg

### Ollama setup
```bash
ollama pull gpt-oss:20b  # or another compatible model
```

### Architecture

```
User
│
▼
Web UI / CLI 
│
▼
Orchestrator (LangChain)
├── Friend Module (memory + personality)
├── Assistant Module (tools)
├── RAG Store (vector DB)
└── LLM Core (Ollama)
```

### Available Tools

- **Web search** - DuckDuckGo and site-specific
- **Math** - symbolic and numeric calculations
- **Code** - execute Python code
- **Files** - read and analyze documents
- **Time** - work with dates and time
- **RAG** - local knowledge base search 

### Virtual friend

- emotional_intelligence: Mood analysis, support, history.
- personality_system: Traits and communication style management.
- proactive_care: Reminders, check-ins, wellness tips, celebrations.


### License

MIT License - see [LICENSE](LICENSE)


---
If you like this project, please give it a star ⭐

For questions, feedback, or support, reach out to:

[Artem KK](https://www.linkedin.com/in/kazkozdev/) |
