"""Base metric protocol."""

from abc import ABC, abstractmethod

from llmtestkit.trace import Score, Trace


class Metric(ABC):
    """Every metric is a class with a measure() method."""

    name: str = "unnamed"
    threshold: float = 0.5

    @abstractmethod
    def measure(self, trace: Trace) -> Score:
        ...

    def _score(self, value: float, evidence: str = "", **kwargs) -> Score:
        value = max(0.0, min(1.0, value))
        return Score(
            name=self.name,
            value=value,
            passed=value >= self.threshold,
            threshold=self.threshold,
            evidence=evidence,
            **kwargs,
        )
