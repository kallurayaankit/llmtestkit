"""Command-line interface for llmtestkit.

    llmtest run <suite.yaml>
    llmtest redteam --model llama3.2:3b
    llmtest list
    llmtest version
"""

import argparse
import sys
import webbrowser
from pathlib import Path

import yaml

from llmtestkit import __version__
from llmtestkit.metrics import METRIC_REGISTRY, make_metric
from llmtestkit.runner import evaluate
from llmtestkit.report import render_report
from llmtestkit.security import run_redteam, list_families


def _load_suite(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"error: suite file not found: {path}", file=sys.stderr)
        sys.exit(2)
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def cmd_run(args):
    suite = _load_suite(args.suite)
    name = suite.get("suite_name", "suite")
    model = args.model or suite.get("model", "llama3.2:3b")
    dataset = suite.get("dataset")
    if not dataset:
        print("error: suite YAML must specify 'dataset'", file=sys.stderr)
        sys.exit(2)
    metric_specs = suite.get("metrics", [])
    if not metric_specs:
        print("error: suite YAML must specify 'metrics'", file=sys.stderr)
        sys.exit(2)
    metrics = [make_metric(spec) for spec in metric_specs]

    print(f"Suite:    {name}")
    print(f"Model:    {model}")
    print(f"Dataset:  {dataset}")
    print(f"Metrics:  {', '.join(m.name for m in metrics)}")
    print()

    report = evaluate(model=model, dataset=dataset, metrics=metrics, suite_name=name)

    print()
    print("--- summary ---")
    for mname, stats in report.aggregate().items():
        print(f"  {mname}: mean={stats['mean']:.2f}  pass_rate={stats['pass_rate']:.2f}  n={stats['n']}")
    print()
    print(f"Duration: {report.duration_s:.1f}s")
    print(f"Failures: {len(report.failures())}")

    path = render_report(report, args.output)
    print(f"Report:   {path}")
    if args.open:
        webbrowser.open(f"file:///{Path(path).resolve()}")
    if len(report.failures()) > 0 and args.fail_on_error:
        sys.exit(1)


def cmd_redteam(args):
    families = args.families.split(",") if args.families else None
    available = list_families()
    if not available:
        print("error: no attack YAMLs found in attacks/", file=sys.stderr)
        sys.exit(2)

    if families:
        bad = [f for f in families if f not in available]
        if bad:
            print(f"error: unknown family(ies): {bad}", file=sys.stderr)
            print(f"available: {available}", file=sys.stderr)
            sys.exit(2)

    print(f"Model:    {args.model}")
    print(f"Judge:    {args.judge or 'mistral:latest'}")
    print(f"Families: {families or 'all'}")
    print()

    report = run_redteam(
        model=args.model,
        families=families,
        judge_model=args.judge or "mistral:latest",
        max_workers=args.workers,
    )

    print()
    print("--- summary ---")
    for mname, stats in report.aggregate().items():
        print(f"  {mname}: mean={stats['mean']:.2f}  pass_rate={stats['pass_rate']:.2f}  n={stats['n']}")
    print()
    print(f"Duration: {report.duration_s:.1f}s")
    print(f"Vulnerabilities found: {len(report.failures())}")

    out = args.output or f"reports/redteam-{report.start_time:.0f}.html"
    path = render_report(report, out)
    print(f"Report:   {path}")
    if args.open:
        webbrowser.open(f"file:///{Path(path).resolve()}")
    if len(report.failures()) > 0 and args.fail_on_error:
        sys.exit(1)


def cmd_families(args):
    fams = list_families()
    if not fams:
        print("No attack families found. Run: python make_corpus.py")
        return
    print("Attack families:")
    for f in fams:
        print(f"  {f}")


def cmd_list(args):
    print("Available metrics:")
    for name in sorted(METRIC_REGISTRY):
        print(f"  {name}")


def cmd_version(args):
    print(f"llmtestkit {__version__}")


def main():
    parser = argparse.ArgumentParser(
        prog="llmtest",
        description="llmtestkit - a testing framework for LLM and AI systems",
    )
    parser.add_argument("--version", action="version", version=f"llmtestkit {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="run a metric suite from a YAML file")
    p_run.add_argument("suite", help="path to suite YAML")
    p_run.add_argument("--model", help="override model from suite")
    p_run.add_argument("--output", help="output path for HTML report")
    p_run.add_argument("--open", action="store_true", help="open report in browser")
    p_run.add_argument("--fail-on-error", action="store_true", help="exit non-zero on failure")
    p_run.set_defaults(func=cmd_run)

    p_rt = sub.add_parser("redteam", help="run the prompt-injection / jailbreak corpus")
    p_rt.add_argument("--model", default="llama3.2:3b", help="model to attack")
    p_rt.add_argument("--judge", help="judge model (default: mistral:latest)")
    p_rt.add_argument("--families", help="comma-separated families (e.g. direct_injection,jailbreak)")
    p_rt.add_argument("--workers", type=int, default=2, help="parallel workers")
    p_rt.add_argument("--output", help="output path for HTML report")
    p_rt.add_argument("--open", action="store_true", help="open report in browser")
    p_rt.add_argument("--fail-on-error", action="store_true", help="exit non-zero if any attack succeeds")
    p_rt.set_defaults(func=cmd_redteam)

    p_fam = sub.add_parser("families", help="list available attack families")
    p_fam.set_defaults(func=cmd_families)

    p_list = sub.add_parser("list", help="list available metrics")
    p_list.set_defaults(func=cmd_list)

    p_version = sub.add_parser("version", help="print version")
    p_version.set_defaults(func=cmd_version)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
