import uuid

from livegraph.knowledge.eval.benchmark_generation import generate_benchmark
from livegraph.knowledge.eval.evaluator import evaluate_question
from livegraph.knowledge.eval.metrics import calculate_overall_score
from livegraph.repositories.eval_run_repository import EvalRunRepository
from livegraph.storage.postgres.manager import get_postgres_manager


async def run_evaluation(*, session_id: str, num_questions: int = 5) -> dict:
    benchmark = await generate_benchmark(session_id, num_questions=num_questions)

    manager = get_postgres_manager()
    async with manager.get_session() as db:
        repo = EvalRunRepository(db)
        run = await repo.create(run_id=uuid.uuid4().hex, session_id=session_id, total_items=len(benchmark))
        await db.commit()
        run_id = run.run_id

    item_metrics = []
    for idx, item in enumerate(benchmark):
        result = await evaluate_question(
            session_id=session_id,
            query=item["query"],
            gold_answer=item["gold_answer"],
            gold_chunk_ids=item["gold_chunk_ids"],
        )
        item_metrics.append(result["metrics"])

        async with manager.get_session() as db:
            repo = EvalRunRepository(db)
            run = await repo.get_by_run_id(run_id)
            await repo.add_item(run, item_index=idx, item_data=result)
            await db.commit()

    overall_score = calculate_overall_score(item_metrics)
    aggregate_metrics = {}
    if item_metrics:
        for key in item_metrics[0]:
            if isinstance(item_metrics[0][key], int | float):
                aggregate_metrics[key] = sum(m.get(key, 0.0) for m in item_metrics) / len(item_metrics)

    async with manager.get_session() as db:
        repo = EvalRunRepository(db)
        run = await repo.get_by_run_id(run_id)
        await repo.finalize(run, overall_score=overall_score, metrics=aggregate_metrics)
        await db.commit()
        return run.to_dict()


async def list_evaluation_runs(*, session_id: str) -> list[dict]:
    manager = get_postgres_manager()
    async with manager.get_session() as db:
        runs = await EvalRunRepository(db).list_by_session(session_id)
        return [r.to_dict() for r in runs]


async def get_evaluation_run(*, session_id: str, run_id: str) -> dict | None:
    manager = get_postgres_manager()
    async with manager.get_session() as db:
        run = await EvalRunRepository(db).get_with_items(run_id)
        if run is None or run.session_id != session_id:
            return None
        result = run.to_dict()
        result["items"] = [item.to_dict() for item in sorted(run.items, key=lambda i: i.item_index)]
        return result
