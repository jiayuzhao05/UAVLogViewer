# Chatbot Feature

## Architecture

Built with DDD and MVC for low coupling and easy extensibility.

### Layer

```
backend/
├── domain/              # Core business logic
│   ├── entities/        # Entities (Conversation, FlightLog, Message)
│   ├── value_objects/   # Value objects (Query, QueryResult)
│   └── repositories/    # Repository interfaces
│
├── application/         # Use cases and services
│   ├── services/        # Application services (ChatService, TelemetryService)
│   └── use_cases/       # Use cases (ChatUseCase)
│
├── infrastructure/      # External dependencies
│   ├── llm/             # LLM clients (OpenAI/Anthropic)
│   ├── parsers/         # File parsers (MAVLink)
│   └── storage/         # Storage impl (in-memory, non-persistent)
│
└── presentation/        # API layer
    ├── api/             # FastAPI routes
    ├── controllers/     # Controllers (ChatController)
    └── dtos/            # Data transfer objects
```

## Core Capabilities

1) File upload & parsing
- Upload `.bin` MAVLink flight logs
- Parse via `pymavlink`
- Parsed data stored in-memory (not persisted)

2) Conversational chat
- Multi-turn dialog with conversation state
- Dynamic telemetry retrieval based on questions
- LLM integration (OpenAI / Anthropic)
- Agentic clarifications when info is insufficient

3) Data retrieval
- Infer relevant message types from question text
- Filter by message type
- Provide telemetry summaries

4) Anomaly awareness
- Heuristic anomaly summary (GPS/RC signal loss, high-severity STATUSTEXT, battery temp, altitude range)
- Context injection to LLM for flexible reasoning (not hard-coded rules)
- Cached per file_id to avoid recomputation

## Code Example

### Upload a file
```python
import requests

with open("flight_log.bin", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/upload",
        files={"file": f}
    )

result = response.json()
file_id = result["file_id"]
print(f"file id: {file_id}")
```

### Send a chat request
```python
import requests

# First question
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "question": "What was the highest altitude reached during the flight?",
        "file_id": "your_file_id"
    }
)

result = response.json()
conversation_id = result["conversation_id"]
answer = result["answer"]
print(f"answer: {answer}")

# Continue the conversation
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "question": "When did the GPS signal first get lost?",
        "conversation_id": conversation_id,
        "file_id": "your_file_id_here"
    }
)
```

### End-to-end example
```python
import requests

# 1. Upload file
with open("flight_log.bin", "rb") as f:
    upload_response = requests.post(
        "http://localhost:8000/api/upload",
        files={"file": f}
    )
    file_id = upload_response.json()["file_id"]
    print(f"uploaded, id: {file_id}")

# 2. Ask questions
questions = [
    "What was the highest altitude reached during the flight?",
    "When did the GPS signal first get lost?",
    "What was the maximum battery temperature?",
    "How long was the total flight time?",
    "List all critical errors that happened mid-flight.",
    "When was the first instance of RC signal loss?",
]

conversation_id = None
for question in questions:
    chat_response = requests.post(
        "http://localhost:8000/api/chat",
        json={
            "question": question,
            "conversation_id": conversation_id,
            "file_id": file_id,
        }
    )
    result = chat_response.json()
    conversation_id = result["conversation_id"]

    print(f"\nQ: {question}")
    print(f"A: {result['answer']}")
    if result.get("requires_clarification"):
        print(f"Clarify: {result.get('clarification_question')}")
```

## API

### POST /api/upload
Upload a `.bin` file.

Request (multipart):
- `file`

Response:
```json
{
  "file_id": "uuid",
  "filename": "flight_log.bin",
  "message": "File uploaded successfully, parsed 1234 messages",
  "parsed_messages": 1234
}
```

### POST /api/chat
Send a chat message.

Request:
```json
{
  "question": "What was the highest altitude?",
  "conversation_id": "optional-uuid",
  "file_id": "optional-uuid"
}
```

Response:
```json
{
  "answer": "Based on telemetry, ...",
  "conversation_id": "uuid",
  "confidence": 0.8,
  "sources": ["Flight log: uuid"],
  "requires_clarification": false,
  "clarification_question": null
}
```

### GET /api/telemetry/summary/{file_id}
Return telemetry summary plus anomaly summary (cached per file).

Response:
```json
{
  "summary": { ... },
  "anomaly_summary": { ... }
}
```

## Environment

Create `.env`:
```env
# LLM
OPENAI_API_KEY=your_openai_key
# or
ANTHROPIC_API_KEY=your_anthropic_key

# Provider (default: openai)
LLM_PROVIDER=openai

# Optional: model config
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Temp upload dir
UPLOAD_DIR=./uploads
```

Switch provider by changing `LLM_PROVIDER` and supplying the corresponding API key/model.

## Run
```bash
# install deps
pip install -r requirements.txt

# start service
uvicorn backend.presentation.api.main:app --reload

```

## UI
- Served at `/ui`
- Upload progress bar, parsed message count, anomaly summary card
- Chat bubbles with source tags, clarification prompts, and copyable conversation_id

## Extending further

Thanks to the low-coupling design, to add new features:
1. New use cases: add under `application/use_cases/`
2. New services: add under `application/services/`
3. New APIs: add routes under `presentation/api/`
4. New storage: implement the repository interfaces

