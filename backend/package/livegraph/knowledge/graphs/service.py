from livegraph.knowledge.graphs.extractor import extract_triples
from livegraph.knowledge.graphs.graph_utils import (
    CYPHER_MERGE_CHUNK,
    CYPHER_MERGE_ENTITY_MENTION,
    CYPHER_MERGE_RELATION,
    compute_entity_id,
    compute_triple_id,
    normalize_entity_name,
)
from livegraph.storage.neo4j.manager import get_shared_neo4j_connection


def _write_chunk_and_triples(driver, session_id: str, chunk_id: str, relations: list[dict]) -> None:
    with driver.session() as session:
        session.run(CYPHER_MERGE_CHUNK, chunk_id=chunk_id, session_id=session_id)

        for relation in relations:
            source = relation.get("source") or {}
            target = relation.get("target") or {}
            source_name = normalize_entity_name(source.get("text", ""))
            target_name = normalize_entity_name(target.get("text", ""))
            source_label = source.get("label") or "Entity"
            target_label = target.get("label") or "Entity"
            relation_type = relation.get("label") or "RELATED_TO"

            if not source_name or not target_name:
                continue

            session.run(
                CYPHER_MERGE_ENTITY_MENTION,
                chunk_id=chunk_id,
                session_id=session_id,
                normalized_name=source_name,
                entity_label=source_label,
                entity_id=compute_entity_id(session_id, source_name, source_label),
                name=source.get("text", ""),
            )
            session.run(
                CYPHER_MERGE_ENTITY_MENTION,
                chunk_id=chunk_id,
                session_id=session_id,
                normalized_name=target_name,
                entity_label=target_label,
                entity_id=compute_entity_id(session_id, target_name, target_label),
                name=target.get("text", ""),
            )
            session.run(
                CYPHER_MERGE_RELATION,
                session_id=session_id,
                chunk_id=chunk_id,
                source_name=source_name,
                target_name=target_name,
                source_label=source_label,
                target_label=target_label,
                relation_type=relation_type,
                triple_id=compute_triple_id(session_id, source_name, target_name, relation_type),
                text=relation.get("text", ""),
            )


async def index_chunk_into_graph(session_id: str, chunk_id: str, content: str) -> int:
    import asyncio

    relations = await extract_triples(content)
    conn = get_shared_neo4j_connection()
    await asyncio.to_thread(_write_chunk_and_triples, conn.driver, session_id, chunk_id, relations)
    return len(relations)


async def index_chunks_into_graph(session_id: str, chunks: list[dict]) -> int:
    total_relations = 0
    for chunk in chunks:
        total_relations += await index_chunk_into_graph(session_id, chunk["chunk_id"], chunk["content"])
    return total_relations
