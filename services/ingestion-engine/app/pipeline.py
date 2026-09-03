"""
Ingestion Pipeline — transforms raw sources into structured, connected knowledge.

Source → Fetch → Normalize → Dedupe → Chunk → Extract Entities/Facts →
Build Graph → Embed → Index → Record Episode
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from packages.connectors.base import SourceConnector, FetchResult
from packages.schemas.documents import Document, DocumentStatus
from packages.schemas.chunks import Chunk, ChunkType
from packages.schemas.entities import Entity, EntityType, Relation, RelationType

from .normalizer import Normalizer
from .deduper import Deduper
from .chunker import Chunker
from .entity_extractor import EntityExtractor
from .fact_extractor import FactExtractor

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    document_id: str
    chunk_count: int
    entity_count: int
    fact_count: int
    relation_count: int = 0
    skipped_duplicate: bool = False
    errors: list[str] = field(default_factory=list)


class IngestionPipeline:
    """
    Runs the full ingestion pipeline for a single source document,
    building the knowledge graph as it goes.

    Steps:
    1. Fetch (via connector)
    2. Normalize
    3. Deduplicate
    4. Chunk
    5. Extract entities
    6. Extract facts
    7. Build knowledge graph (entities + relations)
    8. Embed (requires embedding service)
    9. Index (requires vector store + search index)
    10. Detect conflicts
    11. Record episodic memory of the ingestion
    """

    def __init__(
        self,
        embedding_service=None,
        vector_store=None,
        search_index=None,
        entity_store=None,
        relation_store=None,
        fact_store=None,
        conflict_detector=None,
        episodic_memory=None,
    ) -> None:
        self.normalizer = Normalizer()
        self.deduper = Deduper()
        self.chunker = Chunker()
        self.entity_extractor = EntityExtractor()
        self.fact_extractor = FactExtractor()
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.search_index = search_index
        self.entity_store = entity_store
        self.relation_store = relation_store
        self.fact_store = fact_store
        self.conflict_detector = conflict_detector
        self.episodic_memory = episodic_memory

    def ingest(
        self,
        connector: SourceConnector,
        source_id: str,
        tenant_id: str,
        user_id: str,
    ) -> IngestionResult:
        """Run the full pipeline for a single source."""
        logger.info("Ingesting source: %s", source_id)
        errors: list[str] = []

        # 1. Fetch
        try:
            fetch_result: FetchResult = connector.fetch(source_id)
        except Exception as exc:
            logger.error("Fetch failed for %s: %s", source_id, exc)
            return IngestionResult(document_id="", chunk_count=0, entity_count=0, fact_count=0, errors=[str(exc)])

        # 2. Normalize
        normalized = self.normalizer.normalize(fetch_result.normalized_content, source_type=connector.source_type)

        # 3. Deduplicate
        content_hash = self.deduper.hash(normalized)
        if self.deduper.is_duplicate(normalized):
            logger.info("Duplicate detected for %s — skipping.", source_id)
            return IngestionResult(document_id="", chunk_count=0, entity_count=0, fact_count=0, skipped_duplicate=True)
        self.deduper.register(normalized)

        # Build Document record
        meta = fetch_result.metadata
        doc = Document(
            title=meta.title or source_id,
            source_uri=meta.source_uri,
            source_type=meta.source_type,
            tenant_id=tenant_id,
            user_id=user_id,
            content_hash=content_hash,
            parsed_text=normalized,
            status=DocumentStatus.INGESTING,
            permissions=connector.permissions(source_id),
        )

        # 4. Chunk
        if connector.source_type == "markdown":
            raw_chunks = self.chunker.chunk_markdown(normalized)
        else:
            raw_chunks = self.chunker.chunk_text(normalized)

        chunk_objects: list[Chunk] = []
        chunk_texts: list[str] = []
        for raw in raw_chunks:
            chunk = Chunk(
                document_id=doc.id,
                tenant_id=tenant_id,
                user_id=user_id,
                chunk_type=ChunkType.TEXT,
                content=raw.content,
                content_hash=self.deduper.hash(raw.content),
                chunk_index=raw.chunk_index,
                start_char=raw.start_char,
                end_char=raw.end_char,
                section=raw.section,
                heading_path=raw.heading_path or [],
            )
            chunk_objects.append(chunk)
            chunk_texts.append(raw.content)

        # 5. Extract entities
        extracted_entities = self.entity_extractor.extract_from_chunks(chunk_texts)

        # 6. Extract facts
        extracted_facts = self.fact_extractor.extract_from_chunks(chunk_texts, source=meta.source_uri)

        # 7. Build knowledge graph
        stored_entities: list[Entity] = []
        relations: list[Relation] = []
        if self.entity_store:
            stored_entities, relations = self._build_graph(
                extracted_entities, extracted_facts, doc, chunk_objects,
                tenant_id, user_id, errors,
            )

        # 8. Embed
        if self.embedding_service:
            for chunk in chunk_objects:
                try:
                    chunk.embedding = self.embedding_service.embed(chunk.content)
                except Exception as exc:
                    errors.append(f"Embedding failed for chunk {chunk.id}: {exc}")

        # 9. Index
        if self.vector_store:
            for chunk in chunk_objects:
                try:
                    self.vector_store.upsert(chunk)
                except Exception as exc:
                    errors.append(f"Vector store upsert failed for chunk {chunk.id}: {exc}")

        if self.search_index:
            for chunk in chunk_objects:
                try:
                    self.search_index.index(chunk)
                except Exception as exc:
                    errors.append(f"Search index failed for chunk {chunk.id}: {exc}")

        # 10. Detect conflicts
        if self.conflict_detector and self.fact_store:
            try:
                fact_dicts = [
                    {"subject": f.subject, "predicate": f.predicate, "value": f.value,
                     "source": f.source, "trust_level": "source_backed"}
                    for f in extracted_facts
                ]
                conflicts = self.conflict_detector.detect(fact_dicts)
                if conflicts:
                    logger.info("Detected %d conflict(s) during ingestion of %s", len(conflicts), source_id)
            except Exception as exc:
                errors.append(f"Conflict detection failed: {exc}")

        # 11. Record episodic memory of this ingestion
        if self.episodic_memory:
            try:
                entity_names = [e.name for e in stored_entities] if stored_entities else [ee.name for ee in extracted_entities]
                self.episodic_memory.record(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    episode={
                        "episode_type": "ingestion",
                        "subject": f"Ingested {meta.title or source_id}",
                        "summary": (
                            f"Ingested {meta.source_type} source '{meta.title or source_id}' "
                            f"producing {len(chunk_objects)} chunks, "
                            f"{len(extracted_entities)} entities, "
                            f"{len(extracted_facts)} facts, "
                            f"and {len(relations)} relationships."
                        ),
                        "source_uri": meta.source_uri,
                        "entity_ids": [e.id for e in stored_entities] if stored_entities else [],
                        "significance": "normal",
                    },
                )
            except Exception as exc:
                errors.append(f"Episodic memory recording failed: {exc}")

        doc.status = DocumentStatus.INDEXED
        doc.chunk_count = len(chunk_objects)

        logger.info(
            "Ingested %s: %d chunks, %d entities, %d facts, %d relations.",
            source_id,
            len(chunk_objects),
            len(extracted_entities),
            len(extracted_facts),
            len(relations),
        )

        return IngestionResult(
            document_id=doc.id,
            chunk_count=len(chunk_objects),
            entity_count=len(extracted_entities),
            fact_count=len(extracted_facts),
            relation_count=len(relations),
            errors=errors,
        )

    def _build_graph(
        self,
        extracted_entities,
        extracted_facts,
        doc: Document,
        chunks: list[Chunk],
        tenant_id: str,
        user_id: str,
        errors: list[str],
    ) -> tuple[list[Entity], list[Relation]]:
        """Build knowledge graph entities and relations from extracted data."""
        stored_entities: list[Entity] = []
        relations: list[Relation] = []

        # Create Entity objects and store them
        entity_name_to_id: dict[str, str] = {}
        for ext in extracted_entities:
            entity = Entity(
                tenant_id=tenant_id,
                user_id=user_id,
                entity_type=ext.entity_type,
                name=ext.name,
                canonical_name=ext.name.lower().replace(" ", "_"),
                aliases=ext.aliases or [],
                source_ids=[doc.source_uri],
                document_ids=[doc.id],
            )
            try:
                self.entity_store.upsert(entity)
                stored_entities.append(entity)
                entity_name_to_id[ext.name.lower()] = entity.id
            except Exception as exc:
                errors.append(f"Entity store failed for {ext.name}: {exc}")

        # Create a Document entity to represent the source
        doc_entity = Entity(
            tenant_id=tenant_id,
            user_id=user_id,
            entity_type=EntityType.DOCUMENT,
            name=doc.title,
            canonical_name=doc.title.lower().replace(" ", "_"),
            source_ids=[doc.source_uri],
            document_ids=[doc.id],
        )
        try:
            self.entity_store.upsert(doc_entity)
            stored_entities.append(doc_entity)
        except Exception as exc:
            errors.append(f"Document entity store failed: {exc}")

        # Build relations: document_mentions_entity for each extracted entity
        for entity in stored_entities:
            if entity.entity_type == EntityType.DOCUMENT:
                continue
            rel = Relation(
                tenant_id=tenant_id,
                user_id=user_id,
                relation_type=RelationType.DOCUMENT_MENTIONS_ENTITY,
                source_entity_id=doc_entity.id,
                target_entity_id=entity.id,
                provenance=[doc.source_uri],
            )
            if self.relation_store:
                try:
                    self.relation_store.upsert(rel)
                    relations.append(rel)
                except Exception as exc:
                    errors.append(f"Relation store failed: {exc}")

        # Build relations from extracted facts
        for fact in extracted_facts:
            if fact.predicate == "is_on_vlan":
                device_id = entity_name_to_id.get(fact.subject.lower())
                vlan_name = f"VLAN {fact.value}"
                vlan_id = entity_name_to_id.get(vlan_name.lower())
                if device_id and vlan_id:
                    rel = Relation(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        relation_type=RelationType.DEVICE_ON_NETWORK,
                        source_entity_id=device_id,
                        target_entity_id=vlan_id,
                        provenance=[fact.source],
                    )
                    if self.relation_store:
                        try:
                            self.relation_store.upsert(rel)
                            relations.append(rel)
                        except Exception as exc:
                            errors.append(f"Fact relation store failed: {exc}")

        # Store facts
        if self.fact_store:
            for fact in extracted_facts:
                try:
                    self.fact_store.upsert(fact, tenant_id=tenant_id, user_id=user_id)
                except Exception as exc:
                    errors.append(f"Fact store failed: {exc}")

        return stored_entities, relations
