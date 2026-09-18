"""llmtestkit - a testing framework for LLM and AI systems."""

from llmtestkit.trace import Trace, Span, Score
from llmtestkit.client import BaseClient, OllamaClient, get_client
from llmtestkit.dataset import Dataset, Example, load_jsonl
from llmtestkit.metrics import Metric, ExactMatch, Contains, ValidJSON, Correctness
from llmtestkit.runner import Report, run_suite, evaluate
from llmtestkit.report import render_report
from llmtestkit import security

__version__ = "0.1.0"

__all__ = [
    "Trace", "Span", "Score",
    "BaseClient", "OllamaClient", "get_client",
    "Dataset", "Example", "load_jsonl",
    "Metric", "ExactMatch", "Contains", "ValidJSON", "Correctness",
    "Report", "run_suite", "evaluate",
    "render_report",
    "security",
]
