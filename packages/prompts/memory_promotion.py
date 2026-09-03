"""Memory promotion prompt — asks the LLM to evaluate candidate memories."""

from __future__ import annotations

import json


MEMORY_PROMOTION_TEMPLATE = """\
You are the memory promotion evaluator for E-Version.

A candidate memory has emerged from the current conversation. \
Evaluate whether it's ready to become durable — a lasting part of the user's context.

Candidate memory:
{candidate_json}

Grounding sources available: {grounding_sources}

Session context summary: {session_context}

Evaluate the candidate:
1. Is this fact grounded in the provided sources?
2. Is this the kind of knowledge that enriches future sessions?
3. Is the confidence level strong enough for this memory type?
4. Would the user benefit from confirming this before it's stored?

Respond with a JSON object:
{{
  "should_store": <true | false>,
  "memory_type": "<profile | preference | environment | project | procedural | relationship | episodic | session>",
  "confidence": <0.0 to 1.0>,
  "requires_confirmation": <true | false>,
  "reason": "<brief explanation>"
}}

Return only valid JSON. Do not explain outside the JSON.
"""


def build_memory_promotion_prompt(
    candidate: dict,
    grounding_sources: list[str] | None = None,
    session_context: str = "",
) -> str:
    """Build the memory promotion evaluation prompt."""
    return MEMORY_PROMOTION_TEMPLATE.format(
        candidate_json=json.dumps(candidate, indent=2),
        grounding_sources=json.dumps(grounding_sources or []),
        session_context=session_context or "No session context available.",
    )
