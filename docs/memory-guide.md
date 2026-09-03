# Memory Guide

## How Memory Works

Memory enriches every interaction. Each memory type contributes context that makes retrieval smarter and answers richer — from durable user facts to ephemeral session state.

When the system encounters something worth remembering, it evaluates the candidate against confidence thresholds and grounding requirements, then either promotes it automatically or invites user confirmation.

---

## Memory Types

### Profile Memory
- **Durability:** Permanent until user deletes
- **Creation:** Explicit statement or strong confirmation from user
- **Grounding:** Required
- **Confirmation:** Always invited
- **Example:** "My name is Jeffe." "I am the sole administrator of this network."

### Preference Memory
- **Durability:** Durable across sessions
- **Creation:** Stated preference or observed strong pattern
- **Grounding:** Soft (preference statements may not cite a source)
- **Confirmation:** Invited when confidence < 0.95
- **Example:** "I prefer metric units." "Always show me the source file path."

### Environment Memory
- **Durability:** Durable, updated when source changes
- **Creation:** Grounded in an ingested source
- **Grounding:** Required — cites a source document
- **Confirmation:** Always invited
- **Example:** "Home network uses VLAN segmentation. Source: infra/topology.md"
- **Role:** Routes retrieval toward the right sources — for exact config values, the source document is always retrieved fresh.

### Project Memory
- **Durability:** Durable per project lifecycle
- **Creation:** From project documents or explicit statement
- **Grounding:** Soft
- **Confirmation:** Optional (auto-promotes at confidence >= 0.90)
- **Example:** "Project Aurora goal: migrate all services to K8s by Q3."

### Procedural Memory
- **Durability:** Versioned — old versions retained
- **Creation:** Derived from source documentation
- **Grounding:** Required — cites source procedure document
- **Confirmation:** Always invited
- **Example:** "To reset the router: 1) hold button 10s 2) ... Source: router-manual.pdf"

### Relationship Memory
- **Durability:** Durable
- **Creation:** From explicit statements or strong evidence
- **Grounding:** Soft
- **Confirmation:** Optional
- **Example:** "NAS Main is managed by Jeffe."

### Episodic Memory
- **Durability:** Durable
- **Creation:** Automatic — recorded during ingestion, conflict resolution, queries
- **Grounding:** Automatic from the event itself
- **Confirmation:** Never (events are factual records)
- **Example:** "Ingested topology.md producing 12 chunks, 5 entities, 8 facts."

### Session Memory
- **Durability:** Session-scoped only (cleared on session end)
- **Creation:** Automatic — written by the Chat Orchestrator
- **Grounding:** None required
- **Confirmation:** Never (ephemeral)

### Working Memory
- **Durability:** Turn-scoped (single reasoning cycle)
- **Creation:** Automatic during retrieval/reasoning
- **Grounding:** None required

---

## Confidence Thresholds for Promotion

| Memory Type | Min Confidence | Auto-Promote Up To |
|-------------|---------------|-------------------|
| profile | 0.85 | — (always confirm) |
| preference | 0.80 | 0.95 |
| environment | 0.90 | — (always confirm) |
| project | 0.80 | 0.90 |
| procedural | 0.90 | — (always confirm) |
| relationship | 0.75 | — (always confirm) |
| episodic | — | automatic |
| session | — | stays ephemeral |

---

## Structural Protections

The memory system structurally protects sensitive data:
- Raw credential values (passwords, tokens, API keys) are stored as references, not values
- Environment and procedural memories require source grounding
- Memories from conflicted or stale facts are held for user review before promotion
