"""Tests for the dataset loader."""

import pytest

from llmtestkit.dataset import load_jsonl


SAMPLE = "datasets/qa/general_qa.jsonl"


def test_load_sample():
    ds = load_jsonl(SAMPLE)
    assert len(ds) == 5
    assert ds.examples[0].id == "qa-001"


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_jsonl("does/not/exist.jsonl")


def test_filter():
    ds = load_jsonl(SAMPLE)
    geo = ds.filter(category="geography")
    assert len(geo) >= 1
