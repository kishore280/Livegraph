import hashlib
import re

CYPHER_MERGE_CHUNK = """
MERGE (c:Chunk:LiveGraph {chunk_id: $chunk_id, session_id: $session_id})
"""

CYPHER_MERGE_ENTITY_MENTION = """
MATCH (c:Chunk:LiveGraph {chunk_id: $chunk_id, session_id: $session_id})
MERGE (e:Entity:LiveGraph {session_id: $session_id, normalized_name: $normalized_name, label: $entity_label})
SET e.entity_id = $entity_id, e.name = $name
MERGE (c)-[m:MENTIONS {chunk_id: $chunk_id, session_id: $session_id}]->(e)
"""

CYPHER_MERGE_RELATION = """
MATCH (source:Entity:LiveGraph {session_id: $session_id, normalized_name: $source_name, label: $source_label})
MATCH (target:Entity:LiveGraph {session_id: $session_id, normalized_name: $target_name, label: $target_label})
MERGE (source)-[r:RELATION {session_id: $session_id, chunk_id: $chunk_id, source_name: $source_name, target_name: $target_name, type: $relation_type}]->(target)
SET r.triple_id = $triple_id, r.text = $text
"""


def normalize_entity_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def compute_entity_id(session_id: str, normalized_name: str, label: str) -> str:
    return hashlib.sha256(f"{session_id}:{normalized_name}:{label}".encode()).hexdigest()[:32]


def compute_triple_id(session_id: str, source_name: str, target_name: str, relation_type: str) -> str:
    return hashlib.sha256(f"{session_id}:{source_name}:{target_name}:{relation_type}".encode()).hexdigest()[:32]
