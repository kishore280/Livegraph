from pydantic import BaseModel, Field

from livegraph.knowledge.milvus_store import get_sample_chunks
from livegraph.models.chat import get_chat_model

BENCHMARK_GENERATION_PROMPT = """Based on the following context, generate one question that can be accurately \
answered from it, plus the gold answer.

Context:
{content}
"""


class BenchmarkItem(BaseModel):
    query: str = Field(description="a question that can be accurately answered from the context")
    gold_answer: str = Field(description="the correct answer to the question, based on the context")


async def generate_benchmark_item(chunk_id: str, content: str) -> dict | None:
    model = get_chat_model().with_structured_output(BenchmarkItem)
    prompt = BENCHMARK_GENERATION_PROMPT.format(content=content)
    result = await model.ainvoke(prompt)
    if not isinstance(result, BenchmarkItem) or not result.query or not result.gold_answer:
        return None
    return {"query": result.query, "gold_answer": result.gold_answer, "gold_chunk_ids": [chunk_id]}


async def generate_benchmark(session_id: str, num_questions: int = 5) -> list[dict]:
    chunks = await get_sample_chunks(session_id, limit=num_questions)
    items = []
    for chunk in chunks:
        item = await generate_benchmark_item(chunk["chunk_id"], chunk["content"])
        if item is not None:
            items.append(item)
    return items
