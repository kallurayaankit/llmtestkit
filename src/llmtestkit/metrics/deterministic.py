"""Deterministic metrics. No LLM calls, instant results."""

import json
import re

from llmtestkit.metrics.base import Metric
from llmtestkit.trace import Score, Trace


def _normalize(text: str) -> str:
    text = text.lower().strip()
    replacements = {
        "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-",
        "\u00a0": " ",
    }
    for curly, straight in replacements.items():
        text = text.replace(curly, straight)
    return text


class ExactMatch(Metric):
    name = "exact_match"
    threshold = 1.0

    def measure(self, trace: Trace) -> Score:
        if trace.reference is None:
            return self._score(0.0, "no reference provided")
        match = _normalize(trace.output) == _normalize(trace.reference)
        return self._score(1.0 if match else 0.0, f"output {'matches' if match else 'differs from'} reference")


class Contains(Metric):
    name = "contains"
    threshold = 1.0

    def measure(self, trace: Trace) -> Score:
        if trace.reference is None:
            return self._score(0.0, "no reference provided")
        hit = _normalize(trace.reference) in _normalize(trace.output)
        return self._score(1.0 if hit else 0.0, f"reference {'found' if hit else 'not found'} in output")


class ValidJSON(Metric):
    name = "valid_json"
    threshold = 1.0

    def measure(self, trace: Trace) -> Score:
        try:
            json.loads(trace.output)
            return self._score(1.0, "parsed successfully")
        except json.JSONDecodeError as e:
            return self._score(0.0, f"parse error: {e.msg}")
