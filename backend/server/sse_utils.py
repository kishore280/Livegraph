from __future__ import annotations

import json

SSE_HEARTBEAT_SECONDS = 15
SSE_POLL_INTERVAL_SECONDS = 1.0
SSE_MAX_CONNECTION_MINUTES = 30

def format_sse(data:dict, event:str, event_id:str | None = None) -> str:
    lines = [f"event:{event}", f"data:{json.dumps(data, ensure_ascii=False)}"]
    if event_id is not None:
        lines.append(f"id:{event_id}")
    lines.append("")
    return "\n".join(lines)+ "\n"


def format_heartbeat() -> str:
    return ":heartbeat: \n\n"