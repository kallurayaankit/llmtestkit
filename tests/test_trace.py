"""Tests for the trace data model."""

import pytest
from time import time

from llmtestkit.trace import Trace, Score


def test_trace_construction():
    t = Trace(example_id="x", input="q", output="a")
    t.end_time = t.start_time + 0.5
    assert t.trace_id
    assert t.duration_ms == pytest.approx(500.0, abs=1.0)


def test_span_attachment():
    t = Trace(example_id="x", input="q", output="a")
    start = time()
    t.add_span("generation", "generation", start, start + 0.1, model="llama3.2:3b")
    assert len(t.spans) == 1
    assert t.spans[0].duration_ms == pytest.approx(100.0, abs=1.0)


def test_score_attachment():
    t = Trace(example_id="x", input="q", output="a")
    t.add_score(Score(name="test", value=1.0, passed=True))
    assert len(t.scores) == 1
    assert t.scores[0].passed is True


def test_serialization():
    t = Trace(example_id="x", input="q", output="a", reference="a")
    t.end_time = t.start_time + 1.0
    t.add_score(Score(name="exact_match", value=1.0, passed=True))
    d = t.to_dict()
    assert d["example_id"] == "x"
    assert d["scores"][0]["name"] == "exact_match"
