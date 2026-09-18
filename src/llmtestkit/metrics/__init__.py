from llmtestkit.metrics.base import Metric
from llmtestkit.metrics.deterministic import Contains, ExactMatch, ValidJSON
from llmtestkit.metrics.correctness import Correctness

METRIC_REGISTRY = {
    "exact_match": ExactMatch,
    "contains": Contains,
    "valid_json": ValidJSON,
    "correctness": Correctness,
}


def make_metric(spec: dict) -> Metric:
    """Instantiate a metric from a dict spec like {"name": "correctness", "threshold": 0.8}."""
    if "name" not in spec:
        raise ValueError("metric spec missing 'name'")
    name = spec["name"]
    cls = METRIC_REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(METRIC_REGISTRY))
        raise ValueError(f"unknown metric '{name}'. Available: {available}")

    kwargs = {k: v for k, v in spec.items() if k != "name"}
    try:
        return cls(**kwargs)
    except TypeError:
        m = cls()
        for k, v in kwargs.items():
            setattr(m, k, v)
        return m


__all__ = [
    "Metric",
    "ExactMatch",
    "Contains",
    "ValidJSON",
    "Correctness",
    "METRIC_REGISTRY",
    "make_metric",
]
