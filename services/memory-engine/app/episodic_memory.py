"""Episodic Memory Store — captures what happened, when, and what it meant."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class EpisodicMemoryStore:
    """
    Stores and retrieves episodic memories — records of events, interactions,
    and outcomes that build a narrative understanding of the user's world.

    Episodic memories capture:
    - What happened (the event or interaction)
    - When it happened (temporal anchor)
    - What entities were involved
    - What the outcome or significance was
    - How it connects to other episodes

    These memories enable the system to reason about patterns over time,
    recall relevant past experiences, and understand the user's history.
    """

    def __init__(self) -> None:
        self._episodes: dict[str, list[dict[str, Any]]] = {}

    def record(
        self,
        tenant_id: str,
        user_id: str,
        episode: dict[str, Any],
    ) -> dict[str, Any]:
        """Record a new episodic memory."""
        key = f"{tenant_id}:{user_id}"
        if key not in self._episodes:
            self._episodes[key] = []

        episode.setdefault("recorded_at", datetime.now(tz=timezone.utc).isoformat())
        episode.setdefault("entity_ids", [])
        episode.setdefault("significance", "normal")
        self._episodes[key].append(episode)
        return episode

    def get_for_user(self, user_id: str, tenant_id: str) -> list[dict[str, Any]]:
        """Return all episodic memories for a user, newest first."""
        episodes = list(self._episodes.get(f"{tenant_id}:{user_id}", []))
        episodes.sort(key=lambda e: e.get("recorded_at", ""), reverse=True)
        return episodes

    def get_by_entities(
        self, user_id: str, tenant_id: str, entity_ids: list[str]
    ) -> list[dict[str, Any]]:
        """Return episodes involving any of the given entities."""
        all_episodes = self.get_for_user(user_id, tenant_id)
        entity_set = set(entity_ids)
        return [
            ep for ep in all_episodes
            if entity_set & set(ep.get("entity_ids", []))
        ]

    def get_recent(
        self, user_id: str, tenant_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Return the most recent episodic memories."""
        return self.get_for_user(user_id, tenant_id)[:limit]

    def get_by_type(
        self, user_id: str, tenant_id: str, episode_type: str
    ) -> list[dict[str, Any]]:
        """Return episodes of a specific type (e.g., 'ingestion', 'conflict', 'query')."""
        all_episodes = self.get_for_user(user_id, tenant_id)
        return [ep for ep in all_episodes if ep.get("episode_type") == episode_type]

    def search(
        self, user_id: str, tenant_id: str, query: str
    ) -> list[dict[str, Any]]:
        """Simple text search across episode summaries."""
        all_episodes = self.get_for_user(user_id, tenant_id)
        query_lower = query.lower()
        return [
            ep for ep in all_episodes
            if query_lower in ep.get("summary", "").lower()
            or query_lower in ep.get("subject", "").lower()
        ]
