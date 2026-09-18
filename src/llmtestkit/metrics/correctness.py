"""Correctness judge: semantic match against a reference."""

from dataclasses import dataclass

from llmtestkit.metrics.judge_base import JudgeBase
from llmtestkit.trace import Trace


PROMPT = """You are an expert evaluator. Grade the model's answer against the reference.

QUESTION:
__INPUT__

MODEL ANSWER:
__OUTPUT__

REFERENCE ANSWER (ground truth):
__REFERENCE__

RUBRIC:
- 1.0 if the model answer conveys the same meaning as the reference.
- 0.7-0.9 if mostly correct but misses a minor detail.
- 0.4-0.6 if partially correct or vague.
- 0.1-0.3 if mostly wrong but mentions something relevant.
- 0.0 if wrong, off-topic, or refuses without cause.

Think step by step, then output a JSON object with keys score, confidence, reason.
score is a float from 0.0 to 1.0. reason is one short sentence.
"""


@dataclass
class Correctness(JudgeBase):
    name: str = "correctness"
    threshold: float = 0.7
    rubric_version: str = "v1"
    prompt_template: str = PROMPT
    score_key: str = "score"

    def __post_init__(self):
        super().__post_init__()

    def build_prompt(self, trace: Trace) -> str:
        return (
            PROMPT
            .replace("__INPUT__", trace.input)
            .replace("__OUTPUT__", trace.output)
            .replace("__REFERENCE__", trace.reference or "")
        )
