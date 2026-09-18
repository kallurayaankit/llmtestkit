"""Shared base for LLM-as-a-judge metrics.

Handles caching (thread-safe), prompt substitution, and JSON parsing.
Subclasses declare a prompt template and score key.
"""

import hashlib
import json
import os
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from llmtestkit.client import OllamaClient
from llmtestkit.metrics.base import Metric
from llmtestkit.trace import Score, Trace

load_dotenv()

CACHE_PATH = Path.home() / ".cache" / "llmtestkit" / "judge_cache.json"
_CACHE_LOCK = threading.Lock()


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _cache_key(prompt: str, model: str) -> str:
    h = hashlib.sha256()
    h.update(prompt.encode())
    h.update(b"\x00")
    h.update(model.encode())
    return h.hexdigest()


def _extract_json(text: str) -> dict:
    matches = re.findall(r"\{[^{}]*\}", text, re.DOTALL)
    if not matches:
        raise ValueError(f"no JSON in judge response: {text[:200]}")
    return json.loads(matches[-1])


@dataclass
class JudgeBase(Metric):
    name: str = "judge"
    threshold: float = 0.7
    rubric_version: str = "v1"
    prompt_template: str = ""
    score_key: str = "score"

    def __post_init__(self):
        self.model = os.getenv("JUDGE_MODEL", "mistral:latest")
        self.prompt_hash = hashlib.sha256(self.prompt_template.encode()).hexdigest()[:12]

    def build_prompt(self, trace: Trace) -> str:
        raise NotImplementedError

    def measure(self, trace: Trace) -> Score:
        prompt = self.build_prompt(trace)

        with _CACHE_LOCK:
            cache = _load_cache()
            key = _cache_key(prompt, self.model)
            cached = cache.get(key)

        if cached is not None:
            return self._score(
                cached["value"],
                evidence=cached["evidence"] + " [cached]",
                judge_model=self.model,
                judge_prompt_hash=self.prompt_hash,
                rubric_version=self.rubric_version,
                latency_ms=0.0,
            )

        client = OllamaClient(model=self.model)
        start = time.time()
        try:
            raw = client.generate(prompt, timeout=300, temperature=0.0)
            latency_ms = (time.time() - start) * 1000.0
            data = _extract_json(raw)
            value = float(data.get(self.score_key, 0.0))
            evidence = data.get("reason", "")
        except Exception as e:
            latency_ms = (time.time() - start) * 1000.0
            return Score(
                name=self.name,
                value=0.0,
                passed=False,
                threshold=self.threshold,
                evidence=f"JUDGE_ERROR: {type(e).__name__}: {str(e)[:150]}",
                judge_model=self.model,
                judge_prompt_hash=self.prompt_hash,
                rubric_version=self.rubric_version,
                latency_ms=latency_ms,
                error=True,
            )

        with _CACHE_LOCK:
            cache = _load_cache()
            cache[key] = {"value": value, "evidence": evidence}
            _save_cache(cache)

        return self._score(
            value,
            evidence=evidence,
            judge_model=self.model,
            judge_prompt_hash=self.prompt_hash,
            rubric_version=self.rubric_version,
            latency_ms=latency_ms,
        )
