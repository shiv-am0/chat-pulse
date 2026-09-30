from pathlib import Path
from unittest import TestCase

from benchmarks.api.render_report import parse_duration, render


class RenderReportTests(TestCase):
    def test_render_includes_core_api_metrics(self):
        summary = {
            "metrics": {
                "api_history_requests": {"count": 1200, "rate": 20.0},
                "api_history_latency": {
                    "avg": 30.0,
                    "med": 25.0,
                    "p(95)": 75.0,
                    "p(99)": 110.0,
                    "max": 160.0,
                },
                "api_history_error_rate": {"value": 0.005},
                "dropped_iterations": {"count": 2, "rate": 0.03},
            },
        }

        report = render(summary, Path("summary.json"), duration_seconds=60)

        self.assertIn("20.00", report)
        self.assertIn("25.00 ms", report)
        self.assertIn("75.00 ms", report)
        self.assertIn("110.00 ms", report)
        self.assertIn("0.500%", report)
        self.assertIn("Dropped iterations", report)
        self.assertIn("Measured duration", report)

    def test_render_rejects_summary_without_endpoint_metrics(self):
        with self.assertRaisesRegex(ValueError, "setup or authentication failure"):
            render({"metrics": {}}, Path("failed-summary.json"))

    def test_parse_duration_supports_k6_duration_strings(self):
        self.assertEqual(parse_duration("30s"), 30)
        self.assertEqual(parse_duration("5m"), 300)
        self.assertEqual(parse_duration("1m30s"), 90)
