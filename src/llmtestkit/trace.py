"""Trace, Span, and Score data model.

A Trace is one evaluation run: input, output, and everything in between.
Spans capture intermediate steps (retrieval, generation, tool calls).
Scores attach to the trace with full provenance so any verdict is auditable.
"""

from dataclasses import dataclass, field, asdict
from time import time
from uuid import uuid4


@dataclass
class Span:
    span_id: str
    name: str
    span_type: str
    start_time: float
    end_time: float
    attributes: dict = field(default_factory=dict)
    parent_id: str | None = None

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["duration_ms"] = self.duration_ms
        return d


@dataclass
class Score:
    name: str
    value: float
    passed: bool
    threshold: float = 0.5
    error: bool = False
    judge_model: str | None = None
    judge_prompt_hash: str | None = None
    rubric_version: str | None = None
    evidence: str = ""
    latency_ms: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Trace:
    trace_id: str = field(default_factory=lambda: uuid4().hex[:12])
    example_id: str = ""
    input: str = ""
    output: str = ""
    reference: str | None = None
    context: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    spans: list[Span] = field(default_factory=list)
    scores: list[Score] = field(default_factory=list)
    start_time: float = field(default_factory=time)
    end_time: float = 0.0

    def add_span(self, name, span_type, start, end, **attrs) -> Span:
        s = Span(
            span_id=uuid4().hex[:8],
            name=name,
            span_type=span_type,
            start_time=start,
            end_time=end,
            attributes=attrs,
        )
        self.spans.append(s)
        return s

    def add_score(self, score: Score) -> None:
        self.scores.append(score)

    @property
    def duration_ms(self) -> float:
        if self.end_time == 0:
            return 0.0
        return (self.end_time - self.start_time) * 1000.0

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "example_id": self.example_id,
            "input": self.input,
            "output": self.output,
            "reference": self.reference,
            "context": self.context,
            "metadata": self.metadata,
            "spans": [s.to_dict() for s in self.spans],
            "scores": [s.to_dict() for s in self.scores],
            "duration_ms": self.duration_ms,
        }
