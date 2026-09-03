# E-Version — Personal Context Intelligence

An AI-native platform that gives language models deep, structured access to your personal world — your documents, networks, projects, relationships, and environment — so they can reason with full context, not just chunks.

## What E-Version Does

> Your AI finally knows your world.

| Layer | What it brings |
|-------|---------------|
| **Sources** | Your documents, configs, exports, notes — ingested and kept fresh |
| **Knowledge Graph** | Entities, relationships, and structured facts — your world as a connected model |
| **Memory** | Typed, layered memory — profile, preferences, environment, episodic, session |
| **Retrieval** | Intelligent multi-modal search — semantic, lexical, graph traversal, fact lookup |
| **Trust & Freshness** | Every fact scored by provenance and age — the AI knows what to rely on |
| **LLM** | Reasons over all of it — grounded, cited, and transparent |

---

## Beyond Basic RAG

Basic RAG retrieves **chunks** and hopes for the best.
E-Version retrieves **context** — structured, scored, and connected.

The assistant can:
- **Connect the dots** across your knowledge graph — entities, relationships, causality
- **Retrieve intelligently** — a retrieval planner decides what modes to use before searching
- **Score what it finds** — trust levels, freshness, and source provenance flow through every answer
- **Show its work** — every answer is cited, every retrieval is traceable
- **Remember meaningfully** — typed memory that knows when to persist and when to let go
- **Surface conflicts** — when sources disagree, you see both sides

---

## Architecture

```
e-version/
  services/
    api-gateway/          # Auth, rate limits, routing
    chat-orchestrator/    # Runtime intelligence loop
    retrieval-engine/     # Hybrid search + graph expansion
    ingestion-engine/     # Source → structured knowledge
    memory-engine/        # Typed, layered memory
    knowledge-graph/      # Entity and relationship model
    policy-engine/        # Access, memory, source, sensitivity
    eval-engine/          # Continuous quality evaluation
  packages/
    schemas/              # Core data models (Pydantic)
    connectors/           # Source connectors
    prompts/              # LLM prompt templates
    ranking/              # Trust, freshness, scoring, reranking
    citations/            # Citation formatting and verification
    observability/        # Tracing, metrics, audit logging
    auth/                 # JWT auth, tenant context
    conflict_resolution/  # Conflict resolution strategies
  workers/
    sync_worker/          # Source sync polling
    embedding_worker/     # Vector embedding generation
    extraction_worker/    # Entity and fact extraction
    eval_worker/          # Regression eval runner
  infrastructure/
    docker-compose.yml    # Single-user deployment
    migrations/           # Postgres schema migrations
  apps/
    cli/                  # Command-line interface
    web-console/          # Admin dashboard (planned)
    browser-extension/    # Browser activity connector (planned)
  context-fixtures/       # Sample context for development
  tests/
    unit/                 # Unit tests
    integration/          # Integration tests
    evals/                # Retrieval quality evals
  docs/
    architecture.md
    memory-guide.md
    retrieval-guide.md
    security-model.md
```

---

## Quick Start

### 1. Set up infrastructure

```bash
cp infrastructure/.env.example infrastructure/.env
# Edit .env — set POSTGRES_PASSWORD, REDIS_PASSWORD, OPENAI_API_KEY, etc.
docker compose -f infrastructure/docker-compose.yml up -d
```

### 2. Ingest your context

```bash
# Ingest a directory of markdown files
python -m apps.cli.main ingest ./your-docs/

# Ingest a specific file
python -m apps.cli.main ingest ./infra/topology.md
```

### 3. Chat

```bash
python -m apps.cli.main chat
```

---

## Running Tests

```bash
pip install pytest pydantic
python -m pytest tests/unit/ -q
```

---

## How It Works

### Intelligent Retrieval Planning

Before searching, the system generates a typed retrieval plan that decides *how* to find what's needed:

```json
{
  "intent": "network_troubleshooting",
  "entities": ["apple_tv_lounge", "nas_main", "vlan_20"],
  "retrieval_modes": ["fact_lookup", "graph_traversal", "semantic", "lexical"],
  "freshness_requirement": "high",
  "risk_level": "operational"
}
```

### Trust-Scored Facts

Every fact carries provenance — the system knows how much to rely on each piece of information:

```python
TrustLevel.PINNED           # 1.00 — user-pinned, immutable
TrustLevel.CANONICAL        # 0.95 — authoritative source
TrustLevel.MACHINE_VERIFIED # 0.90 — machine-parsed export
TrustLevel.USER_CONFIRMED   # 0.85 — confirmed by user
TrustLevel.SOURCE_BACKED    # 0.75 — from an ingested source
TrustLevel.INFERRED         # 0.45 — LLM inference
TrustLevel.STALE            # 0.25 — outdated
```

### Typed Memory

Memory is layered by purpose, each with its own lifecycle:

```python
ProfileMemory      # Durable — who you are, confirmed by you
PreferenceMemory   # Durable — how you like things
EnvironmentMemory  # Durable — your infrastructure, grounded in sources
EpisodicMemory     # Durable — what happened, when, and what it meant
ProceduralMemory   # Versioned — how-to knowledge from your docs
SessionMemory      # Ephemeral — current conversation context
WorkingMemory      # Ephemeral — single reasoning cycle
```

### Transparent Conflicts

When sources disagree, the system surfaces both sides:

```
Heads up — conflicting values for vlan_20.subnet:
  - 192.168.20.0/24 (source: vlans.md, trust: canonical)
  - 10.20.0.0/24 (source: router_export.json, trust: machine_verified)
  Suggested resolution: prefer router_export.json (machine_verified, newer)
```

---

## Docs

- [Architecture](docs/architecture.md)
- [Memory Guide](docs/memory-guide.md)
- [Retrieval Guide](docs/retrieval-guide.md)
- [Security Model](docs/security-model.md)
