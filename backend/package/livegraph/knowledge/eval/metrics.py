from pydantic import BaseModel, Field

from livegraph.models.chat import get_chat_model

JUDGE_PROMPT = """You are a fair judge. Evaluate whether the AI-generated answer is factually consistent with \
the standard answer for the given question. Ignore wording, punctuation, and formatting differences \
- only judge whether the core facts match.

Question: {question}
Standard answer: {gold_answer}
AI-generated answer: {generated_answer}
"""


class JudgeResult(BaseModel):
    score: float = Field(description="1.0 if the answer is factually correct, 0.0 if it is not")
    reasoning: str = Field(description="brief explanation of the judgment")


def precision_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    return len(set(top_k) & set(relevant_ids)) / k


def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    return len(set(retrieved_ids[:k]) & set(relevant_ids)) / len(set(relevant_ids))


def f1_score_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    p = precision_at_k(retrieved_ids, relevant_ids, k)
    r = recall_at_k(retrieved_ids, relevant_ids, k)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def calculate_retrieval_metrics(
    retrieved_ids: list[str], relevant_ids: list[str], k_values: list[int] | None = None
) -> dict[str, float]:
    k_values = k_values or [1, 3, 5]
    metrics: dict[str, float] = {}
    for k in k_values:
        metrics[f"recall@{k}"] = recall_at_k(retrieved_ids, relevant_ids, k)
        metrics[f"f1@{k}"] = f1_score_at_k(retrieved_ids, relevant_ids, k)
    return metrics


async def judge_correctness(question: str, gold_answer: str, generated_answer: str) -> dict:
    model = get_chat_model().with_structured_output(JudgeResult)
    prompt = JUDGE_PROMPT.format(question=question, gold_answer=gold_answer, generated_answer=generated_answer)
    result = await model.ainvoke(prompt)
    if not isinstance(result, JudgeResult):
        return {"score": 0.0, "reasoning": "Could not parse judge response"}
    return {"score": result.score, "reasoning": result.reasoning}


def calculate_overall_score(item_metrics: list[dict]) -> float:
    judge_scores = [m["judge_score"] for m in item_metrics if "judge_score" in m]
    if judge_scores:
        return sum(judge_scores) / len(judge_scores)

    recall_5_scores = [m.get("recall@5", 0.0) for m in item_metrics]
    if not recall_5_scores:
        return 0.0
    return sum(recall_5_scores) / len(recall_5_scores)
