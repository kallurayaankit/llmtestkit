"""Run a metric suite against a dataset."""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from time import time

from llmtestkit.client import OllamaClient
from llmtestkit.dataset import Dataset
from llmtestkit.metrics.base import Metric
from llmtestkit.trace import Score, Trace


@dataclass
class Report:
    dataset_path: str
    suite_name: str
    metrics: list[str]
    traces: list[Trace] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def duration_s(self) -> float:
        if self.end_time == 0:
            return 0.0
        return self.end_time - self.start_time

    def aggregate(self) -> dict:
        buckets = {}
        for t in self.traces:
            for s in t.scores:
                if s.error:
                    buckets.setdefault(f"{s.name}__errors", []).append(s)
                    continue
                buckets.setdefault(s.name, []).append(s)

        summary = {}
        for name, scores in buckets.items():
            n = len(scores)
            values = [s.value for s in scores]
            passes = sum(1 for s in scores if s.passed)
            summary[name] = {
                "n": n,
                "mean": sum(values) / n if n else 0.0,
                "min": min(values) if n else 0.0,
                "max": max(values) if n else 0.0,
                "pass_rate": passes / n if n else 0.0,
            }
        return summary

    def failures(self):
        return [t for t in self.traces if any(not s.passed for s in t.scores)]


def _run_one_metric(metric, trace):
    try:
        return metric.measure(trace)
    except Exception as e:
        return Score(name=metric.name, value=0.0, passed=False,
                     evidence=f"metric raised: {type(e).__name__}: {e}", error=True)


def _evaluate_one(ex, metrics, model):
    client = OllamaClient(model=model)
    trace = Trace(
        example_id=ex.id,
        input=ex.input,
        reference=ex.reference,
        context=ex.context,
        metadata=ex.metadata,
    )
    start = time()
    output = client.generate(ex.input, timeout=300, temperature=0.0)
    end = time()
    trace.output = output
    trace.add_span("generation", "generation", start, end, model=client.model)
    trace.end_time = end

    with ThreadPoolExecutor(max_workers=len(metrics)) as pool:
        futures = [pool.submit(_run_one_metric, m, trace) for m in metrics]
        for fut in as_completed(futures):
            trace.add_score(fut.result())
    return trace


def run_suite(dataset: Dataset, metrics: list, suite_name="default", model=None, max_workers=2) -> Report:
    report = Report(
        dataset_path=dataset.path,
        suite_name=suite_name,
        metrics=[m.name for m in metrics],
        start_time=time(),
    )
    examples = list(dataset)
    lock = threading.Lock()
    state = [0]

    def worker(ex):
        trace = _evaluate_one(ex, metrics, model)
        with lock:
            state[0] += 1
            scores = {s.name: f"{s.value:.2f}" for s in trace.scores}
            print(f"  [{state[0]}/{len(examples)}] {ex.id}  {scores}")
        return trace

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for fut in as_completed([pool.submit(worker, ex) for ex in examples]):
            report.traces.append(fut.result())

    order = {ex.id: i for i, ex in enumerate(examples)}
    report.traces.sort(key=lambda t: order.get(t.example_id, 999999))
    report.end_time = time()
    return report


def evaluate(model, dataset, metrics, suite_name="default"):
    """Convenience one-liner: load dataset + run suite."""
    from llmtestkit.dataset import load_jsonl
    if isinstance(dataset, str):
        dataset = load_jsonl(dataset)
    return run_suite(dataset, metrics, suite_name=suite_name, model=model)
