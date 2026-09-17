from fastapi import APIRouter

from livegraph.knowledge.graphs.query import get_subgraph

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/{session_id}/subgraph")
async def read_subgraph(session_id: str, max_nodes: int = 200):
    return await get_subgraph(session_id, max_nodes=max_nodes)
