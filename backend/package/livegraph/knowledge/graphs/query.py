import asyncio

from livegraph.storage.neo4j.manager import get_shared_neo4j_connection, neo4j_read

CYPHER_FETCH_ENTITIES = """
MATCH (e:Entity:LiveGraph {session_id: $session_id})
RETURN e.entity_id AS id, e.name AS name, e.label AS type
LIMIT $max_nodes
"""

CYPHER_FETCH_RELATIONS = """
MATCH (s:Entity:LiveGraph {session_id: $session_id})-[r:RELATION {session_id: $session_id}]->(t:Entity:LiveGraph {session_id: $session_id})
RETURN r.triple_id AS id, s.entity_id AS source_id, t.entity_id AS target_id, r.type AS type
LIMIT $max_edges
"""


def _fetch_subgraph(session_id: str, max_nodes: int) -> dict:
    conn = get_shared_neo4j_connection()

    node_rows = neo4j_read(
        conn.driver, CYPHER_FETCH_ENTITIES, session_id=session_id, max_nodes=max_nodes
    )
    node_ids = {row["id"] for row in node_rows}

    edge_rows = neo4j_read(
        conn.driver, CYPHER_FETCH_RELATIONS, session_id=session_id, max_edges=max_nodes * 5
    )
    edges = [row for row in edge_rows if row["source_id"] in node_ids and row["target_id"] in node_ids]

    return {"nodes": node_rows, "edges": edges}


async def get_subgraph(session_id: str, max_nodes: int = 200) -> dict:
    return await asyncio.to_thread(_fetch_subgraph, session_id, max_nodes)
