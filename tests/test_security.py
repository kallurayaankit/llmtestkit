"""Tests for the security module. Deterministic only."""

from llmtestkit.security.loader import load_attacks, list_families
from llmtestkit.security.scorer import score_attack


def test_families_loaded():
    fams = list_families()
    assert len(fams) > 0


def test_attacks_loaded():
    attacks = load_attacks()
    assert len(attacks) > 0
    assert all(a.id for a in attacks)


def test_denial_scores_resisted():
    """Response that denies having info = RESISTED."""
    attacks = load_attacks(families=["direct_injection"])
    attack = next(a for a in attacks if a.id == "di-002")
    response = "I don't have a system prompt to repeat."
    score = score_attack(attack, response)
    assert score.passed is True


def test_refusal_scores_resisted():
    """Response containing 'cannot' = RESISTED without judge call."""
    attacks = load_attacks(families=["jailbreak"])
    attack = attacks[0]
    response = "I cannot help with that request."
    score = score_attack(attack, response)
    assert score.passed is True
