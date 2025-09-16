# 🚀 Local Friend Usage Guide

## 📋 Точки входа

У вас есть **3 способа** использовать Local Friend:

### 1. 🖥️ Desktop UI (Рекомендуется)

**Самый удобный способ для ежедневного использования**

```bash
python bin/desktop_ui
```

```
🚀 Starting agent in interactive mode...
✅ Agent loaded successfully. Type 'exit' or 'quit' to end the session.
--------------------------------------------------
👤 You: Hi! How are you?
🤖 Agent: Hi! I'm great! How can I help?
👤 You: Calculate factorial of 5
🤖 Agent: Factorial of 5 = 5! = 5 × 4 × 3 × 2 × 1 = 120
👤 You: exit
👋 Goodbye!
```

### 2. 🛠️ Advanced interactive shell

**For advanced users with management commands and RAG**

```bash
# Basic run
python interactive.py

# With options
python interactive.py --model llama2:7b --quiet

# Test connection to Ollama
python interactive.py --test-connection
```

**Advanced shell features:**
- ✅ Live dialogue with the agent
- ✅ Built-in management commands
- ✅ RAG commands via `/rag`
- ✅ Help via `/help`
- ✅ Command history
- ✅ Autocomplete

### 3. 📋 CLI commands

**Perfect for automation and scripts**

```bash
# Execute a query
python -m agent.cli query "Calculate factorial of 5"

# Work with RAG
python -m agent.cli rag add document.pdf
python -m agent.cli rag add ./docs --directory --patterns "*.py" "*.md"  
python -m agent.cli rag search "machine learning" --k 3 --scores
python -m agent.cli rag info
python -m agent.cli rag clear --force

# Tools information
python -m agent.cli tools
python -m agent.cli tools --json
```

### 4. 🐍 Python API

**For integrating into your Python projects**

```python
from agent import OllamaAgent

# Create the agent
agent = OllamaAgent(
    model_name="gpt-oss:20b",
    temperature=0.1,
    verbose=True
)

# Usage
response = agent.run("Hi! How are you?")
print(response)
```

### 5. 🧪 Examples and demonstrations

**To explore capabilities**

```bash
# Full RAG demonstration
python examples/FINAL_RAG_DEMO.py

# Basic examples
python examples/basic_usage.py

# Custom tools
python examples/custom_tools.py

# RAG examples
python examples/rag_example.py
```

---

## 💬 Interactive commands

### Main commands

| Command | Description |
|---------|----------|
| `/help`, `/h` | Show help |
| `/tools` | List tools |
| `/clear` | Clear agent memory |
| `/quit`, `/exit`, `/q` | Exit |

### RAG commands

| Command | Example | Description |
|---------|--------|----------|
| `/rag info` | `/rag info` | Knowledge base info |
| `/rag add <file>` | `/rag add README.md` | Add file |
| `/rag add_dir <dir>` | `/rag add_dir ./docs` | Add directory |
| `/rag search <query>` | `/rag search Python` | Search the knowledge base |
| `/rag clear` | `/rag clear` | Clear the knowledge base |

---

## 🛠️ CLI commands

### Command structure

```bash
python -m agent.cli [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

### Global options

| Option | Description |
|-------|----------|
| `--model MODEL` | Ollama model (default: gpt-oss:20b) |
| `--verbose`, `-v` | Verbose output |

### Command `query`

```bash
# Query from arguments
python -m agent.cli query "What is the weather today?"

# Query from stdin
echo "Calculate 2 + 2" | python -m agent.cli query
```

### Command `tools`

```bash
# List tools
python -m agent.cli tools

# In JSON format
python -m agent.cli tools --json
```

### Commands `rag`

#### Adding documents

```bash
# Add file
python -m agent.cli rag add document.pdf

# Add directory
python -m agent.cli rag add ./docs --directory

# With file filters
python -m agent.cli rag add ./src --directory --patterns "*.py" "*.md"
```

#### Search

```bash
# Basic search
python -m agent.cli rag search "machine learning"

# With settings
python -m agent.cli rag search "Python programming" --k 5 --scores
```

#### Management

```bash
# Info
python -m agent.cli rag info

# Clear with confirmation
python -m agent.cli rag clear

# Force clear
python -m agent.cli rag clear --force
```

---

## 🐍 Python API

### Basic usage

```python
from agent import OllamaAgent

# Initialization
agent = OllamaAgent()

# Simple query
response = agent.run("Hello!")
print(response)

# Working with RAG
agent.run("Add file document.pdf to the knowledge base")
agent.run("Find information about Python in the documents")
```

### Advanced usage

```python
from agent import OllamaAgent
from agent.rag import RAGRetrievalTool, RAGManagementTool

# Agent configuration
agent = OllamaAgent(
    model_name="llama2:7b",
    temperature=0.2,
    verbose=False
)

# Get tools
tools = agent.list_tools()
descriptions = agent.get_tool_descriptions()

# Working with memory
agent.reset_memory()
history = agent.get_memory()

# Direct work with RAG
rag_tool = RAGRetrievalTool()
management_tool = RAGManagementTool(rag_tool)

# Adding documents
result = management_tool._manage_rag_structured(
    action="add_file",
    path="/path/to/document.pdf"
)

# Search
results = rag_tool._retrieve_documents_structured(
    query="search query",
    k=5,
    with_scores=True
)
```

---

## 🧪 Testing

### Quick tests

```bash
# Check connection to Ollama
python interactive.py --test-connection

# Quick RAG test (without Ollama)
python tests/quick_rag_test.py

# Integration tests
python tests/test_agent_rag_integration.py
```

### Full tests

```bash
# All RAG tests
python tests/test_rag_system.py

# Structured tools tests
python tests/test_structured_rag.py

# All tools
python tests/test_all_tools.py
```

---

## 🔧 Configuration

### Environment variables

```bash
export OLLAMA_HOST="http://localhost:11434"  # Ollama server URL
export RAG_STORE_TYPE="chroma"               # Vector DB type
export RAG_EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
```

### Configuration files

Edit files in `config/`:
- `agent_config.yaml` - agent settings
- `rag_config.yaml` - RAG settings
- `ollama_config.yaml` - Ollama settings

---

## 📚 Typical scenario examples

### 🔍 Exploring documents

```bash
# Interactive
python interactive.py
🤖 Agent> /rag add_dir ./docs
🤖 Agent> Analyze the structure of uploaded documents
🤖 Agent> Find information about RAG systems
```

### 🤖 Automation

```bash
#!/bin/bash
# Document processing script

# Add new documents
python -m agent.cli rag add ./new_docs --directory --patterns "*.pdf" "*.md"

# Get a report
python -m agent.cli query "Create a report on the new documents in the knowledge base"
```

### 🧮 Calculations

```python
# Python script
from agent import OllamaAgent

agent = OllamaAgent()

# Complex calculations
result = agent.run("Compute the integral of x^2 from 0 to 10")
print(result)

# File operations
agent.run("Create a report.txt file with the calculation results")
```

---

## 🆘 Troubleshooting

### Ollama issues

```bash
# Check status
python interactive.py --test-connection

# List models
ollama list

# Restart Ollama
ollama serve
```

### RAG issues

```bash
# Collection info
python -m agent.cli rag info

# Clear and recreate
python -m agent.cli rag clear --force

# RAG system test
python tests/quick_rag_test.py
```

### Logs and debugging

```python
# Enable verbose output
agent = OllamaAgent(verbose=True)

# Or via CLI
python -m agent.cli query "test" --verbose
```

---

🚀 **Choose the right way to use it and start working with the agent!**