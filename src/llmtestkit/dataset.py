"""JSONL dataset loader."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Example:
    id: str
    input: str
    reference: str | None = None
    context: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class Dataset:
    def __init__(self, examples, path=""):
        self.examples = examples
        self.path = path

    def __len__(self):
        return len(self.examples)

    def __iter__(self):
        return iter(self.examples)

    def filter(self, **criteria):
        def matches(ex):
            return all(ex.metadata.get(k) == v for k, v in criteria.items())
        return Dataset([e for e in self.examples if matches(e)], self.path)


def load_jsonl(path) -> Dataset:
    path = Path(path)
    if not path.exists():
        base = os.getenv("DATASETS_DIR")
        if base:
            alt = Path(base) / path
            if alt.exists():
                path = alt
    if not path.exists():
        raise FileNotFoundError(f"dataset not found: {path}")

    examples = []
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            examples.append(Example(
                id=data["id"],
                input=data["input"],
                reference=data.get("reference"),
                context=data.get("context") or [],
                metadata=data.get("metadata") or {},
            ))
    return Dataset(examples, str(path))
