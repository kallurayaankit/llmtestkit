"""Tests for metrics. Deterministic only, no LLM."""

from llmtestkit import ExactMatch, Contains, ValidJSON, Trace


def test_exact_match_pass():
    t = Trace(input="q", output="Paris", reference="paris")
    s = ExactMatch().measure(t)
    assert s.value == 1.0
    assert s.passed is True


def test_exact_match_fail():
    t = Trace(input="q", output="London", reference="Paris")
    s = ExactMatch().measure(t)
    assert s.value == 0.0
    assert s.passed is False


def test_contains_pass():
    t = Trace(input="q", output="The capital of France is Paris.", reference="Paris")
    s = Contains().measure(t)
    assert s.value == 1.0


def test_contains_fail():
    t = Trace(input="q", output="London", reference="Paris")
    s = Contains().measure(t)
    assert s.value == 0.0


def test_valid_json_pass():
    t = Trace(input="q", output='{"a": 1}')
    s = ValidJSON().measure(t)
    assert s.value == 1.0


def test_valid_json_fail():
    t = Trace(input="q", output="{not json}")
    s = ValidJSON().measure(t)
    assert s.value == 0.0


def test_missing_reference():
    t = Trace(input="q", output="a")
    s = ExactMatch().measure(t)
    assert s.value == 0.0
    assert "no reference" in s.evidence
