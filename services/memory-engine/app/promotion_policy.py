"""Memory Promotion Policy — governs when session memories become durable."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PromotionDecision:
    should_promote: bool
    memory_type: str
    confidence: float
    requires_confirmation: bool
    reason: str
    candidate: dict[str, Any] = field(default_factory=dict)


class MemoryPromotionPolicy:
    """
    Evaluates whether a candidate memory is ready for promotion to durable storage.

    Promotion criteria (in order):
    1. Grounded memories (with source backing) promote with higher confidence.
    2. Confidence must meet the threshold for its memory_type.
    3. Environment and procedural memories are strongest when source-grounded.
    4. Profile memories invite user confirmation when confidence < 0.90.
    5. Session memories stay ephemeral unless explicitly promoted.
    """

    CONFIDENCE_THRESHOLDS: dict[str, float] = {
        "profile": 0.85,
        "preference": 0.80,
        "environment": 0.90,
        "project": 0.80,
        "procedural": 0.90,
        "relationship": 0.75,
        "session": 1.00,
    }

    REQUIRES_GROUNDING: set[str] = {"environment", "procedural", "profile"}
    AUTO_CONFIRM_MAX_CONFIDENCE: dict[str, float] = {
        "preference": 0.95,
        "project": 0.90,
    }

    def evaluate(self, candidate: dict[str, Any]) -> PromotionDecision:
        """Evaluate a candidate memory for promotion."""
        memory_type = candidate.get("memory_type", "session")
        confidence = float(candidate.get("confidence", 0.0))
        grounding_sources = candidate.get("grounding_sources", [])

        if memory_type == "session":
            return PromotionDecision(
                should_promote=False,
                memory_type=memory_type,
                confidence=confidence,
                requires_confirmation=False,
                reason="Session memories stay ephemeral by design.",
                candidate=candidate,
            )

        if memory_type in self.REQUIRES_GROUNDING and not grounding_sources:
            return PromotionDecision(
                should_promote=False,
                memory_type=memory_type,
                confidence=confidence,
                requires_confirmation=False,
                reason=f"{memory_type} memory needs source grounding to promote — add a source reference.",
                candidate=candidate,
            )

        threshold = self.CONFIDENCE_THRESHOLDS.get(memory_type, 0.80)
        if confidence < threshold:
            return PromotionDecision(
                should_promote=False,
                memory_type=memory_type,
                confidence=confidence,
                requires_confirmation=False,
                reason=f"Confidence {confidence:.2f} hasn't reached the {threshold:.2f} threshold for {memory_type} yet.",
                candidate=candidate,
            )

        # Determine if user confirmation is needed
        auto_max = self.AUTO_CONFIRM_MAX_CONFIDENCE.get(memory_type, 0.0)
        requires_confirmation = confidence < auto_max or memory_type == "profile"

        return PromotionDecision(
            should_promote=True,
            memory_type=memory_type,
            confidence=confidence,
            requires_confirmation=requires_confirmation,
            reason="Memory meets promotion criteria.",
            candidate=candidate,
        )
