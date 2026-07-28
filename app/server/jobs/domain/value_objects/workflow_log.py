"""WorkflowLog value object — represents processing step entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WorkflowEntry:
    """A single workflow log entry."""
    step: str
    msg: str
    ts: str = field(default_factory=lambda: datetime.now().strftime('%H:%M:%S'))


@dataclass
class WorkflowLog:
    """Value object for job workflow log."""

    entries: list[WorkflowEntry] = field(default_factory=list)

    def add(self, step: str, msg: str) -> None:
        self.entries.append(WorkflowEntry(step=step, msg=msg))

    def to_json(self) -> str:
        import json
        return json.dumps([
            {"step": e.step, "msg": e.msg, "ts": e.ts}
            for e in self.entries
        ])

    @classmethod
    def from_json(cls, data: str) -> WorkflowLog:
        import json
        try:
            entries = json.loads(data)
            return cls(entries=[
                WorkflowEntry(step=e["step"], msg=e["msg"], ts=e.get("ts", ""))
                for e in entries
            ])
        except (json.JSONDecodeError, KeyError):
            return cls()
