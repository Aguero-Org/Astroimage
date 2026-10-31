from __future__ import annotations

import unittest

from export_report import (
    build_report,
    collect_pages,
    component_path,
    normalize_hotspot,
    normalize_issue,
    render_markdown,
)


class ExportReportTests(unittest.TestCase):
    def test_component_path_strips_project_key(self) -> None:
        self.assertEqual(component_path("Astroimage:backend/src/foo.py", "Astroimage"), "backend/src/foo.py")
        self.assertEqual(component_path("backend/src/foo.py", "Astroimage"), "backend/src/foo.py")

    def test_normalize_issue_uses_text_range_and_impacts(self) -> None:
        issue = normalize_issue(
            {
                "rule": "python:S1192",
                "severity": "MAJOR",
                "component": "Astroimage:backend/src/foo.py",
                "message": "Define a constant\ninstead",
                "textRange": {"startLine": 12},
                "impacts": [{"softwareQuality": "MAINTAINABILITY", "severity": "HIGH"}],
                "type": "CODE_SMELL",
                "effort": "5min",
                "cleanCodeAttribute": "DISTINCT",
                "status": "OPEN",
            },
            "Astroimage",
        )
        self.assertEqual(issue["severity"], "HIGH")
        self.assertEqual(issue["line"], 12)
        self.assertEqual(issue["component"], "backend/src/foo.py")
        self.assertEqual(issue["message"], "Define a constant instead")
        self.assertEqual(issue["impacts"], [{"softwareQuality": "MAINTAINABILITY", "severity": "HIGH"}])

    def test_file_level_issue_has_no_line(self) -> None:
        issue = normalize_issue(
            {"rule": "python:S104", "severity": "MAJOR", "component": "Astroimage:backend/src/foo.py", "message": "too long"},
            "Astroimage",
        )
        self.assertIsNone(issue["line"])
        self.assertEqual(issue["severity"], "MEDIUM")

    def test_collect_pages_stops_at_total(self) -> None:
        pages = {
            1: {"issues": [{"key": "a"}], "paging": {"pageIndex": 1, "pageSize": 1, "total": 2}},
            2: {"issues": [{"key": "b"}], "paging": {"pageIndex": 2, "pageSize": 1, "total": 2}},
        }
        self.assertEqual(collect_pages(pages.__getitem__, "issues"), [{"key": "a"}, {"key": "b"}])

    def test_markdown_lists_higher_severity_first_and_names_json_twin(self) -> None:
        report = build_report(
            project_key="Astroimage",
            generated_at="2026-10-31T00:00:00Z",
            measures={"coverage": "81.0", "ncloc": "10"},
            quality_gate={
                "status": "ERROR",
                "conditions": [
                    {
                        "metricKey": "new_coverage",
                        "status": "ERROR",
                        "comparator": "LT",
                        "errorThreshold": "80",
                        "actualValue": "0.0",
                    }
                ],
            },
            issues=[
                normalize_issue(
                    {
                        "rule": "python:S1481",
                        "severity": "MINOR",
                        "component": "Astroimage:backend/src/bar.py",
                        "line": 4,
                        "message": "unused",
                    },
                    "Astroimage",
                ),
                normalize_issue(
                    {
                        "rule": "python:S1192",
                        "severity": "CRITICAL",
                        "component": "Astroimage:backend/src/foo.py",
                        "line": 12,
                        "message": "duplicated",
                    },
                    "Astroimage",
                ),
            ],
            hotspots=[
                normalize_hotspot(
                    {
                        "ruleKey": "python:S3649",
                        "component": "Astroimage:backend/src/foo.py",
                        "line": 3,
                        "message": "query",
                        "vulnerabilityProbability": "HIGH",
                        "securityCategory": "sql-injection",
                        "status": "TO_REVIEW",
                    },
                    "Astroimage",
                )
            ],
        )
        text = render_markdown(report)
        self.assertLess(text.index("### HIGH — python:S1192"), text.index("### LOW — python:S1481"))
        self.assertIn("`backend/src/foo.py:12` duplicated", text)
        self.assertIn("`backend/src/foo.py:3` HIGH python:S3649 query", text)
        self.assertIn("issues.json", text)
        self.assertIn("| coverage | 81.0 |", text)
        self.assertIn("new_coverage", text)
        self.assertEqual(report["issues"][0]["rule"], "python:S1192")

    def test_empty_report_says_there_are_no_issues(self) -> None:
        text = render_markdown(
            build_report(
                project_key="Astroimage",
                generated_at="2026-10-31T00:00:00Z",
                measures={},
                quality_gate=None,
                issues=[],
                hotspots=[],
            )
        )
        self.assertIn("No open issues.", text)
        self.assertIn("No security hotspots.", text)
        self.assertIn("Unavailable.", text)


if __name__ == "__main__":
    unittest.main()
