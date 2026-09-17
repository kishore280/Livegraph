from langchain_core.tools import tool
from langgraph.prebuilt.tool_node import ToolRuntime

from livegraph.knowledge.chunking import chunk_text
from livegraph.knowledge.graphs.service import index_chunks_into_graph
from livegraph.knowledge.milvus_store import add_chunks, search


@tool
async def web_search(query: str, runtime: ToolRuntime) -> str:
    """Search the web for information relevant to the query. Results are saved for later reuse this session."""
    from tavily import AsyncTavilyClient

    from livegraph.config import settings

    session_id = str(getattr(runtime.context, "session_id", "") or "")
    if not session_id:
        return "No session context available."
    if not settings.tavily_api_key:
        return "Web search is not configured (missing Tavily API key)."

    client = AsyncTavilyClient(settings.tavily_api_key)
    response = await client.search(query, max_results=5)
    results = response.get("results", [])
    if not results:
        return "No web results found."

    all_chunks: list[str] = []
    for result in results:
        content = result.get("content") or ""
        if content:
            all_chunks.extend(chunk_text(content))

    if all_chunks:
        added = await add_chunks(session_id, all_chunks)
        await index_chunks_into_graph(session_id, added)

    return "\n\n".join(
        f"[{r.get('title', '')}]({r.get('url', '')})\n{r.get('content', '')}" for r in results
    )


@tool
async def search_session(query_text: str, runtime: ToolRuntime) -> str:
    """Search content already gathered this session for information relevant to the query."""
    session_id = str(getattr(runtime.context, "session_id", "") or "")
    if not session_id:
        return "No session context available."

    results = await search(session_id, query_text)
    if not results:
        return "No relevant content found in this session yet."

    return "\n\n".join(f"[score={r['score']:.4f}] {r['content']}" for r in results)
