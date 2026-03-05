# Bakery Order Assistant — Conversational AI System

A fully local, production-style conversational AI system for bakery order management. Built with FastAPI, WebSocket streaming, and Ollama-powered LLM inference.

## Architecture

```
Web UI (HTML/JS) ↔ FastAPI + WebSocket ↔ Conversation Manager ↔ Ollama (Qwen 2.5 1.5B)
```

### Components

| Component | File | Responsibility |
|---|---|---|
| LLM Engine | `backend/model_engine.py` | Async streaming inference via Ollama |
| Session Store | `backend/session_store.py` | In-memory multi-user session management |
| Conversation Manager | `backend/conversation_manager.py` | Prompt orchestration, context filtering, order export |
| API Server | `backend/main.py` | FastAPI with WebSocket endpoint + static file serving |
| Frontend | `frontend/` | ChatGPT-style web chat interface |

## Business Use-Case

**Bakery Order Assistant** — A conversational chatbot that helps customers place bakery orders. The assistant:
- Only discusses bakery products
- Collects complete order details (item, quantity, weight, etc.)
- Confirms orders before finalizing
- Exports confirmed orders to Excel

### Example Dialogue

```
User: Hi, I'd like to order a cake
Assistant: Welcome! What type of cake would you like? We have chocolate, vanilla, red velvet, and more.
User: Chocolate cake, 2 pounds
Assistant: A 2-pound chocolate cake. Would you like any decorations or message on it?
User: Yes, write "Happy Birthday"
Assistant: Got it! 2-pound chocolate cake with "Happy Birthday" message. Shall I confirm this order?
User: Yes, confirm
Assistant: Order confirmed! Your 2-pound chocolate cake with "Happy Birthday" will be ready.
```

## Model Selection

| Property | Value |
|---|---|
| Model | Qwen 2.5 1.5B |
| Runtime | Ollama |
| Quantization | Default (Q4_K_M) |
| Inference | CPU-only, fully local |

**Why Qwen 2.5 1.5B?**
- Small enough for CPU inference (~1GB RAM)
- Instruction-tuned for conversational tasks
- Good balance of quality vs latency

## Context Management Strategy

- **History trimming**: When conversation exceeds 8 messages, only the last 6 are kept
- **Order state persistence**: Structured order data is always included in the prompt regardless of trim
- **Signal filtering**: Small talk is naturally discarded during trimming, keeping task-relevant turns

## Setup Instructions

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- Qwen 2.5 1.5B model pulled: `ollama pull qwen2.5:1.5b`

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload
```

### Docker Setup

```bash
docker build -t bakery-assistant .
docker run -p 8000:8000 bakery-assistant
```

### Access

- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws/chat

## API Specification

### WebSocket: `/ws/chat`

**Request:**
```json
{"message": "I want to order a chocolate cake"}
```

**Response:** Streamed text tokens, followed by:
```json
{"type": "end"}
```

**Error:**
```json
{"type": "error", "message": "error description"}
```

## Performance Benchmarks

Tested on: 16 GB RAM, 24-thread CPU

| Metric | Result |
|---|---|
| **Single User Response Time** | 3.58s |
| **Single User Tokens/sec** | 8.94 |
| **2 Concurrent Users Avg Response** | 2.48s |
| **3 Concurrent Users Avg Response** | 2.46s |
| **5 Concurrent Users Avg Response** | 2.78s |
| **5 Concurrent Users Max Response** | 2.86s |
| **Process RAM Usage** | ~34 MB |
| **System RAM Available** | ~7 GB (of 16 GB) |

### Observations
- Response time remains stable under concurrent load
- Tokens/sec throughput is consistent at ~9-17 tokens/second
- Memory footprint is minimal (~34 MB for the Python process)
- Ollama handles model inference separately with ~1 GB model memory

## Known Limitations

- **No persistent storage**: Sessions are in-memory and lost on server restart
- **No authentication**: No user login or API key validation
- **No RAG or tools**: By design (assignment constraint) — all intelligence comes from prompt orchestration
- **Single-machine deployment**: Requires Ollama running on the same host
- **Order state extraction**: Currently relies on keyword detection for confirmation; a more robust NLU approach would improve accuracy
