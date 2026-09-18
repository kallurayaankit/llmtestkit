"""Load attack definitions from YAML files."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


DEFAULT_ATTACKS_DIR = Path(__file__).parent.parent.parent.parent / "attacks"


@dataclass
class Attack:
    id: str
    name: str
    severity: str
    family: str = ""
    payload: str = ""
    turns: list[str] = field(default_factory=list)
    success_signals: list[str] = field(default_factory=list)
    refusal_signals: list[str] = field(default_factory=list)

    @property
    def is_multi_turn(self) -> bool:
        return bool(self.turns)

    @property
    def full_text(self) -> str:
        if self.turns:
            return "\n---\n".join(self.turns)
        return self.payload


def load_attacks(attacks_dir=None, families=None) -> list:
    base = Path(attacks_dir) if attacks_dir else DEFAULT_ATTACKS_DIR
    if not base.exists():
        raise FileNotFoundError(f"attacks directory not found: {base}")

    files = sorted(base.glob("*.yaml"))
    if families:
        wanted = {f.lower() for f in families}
        files = [f for f in files if f.stem.lower() in wanted]

    attacks = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            entries = yaml.safe_load(f) or []
        for entry in entries:
            attacks.append(Attack(
                id=entry["id"],
                name=entry["name"],
                severity=entry.get("severity", "medium"),
                family=path.stem,
                payload=(entry.get("payload") or "").strip(),
                turns=[t.strip() for t in (entry.get("turns") or [])],
                success_signals=[s.lower() for s in entry.get("success_signals", [])],
                refusal_signals=[s.lower() for s in entry.get("refusal_signals", [])],
            ))
    return attacks


def list_families(attacks_dir=None) -> list:
    base = Path(attacks_dir) if attacks_dir else DEFAULT_ATTACKS_DIR
    if not base.exists():
        return []
    return sorted(p.stem for p in base.glob("*.yaml"))
