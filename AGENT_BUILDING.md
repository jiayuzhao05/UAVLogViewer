# Agent Building — Design Focus

> **This submission emphasizes Agent Building**: following agentic standards and use of state-of-the-art tools and packages for an intelligent, reasoning-based chatbot.

## Agentic Standards Followed

### 1. **Conversation State & Multi-Turn Reasoning**

The agent maintains **persistent conversation state** across turns:

- `Conversation` entity (`backend/domain/entities/conversation.py`) holds full message history
- `conversation_id` is returned to the client and passed back for follow-up questions
- LLM receives full context: `conversation.get_messages_for_llm()` — no information loss between turns

```python
# Agent persists state; client continues the conversation
payload = {"question": "When did GPS first get lost?", "conversation_id": conv_id, "file_id": fid}
```

### 2. **Proactive Clarification (Agentic Behavior)**

Instead of guessing, the agent **asks for clarification** when data is insufficient:

- `_needs_clarification()` detects when the LLM requests more info
- `clarification_question` is extracted and returned to the user
- Response includes `requires_clarification: true` and `clarification_question` for UX

```json
{
  "answer": "I need more context about which flight segment...",
  "requires_clarification": true,
  "clarification_question": "Which time range should I focus on?"
}
```

### 3. **Dynamic Tool-Like Data Retrieval**

The agent **infers what data to fetch** from the user's question — no hardcoded question→answer mapping:

- `_infer_message_types(query_text)` maps natural language to MAVLink message types
- Keywords like "altitude", "GPS", "battery", "error" → `GPS_RAW_INT`, `BATTERY_STATUS`, `STATUSTEXT`, etc.
- Telemetry is retrieved **on demand** per query, not pre-loaded

| User Question | Inferred Message Types |
|---------------|------------------------|
| "Highest altitude?" | `GPS_RAW_INT`, `GLOBAL_POSITION_INT` |
| "GPS signal lost?" | `GPS_RAW_INT` |
| "Battery temperature?" | `BATTERY_STATUS` |
| "Critical errors?" | `STATUSTEXT` |

### 4. **Flexible Reasoning Over Rule-Based Logic**

Per the spec: *"Design prompts to encourage flexible reasoning rather than binary rule evaluation."*

- **No hardcoded rules** like "altitude must not drop >10m in 1 second"
- **Anomaly summary** is injected as **hints** (status, counts, examples) — LLM reasons about patterns
- System prompt: *"Look for sudden changes in altitude, battery temperature, inconsistent GPS lock"* — guidance, not rules
- `AnomalyService` provides heuristic summaries; LLM interprets and explains

### 5. **Context Injection for Richer Reasoning**

Structured context is injected into the LLM system prompt:

- **Telemetry summary**: filename, message count, types, time range
- **Anomaly summary**: status, counts (gps_loss, rc_loss, etc.), altitude range, battery temp max, examples
- **MAVLink docs**: `https://ardupilot.org/plane/docs/logmessages.html`
- **Sample telemetry**: first 10 messages for grounding

All injected in `openai_client.py` / `anthropic_client.py` `_build_system_prompt()`.

### 6. **Multi-Provider LLM Support**

- `ILLMClient` interface abstracts LLM calls
- `LLMFactory` creates OpenAI or Anthropic client from `LLM_PROVIDER`
- Same agent logic works with different models — easy to swap or add providers

## State-of-the-Art Tools & Packages

| Package | Purpose |
|---------|---------|
| **OpenAI API** (`openai>=1.3.0`) | Chat completions, async support |
| **Anthropic API** (`anthropic>=0.7.0`) | Claude models for alternative reasoning |
| **pymavlink** | Industry-standard MAVLink parsing |
| **FastAPI** | Async API, type-safe request/response |
| **Pydantic** | Structured validation for DTOs |

## Architecture: Agent-Oriented Design

```
User Question
      ↓
ChatUseCase.process_query()
      ↓
┌─────────────────────────────────────┐
│ 1. Get/Create Conversation (state)  │
│ 2. Build Context (summary + anomaly) │
│ 3. Infer & Retrieve Telemetry       │  ← Dynamic, question-driven
│ 4. LLM with full context           │  ← Flexible reasoning
│ 5. Detect clarification need       │  ← Agentic behavior
└─────────────────────────────────────┘
      ↓
QueryResult (answer, clarification, sources)
```

## Key Files for Agent Logic

| File | Role |
|------|------|
| `backend/application/use_cases/chat_use_case.py` | Core agent orchestration |
| `backend/application/services/anomaly_service.py` | Anomaly hints for LLM |
| `backend/infrastructure/llm/openai_client.py` | Context injection into prompt |
| `backend/domain/entities/conversation.py` | Conversation state model |

## ETE Intelligence: Beyond Rule-Based

- **Not**: if "altitude" in question → return max(altitudes)
- **Is**: Infer message types → retrieve data → inject context → LLM reasons about patterns, thresholds, inconsistencies → may ask for clarification

The agent combines **structured data retrieval** with **LLM reasoning** — hybrid approach for robust, generalizable answers.
