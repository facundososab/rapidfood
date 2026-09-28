# Conversational agent — LangChain / LangGraph driver

This directory is the LangChain **driver adapter**. The core
(`conversation/application`, `conversation/domain`) does not depend on LangChain,
LangGraph or LangSmith.

## What talks to what

```
Studio / LangSmith (threads, tracing)
        |
graph.py                   <- Agent Server entrypoint: resolves the context from
        |                     the thread and delegates to the REAL flow
HandleIncomingMessageUseCase
        |                   <- persist USER -> agent -> persist ASSISTANT
LangChainConversationAgentAdapter -> tools.py -> conversation use cases
        |
cross-module adapters -> order / catalog / delivery
```

Studio runs **the same agent** that a WhatsApp driver will use later: `graph.py`
only adapts the channel, it holds no business logic.

## Provider

Groq via `langchain-groq` (`build_agent_model`). The model comes from
`AGENT_MODEL` and the key from `GROQ_API_KEY`. Nothing is hardcoded.

## Environment (repo-root `.env`)

```
GROQ_API_KEY=...                    # required to build the model
AGENT_MODEL=openai/gpt-oss-120b
AGENT_BUSINESS_CONFIG_ID=<id>       # optional DEV fallback (see below)

LANGSMITH_TRACING=true              # optional: tracing
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=rapidfood-agent-dev
# LANGSMITH_WORKSPACE_ID / LANGSMITH_ENDPOINT if needed
```

LangSmith reads these from `os.environ` (the `.env` loader populates it); they are
**not** copied into Django settings. Never put secrets in prompts, tool metadata
or traces.

## Identity

- `thread_id` → `Conversation.externalThreadId` (external identity). It is
  **never** the `Conversation.id` and **never** an `Order.id`.
- `businessConfigId` / `clientId`: taken from the graph **runtime context**:
  `configurable = {"business_config_id": "...", "client_id": "..."}`.
- `AGENT_BUSINESS_CONFIG_ID` is an **optional DEV fallback**. It can even stay
  empty: the driver resolves the single existing business dynamically, so it
  keeps working after a database re-seed (the business id is a generated UUID and
  hardcoding it can go stale). It is not the multi-tenant design.
- `externalMessageId` is generated once per incoming message and reused by every
  tool of that turn. It is **not** the LangSmith `run_id`.

## Run

`graph.py` makes the `api` root importable on its own, so no `PYTHONPATH` is
needed:

```bash
uv run langgraph dev
```

The Agent Server exposes the graph `rapidfood_agent` (see `langgraph.json`), by
default on `http://127.0.0.1:2024`. Open LangSmith Studio and connect it to the
local server, start a thread and send a message.

## Docker note

The backend container bakes its dependencies and the generated Prisma client; it
does not mount `pyproject.toml` / `uv.lock` / `.venv`. After changing the schema
or the dependencies, rebuild:

```bash
docker compose build backend && docker compose up -d backend
```

## Limitations

- The exact Mercado Pago Orders API payload/response fields were not validated
  against live credentials; the adapter parses defensively.
- The Groq free tier has per-minute/per-day rate limits that can throttle live evals.
