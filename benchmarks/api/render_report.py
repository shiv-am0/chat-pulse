#!/usr/bin/env python3
"""Render a small, dependency-free HTML report from a k6 summary export."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any


def metric_values(summary: dict[str, Any], name: str) -> dict[str, Any]:
    metric = summary.get("metrics", {}).get(name, {})
    # `k6 --summary-export` writes values directly on the metric. Data passed to
    # handleSummary() and some older exports wrap the same values in `values`.
    # Supporting both keeps previously captured runs renderable.
    return metric.get("values", metric)


def number(values: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = values.get(key, default)
    return float(value) if value is not None else default


def format_number(value: float, decimal_places: int = 2) -> str:
    return f"{value:,.{decimal_places}f}"


def parse_duration(value: str) -> float:
    units = {"ms": 0.001, "s": 1, "m": 60, "h": 3600}
    matches = list(re.finditer(r"(\d+(?:\.\d+)?)(ms|s|m|h)", value))
    if not matches or "".join(match.group(0) for match in matches) != value:
        raise ValueError(f"Unsupported benchmark duration: {value!r}")
    return sum(float(match.group(1)) * units[match.group(2)] for match in matches)


def render(
    summary: dict[str, Any],
    source: Path,
    duration_seconds: float | None = None,
) -> str:
    required_metrics = {
        "api_history_requests",
        "api_history_latency",
        "api_history_error_rate",
    }
    missing_metrics = required_metrics - summary.get("metrics", {}).keys()
    if missing_metrics:
        missing = ", ".join(sorted(missing_metrics))
        raise ValueError(
            f"The k6 run did not produce required API metrics: {missing}. "
            "Inspect the k6 output for a setup or authentication failure."
        )

    requests = metric_values(summary, "api_history_requests")
    latency = metric_values(summary, "api_history_latency")
    errors = metric_values(summary, "api_history_error_rate")
    dropped = metric_values(summary, "dropped_iterations")

    request_count = number(requests, "count")
    requests_per_second = (
        request_count / duration_seconds
        if duration_seconds
        else number(requests, "rate")
    )
    error_rate = number(errors, "rate", number(errors, "value")) * 100
    p50 = number(latency, "med", number(latency, "p(50)"))
    p95 = number(latency, "p(95)")
    p99 = number(latency, "p(99)")
    average = number(latency, "avg")
    maximum = number(latency, "max")
    dropped_iterations = number(dropped, "count")

    cards = [
        ("Requests/sec", format_number(requests_per_second)),
        ("Total requests", format_number(request_count, 0)),
        ("Error rate", f"{format_number(error_rate, 3)}%"),
        ("p50 latency", f"{format_number(p50)} ms"),
        ("p95 latency", f"{format_number(p95)} ms"),
        ("p99 latency", f"{format_number(p99)} ms"),
        ("Dropped iterations", format_number(dropped_iterations, 0)),
    ]
    if duration_seconds:
        cards.append(("Measured duration", f"{format_number(duration_seconds)} s"))
    cards_html = "".join(
        f'<article class="card"><span>{html.escape(label)}</span>'
        f"<strong>{html.escape(value)}</strong></article>"
        for label, value in cards
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Chat Pulse API benchmark</title>
  <style>
    :root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
    body {{ max-width: 1050px; margin: 0 auto; padding: 2rem; line-height: 1.5; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }}
    .card {{ border: 1px solid #8886; border-radius: 12px; padding: 1rem; }}
    .card span {{ display: block; color: #777; font-size: .9rem; }}
    .card strong {{ display: block; font-size: 1.7rem; margin-top: .25rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
    th, td {{ padding: .65rem; border-bottom: 1px solid #8886; text-align: left; }}
    code {{ overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <h1>Chat Pulse API benchmark</h1>
  <p>Authenticated <code>GET /api/messages/</code> results. Login/setup traffic is excluded.</p>
  <section class="grid">{cards_html}</section>
  <h2>Additional latency</h2>
  <table>
    <tr><th>Measurement</th><th>Value</th></tr>
    <tr><td>Average</td><td>{format_number(average)} ms</td></tr>
    <tr><td>Maximum</td><td>{format_number(maximum)} ms</td></tr>
  </table>
  <h2>How to read this</h2>
  <ul>
    <li><strong>Requests/sec</strong> is the achieved request rate, not merely the configured target.</li>
    <li><strong>p50</strong> means half of requests were faster and half were slower.</li>
    <li><strong>p95</strong> means 95% of requests completed within that time.</li>
    <li><strong>p99</strong> exposes slow tail requests that averages can hide.</li>
    <li><strong>Error rate</strong> includes non-200 responses and malformed response bodies.</li>
    <li><strong>Dropped iterations</strong> are requests k6 could not start; increase available VUs or reduce the target rate.</li>
  </ul>
  <p>Source summary: <code>{html.escape(str(source))}</code></p>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("summary", type=Path, help="k6 --summary-export JSON file")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--duration",
        help="Measured k6 scenario duration, for example 30s, 5m, or 1m30s",
    )
    args = parser.parse_args()

    with args.summary.open(encoding="utf-8") as summary_file:
        summary = json.load(summary_file)

    duration_seconds = parse_duration(args.duration) if args.duration else None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render(summary, args.summary, duration_seconds),
        encoding="utf-8",
    )

    requests = metric_values(summary, "api_history_requests")
    latency = metric_values(summary, "api_history_latency")
    errors = metric_values(summary, "api_history_error_rate")
    print(f"Report: {args.output}")
    request_count = number(requests, "count")
    requests_per_second = (
        request_count / duration_seconds
        if duration_seconds
        else number(requests, "rate")
    )
    print(f"Requests/sec: {requests_per_second:.2f}")
    print(f"p50: {number(latency, 'med', number(latency, 'p(50)')):.2f} ms")
    print(f"p95: {number(latency, 'p(95)'):.2f} ms")
    print(f"p99: {number(latency, 'p(99)'):.2f} ms")
    error_rate = number(errors, "rate", number(errors, "value"))
    print(f"Error rate: {error_rate * 100:.3f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
