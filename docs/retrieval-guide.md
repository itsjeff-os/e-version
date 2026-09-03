# Retrieval Guide

## How Retrieval Works

Every query starts with a **retrieval plan** — the system decides what it needs, where to look, and how to rank what it finds before searching.

The retrieval planner considers:
- What context does this question need?
- Which sources are most relevant?
- How fresh does the context need to be?
- What retrieval modes will produce the best answer?

---

## Retrieval Modes

| Mode | What It Does |
|------|-------------|
| `semantic` | General question answering, summarization |
| `lexical` | Exact matches, config values, device names, file paths |
| `fact_lookup` | Structured fact retrieval from the fact store |
| `graph_traversal` | Entity-linked context expansion across the knowledge graph |
| `temporal` | Time-sensitive queries, recent events |
| `procedural` | How-to questions, setup procedures |
| `preference` | User preference retrieval |
| `recent_session` | Cross-session context continuity |

---

## Retrieval Plan Schema

```json
{
  "intent": "network_troubleshooting",
  "entities": ["apple_tv_lounge", "nas_main", "vlan_20", "mdns"],
  "needed_context": [
    "device_facts",
    "network_topology",
    "vlan_rules",
    "firewall_rules",
    "known_issues",
    "recent_session_state"
  ],
  "retrieval_modes": [
    "fact_lookup",
    "graph_traversal",
    "semantic",
    "lexical"
  ],
  "freshness_requirement": "high",
  "risk_level": "operational"
}
```

---

## Ranking Formula

```
final_score =
  semantic_score    * 0.20 +
  lexical_score     * 0.15 +
  entity_overlap    * 0.20 +
  graph_relevance   * 0.15 +
  trust_score       * 0.15 +
  freshness_score   * 0.10 +
  session_relevance * 0.05
```

For technical config queries (`risk_level: operational`), exact match and trust weights are boosted. The planner adjusts weights by intent class.

---

## Permission Scoping

Source permissions flow through every layer of retrieval:

1. Resolve the user's permission set from the tenant context
2. Scope all chunks to their `permissions` list
3. Scope all facts to their source permissions
4. Only content within the active context's scope reaches the LLM

This is structural — enforced by the Policy Engine before any content is assembled.

---

## Context Budget

The model receives context in layers. When token budget is constrained:

1. Task/instruction context (always included)
2. Relevant durable preferences
3. Current session state
4. High-trust structured facts (pinned → canonical → machine_verified)
5. Supporting retrieved chunks (by final_score)
6. Conflicts / freshness notes (always included if present)
7. Raw excerpts — only if budget remains

Structured facts are preferred over large raw documents when available.

---

## Transparent Conflicts

Conflicts are **first-class objects** — when sources disagree, both sides surface.

When the retrieval engine detects conflicting claims:
1. Surface both claims with their sources and trust levels
2. Apply the default resolution strategy (prefer machine_verified + newer)
3. Flag conflicts that would benefit from user review
4. Always show the conflict in the answer — transparency over silent resolution

Example:
```
Heads up — conflicting values for vlan_20.subnet:
  - 192.168.20.0/24 (source: vlans.md, trust: canonical)
  - 10.20.0.0/24 (source: router_export.json, trust: machine_verified)
  Suggested resolution: prefer router_export.json (machine_verified, newer)
```

---

## Freshness

Freshness classification:
- `current` — updated within 7 days
- `recent` — updated within 30 days
- `aging` — updated within 90 days
- `stale` — updated within 365 days
- `expired` — not updated in over a year

For `risk_level: operational` queries, stale and expired facts are surfaced with freshness notes and not used as primary answers.
