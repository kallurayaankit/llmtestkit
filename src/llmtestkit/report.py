"""Self-contained HTML traceability report.

One file per run. Opens in a browser. No server, no CDN.
Templates live in src/llmtestkit/templates/.
"""

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from llmtestkit.runner import Report


TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _render_trace(trace, force_open=False):
    has_fail = any(not s.passed for s in trace.scores)
    template = _env.get_template("trace.html")
    rendered = template.render(trace=trace, has_fail=has_fail)
    if force_open:
        rendered = rendered.replace("<details class=", "<details open class=", 1)
    return Markup(rendered)


def render_report(report: Report, output_path=None) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    env.globals["render_trace"] = _render_trace

    template = env.get_template("report.html")
    summary = report.aggregate()
    failures = report.failures()
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_out = template.render(
        suite_name=report.suite_name,
        dataset_path=report.dataset_path,
        n_traces=len(report.traces),
        n_failures=len(failures),
        duration_s=f"{report.duration_s:.1f}",
        generated_at=generated_at,
        summary=summary,
        failures=failures,
        traces=report.traces,
    )

    if output_path is None:
        Path("reports").mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = f"reports/{report.suite_name}-{ts}.html"

    Path(output_path).write_text(html_out, encoding="utf-8")
    return output_path
