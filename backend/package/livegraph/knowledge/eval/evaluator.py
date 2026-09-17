from livegraph.knowledge.eval.metrics import calculate_retrieval_metrics, judge_correctness
from livegraph.knowledge.milvus_store import search
from livegraph.models.chat import get_chat_model

ANSWER_PROMPT = """Based on the following context, answer the user's question.

Context:
{context}

Question: {question}

Answer accurately based on the context above. If the context lacks relevant information, \
respond "insufficient information to answer".
"""


async def _generate_answer(query: str, retrieved_chunks: list[dict]) -> str:
    context = "\n\n".join(f"Document {i + 1}:\n{c['content']}" for i, c in enumerate(retrieved_chunks[:5]))
    model = get_chat_model()
    response = await model.ainvoke(ANSWER_PROMPT.format(context=context, question=query))
    return response.content if isinstance(response.content, str) else str(response.content)


async def evaluate_question(*, session_id: str, query: str, gold_answer: str, gold_chunk_ids: list[str]) -> dict:
    retrieved_chunks = await search(session_id, query, top_k=5)
    generated_answer = await _generate_answer(query, retrieved_chunks)

    retrieved_ids = [str(c.get("chunk_id", "")) for c in retrieved_chunks]
    retrieval_metrics = calculate_retrieval_metrics(retrieved_ids, gold_chunk_ids)

    judge_result = await judge_correctness(query, gold_answer, generated_answer)
    item_metrics = {
        **retrieval_metrics,
        "judge_score": judge_result["score"],
        "judge_reasoning": judge_result["reasoning"],
    }

    return {
        "query_text": query,
        "gold_chunk_ids": gold_chunk_ids,
        "gold_answer": gold_answer,
        "generated_answer": generated_answer,
        "retrieved_chunk_ids": retrieved_ids,
        "metrics": item_metrics,
    }
