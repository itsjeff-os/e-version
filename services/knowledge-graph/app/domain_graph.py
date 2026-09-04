"""Domain Graph — scoped knowledge graph interface for querying domain-specific entities and relations."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

_kg_app = Path(__file__).resolve().parent
if str(_kg_app) not in sys.path:
    sys.path.insert(0, str(_kg_app))

from packages.schemas.entities import Entity, EntityType, Relation, RelationType
from entity_store import EntityStore
from relation_store import RelationStore


class DomainGraph:
    """Query interface over a scoped domain graph (smart home, design, coding, etc.)."""

    def __init__(self, domain: str, entity_store: EntityStore, relation_store: RelationStore) -> None:
        self.domain = domain
        self.entity_store = entity_store
        self.relation_store = relation_store

    def get_area(self, area_id: str) -> Entity | None:
        return self.entity_store.get_by_id(f"{self.domain}:area:{area_id}")

    def get_device(self, device_id: str) -> Entity | None:
        return self.entity_store.get_by_id(f"{self.domain}:device:{device_id}")

    def resolve(self, name: str) -> Entity | None:
        return self.entity_store.get_by_name(name)

    def devices_in_area(self, area_id: str) -> list[Entity]:
        area_entity_id = f"{self.domain}:area:{area_id}"
        incoming = self.relation_store.get_incoming(area_entity_id, [RelationType.DEVICE_IN_AREA])
        return [
            e for rel in incoming
            if (e := self.entity_store.get_by_id(rel.source_entity_id)) is not None
        ]

    def area_for_device(self, device_id: str) -> Entity | None:
        device_entity_id = f"{self.domain}:device:{device_id}"
        outgoing = self.relation_store.get_outgoing(device_entity_id, [RelationType.DEVICE_IN_AREA])
        if outgoing:
            return self.entity_store.get_by_id(outgoing[0].target_entity_id)
        return None

    def adjacent_areas(self, area_id: str) -> list[Entity]:
        area_entity_id = f"{self.domain}:area:{area_id}"
        rels = self.relation_store.get_outgoing(area_entity_id, [RelationType.AREA_ADJACENT_TO])
        return [
            e for rel in rels
            if (e := self.entity_store.get_by_id(rel.target_entity_id)) is not None
        ]

    def zones_in_area(self, area_id: str) -> list[Entity]:
        area_entity_id = f"{self.domain}:area:{area_id}"
        incoming = self.relation_store.get_incoming(area_entity_id, [RelationType.ZONE_WITHIN_AREA])
        return [
            e for rel in incoming
            if (e := self.entity_store.get_by_id(rel.source_entity_id)) is not None
        ]

    def devices_by_type(self, entity_type: EntityType) -> list[Entity]:
        return self.entity_store.find_by_type(entity_type, "default", "jeff")

    def integration_devices(self, integration_id: str) -> list[Entity]:
        integ_entity_id = f"{self.domain}:integration:{integration_id}"
        outgoing = self.relation_store.get_outgoing(integ_entity_id, [RelationType.INTEGRATION_PROVIDES_DEVICE])
        return [
            e for rel in outgoing
            if (e := self.entity_store.get_by_id(rel.target_entity_id)) is not None
        ]

    def traverse(self, entity_id: str, depth: int = 1) -> dict[str, Any]:
        visited: set[str] = set()
        result: dict[str, Any] = {"entity": None, "neighbors": []}

        entity = self.entity_store.get_by_id(entity_id)
        if not entity:
            return result

        result["entity"] = entity

        def _walk(eid: str, remaining: int) -> list[dict[str, Any]]:
            if remaining <= 0 or eid in visited:
                return []
            visited.add(eid)
            neighbor_ids = self.relation_store.get_neighbors(eid)
            neighbors = []
            for nid in neighbor_ids:
                n = self.entity_store.get_by_id(nid)
                if n:
                    entry: dict[str, Any] = {"entity": n}
                    if remaining > 1:
                        entry["neighbors"] = _walk(nid, remaining - 1)
                    neighbors.append(entry)
            return neighbors

        result["neighbors"] = _walk(entity_id, depth)
        return result
