from dataclasses import dataclass


@dataclass
class LiveGraphContext:
    session_id: str | None = None
