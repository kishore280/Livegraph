
from fastapi import APIRouter

router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/health")
async def health():
    return {"status": "alive"}

@router.get("/ready")
async def ready():
    pass
