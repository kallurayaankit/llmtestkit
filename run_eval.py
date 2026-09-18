"""First end-to-end eval with HTML report."""

from llmtestkit import evaluate, metrics, render_report


report = evaluate(
    model="llama3.2:3b",
    dataset="datasets/qa/general_qa.jsonl",
    metrics=[
        metrics.ExactMatch(),
        metrics.Contains(),
        metrics.Correctness(),
    ],
    suite_name="qa-general",
)

print("\n--- summary ---")
for name, stats in report.aggregate().items():
    print(f"{name}: mean={stats['mean']:.2f} pass_rate={stats['pass_rate']:.2f}")

print(f"\nTotal time: {report.duration_s:.1f}s")
print(f"Failures: {len(report.failures())}")

path = render_report(report)
print(f"\nReport: {path}")