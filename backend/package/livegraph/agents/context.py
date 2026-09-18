from dataclasses import dataclass, field


@dataclass
class LiveGraphContext:
    session_id: str | None = None
    sources: list[dict[str, str]] = field(default_factory=list)
