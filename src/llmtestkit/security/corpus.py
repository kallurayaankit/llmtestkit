"""Run the attack corpus against a model."""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time

from llmtestkit.client import OllamaClient
from llmtestkit.runner import Report
from llmtestkit.security.loader import load_attacks
from llmtestkit.security.scorer import score_attack
from llmtestkit.trace import Trace


def run_redteam(model="llama3.2:3b", families=None, attacks_dir=None,
                judge_model="mistral:latest", max_workers=2) -> Report:
    attacks = load_attacks(attacks_dir=attacks_dir, families=families)

    report = Report(
        dataset_path=str(attacks_dir or "bundled"),
        suite_name="redteam",
        metrics=["resisted"],
        start_time=time(),
    )

    lock = threading.Lock()
    state = [0]
    total = len(attacks)

    def run_one(attack):
        client = OllamaClient(model=model)
        trace = Trace(
            example_id=attack.id,
            input=attack.full_text,
            metadata={"attack_name": attack.name, "severity": attack.severity, "family": attack.family},
        )
        start = time()
        if attack.is_multi_turn:
            output = client.chat(attack.turns, timeout=300)
        else:
            output = client.generate(attack.payload, timeout=300)
        end = time()
        trace.output = output
        trace.add_span("generation", "generation", start, end, model=model)
        trace.end_time = end

        score = score_attack(attack, output, judge_model=judge_model)
        trace.add_score(score)

        with lock:
            state[0] += 1
            verdict = "RESISTED" if score.passed else ("ERROR" if score.error else "COMPLIED")
            print(f"  [{state[0]}/{total}] {attack.id} ({attack.severity}) -> {verdict}")

        return trace

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(run_one, a) for a in attacks]
        for fut in as_completed(futures):
            report.traces.append(fut.result())

    order = {a.id: i for i, a in enumerate(attacks)}
    report.traces.sort(key=lambda t: order.get(t.example_id, 999999))
    report.end_time = time()
    return report
