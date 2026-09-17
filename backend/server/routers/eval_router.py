from fastapi import APIRouter, Body, HTTPException

from livegraph.services import eval_service

router = APIRouter(prefix="/api/sessions", tags=["eval"])


@router.post("/{session_id}/eval")
async def run_evaluation(session_id: str, num_questions: int = Body(5, embed=True)):
    return await eval_service.run_evaluation(session_id=session_id, num_questions=num_questions)


@router.get("/{session_id}/eval")
async def list_evaluation_runs(session_id: str):
    runs = await eval_service.list_evaluation_runs(session_id=session_id)
    return {"runs": runs}


@router.get("/{session_id}/eval/{run_id}")
async def get_evaluation_run(session_id: str, run_id: str):
    run = await eval_service.get_evaluation_run(session_id=session_id, run_id=run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return run
