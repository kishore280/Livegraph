import sys
from typing import ClassVar

sys.path.insert(0, "package")

from livegraph.storage.redis import get_arq_redis_settings


async def ping(ctx: dict) -> str:
    return "pong"


class WorkerSettings:
    functions: ClassVar[list] = [ping]
    redis_settings = get_arq_redis_settings()
