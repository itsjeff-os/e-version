"""Memory Policy Engine — guides when memories are promoted to durable storage."""

from __future__ import annotations

from typing import Any


class MemoryPolicyEngine:
    """
    Layers promotion criteria on top of the base MemoryPromotionPolicy.

    Evaluates:
    - Whether the memory type is enabled for this tenant
    - Whether user confirmation is appropriate
    - Whether grounding is sufficient for promotion
    """

    def __init__(
        self,
        allowed_memory_types: list[str] | None = None,
        require_grounding: bool = True,
    ) -> None:
        from services.memory_engine.app.promotion_policy import MemoryPromotionPolicy
        self._promotion_policy = MemoryPromotionPolicy()
        self._allowed_types = set(allowed_memory_types or ["profile", "preference", "environment", "project", "procedural", "relationship"])
        self._require_grounding = require_grounding

    def evaluate_promotion(self, candidate: dict[str, Any]):
        """Evaluate a memory candidate for promotion."""
        from services.memory_engine.app.promotion_policy import PromotionDecision
        memory_type = candidate.get("memory_type", "session")
        if memory_type not in self._allowed_types:
            return PromotionDecision(
                should_promote=False,
                memory_type=memory_type,
                confidence=0.0,
                requires_confirmation=False,
                reason=f"Memory type '{memory_type}' is not enabled for this tenant.",
                candidate=candidate,
            )
        return self._promotion_policy.evaluate(candidate)
