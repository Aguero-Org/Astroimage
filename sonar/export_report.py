"""Export one SonarQube analysis as JSON for agents and Markdown for humans."""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_KEY = "Astroimage"
NOTE = (
    "Ephemeral SonarQube Community scan. No previous analysis, so this is the "
    "full open-issue set, not a new-code delta. The CI job does not fail on "
    "the quality gate."
)
SEVERITY_ORDER = ("BLOCKER", "HIGH", "MEDIUM", "LOW", "INFO")
LEGACY_SEVERITY = {
    "BLOCKER": "BLOCKER",
    "CRITICAL": "HIGH",
    "MAJOR": "MEDIUM",
    "MINOR": "LOW",
    "INFO": "INFO",
}
CLASSIC_METRICS = (
    "ncloc",
    "coverage",
    "duplicated_lines_density",
    "bugs",
    "vulnerabilities",
    "code_smells",
    "security_hotspots",
)
SOFTWARE_QUALITY_METRICS = (
    "software_quality_maintainability_issues",
    "software_quality_reliability_issues",
    "software_quality_security_issues",
)


def basic_header(user: str, password: str) -> str:
    token = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
    return f"Basic {token}"


def component_path(component: str, project_key: str) -> str:
    prefix = f"{project_key}:"
    if component.startswith(prefix):
        return component[len(prefix) :]
    return component


def impact_severity(issue: dict[str, Any]) -> str:
    impacts = issue.get("impacts")
    ranks = []
    if isinstance(impacts, list):
        for impact in impacts:
            if isinstance(impact, dict):
                severity = impact.get("severity")
                if isinstance(severity, str):
                    ranks.append(severity)
    if ranks:
        return min(ranks, key=lambda item: SEVERITY_ORDER.index(item) if item in SEVERITY_ORDER else len(SEVERITY_ORDER))
    legacy = issue.get("severity")
    if isinstance(legacy, str):
        return LEGACY_SEVERITY.get(legacy, legacy)
    return "INFO"


def line_number(raw: dict[str, Any]) -> int | None:
    line = raw.get("line")
    if isinstance(line, int):
        return line
    text_range = raw.get("textRange")
    if isinstance(text_range, dict) and isinstance(text_range.get("startLine"), int):
        return text_range["startLine"]
    return None


def normalize_issue(raw: dict[str, Any], project_key: str) -> dict[str, Any]:
    impacts = []
    raw_impacts = raw.get("impacts")
    if isinstance(raw_impacts, list):
        for impact in raw_impacts:
            if not isinstance(impact, dict):
                continue
            quality = impact.get("softwareQuality")
            severity = impact.get("severity")
            if isinstance(quality, str) and isinstance(severity, str):
                impacts.append({"softwareQuality": quality, "severity": severity})
    component = raw.get("component")
    path = component_path(component, project_key) if isinstance(component, str) else ""
    message = raw.get("message")
    return {
        "rule": raw.get("rule") if isinstance(raw.get("rule"), str) else "",
        "severity": impact_severity(raw),
        "impacts": impacts,
        "type": raw.get("type") if isinstance(raw.get("type"), str) else "",
        "message": message.replace("\n", " ") if isinstance(message, str) else "",
        "component": path,
        "line": line_number(raw),
        "effort": raw.get("effort") if isinstance(raw.get("effort"), str) else "",
        "cleanCodeAttribute": raw.get("cleanCodeAttribute") if isinstance(raw.get("cleanCodeAttribute"), str) else "",
        "status": raw.get("status") if isinstance(raw.get("status"), str) else "",
    }


def normalize_hotspot(raw: dict[str, Any], project_key: str) -> dict[str, Any]:
    component = raw.get("component")
    path = component_path(component, project_key) if isinstance(component, str) else ""
    rule = raw.get("ruleKey")
    if not isinstance(rule, str):
        rule = raw.get("rule") if isinstance(raw.get("rule"), str) else ""
    message = raw.get("message")
    probability = raw.get("vulnerabilityProbability")
    category = raw.get("securityCategory")
    status = raw.get("status")
    return {
        "rule": rule,
        "message": message.replace("\n", " ") if isinstance(message, str) else "",
        "component": path,
        "line": line_number(raw),
        "vulnerabilityProbability": probability if isinstance(probability, str) else "",
        "securityCategory": category if isinstance(category, str) else "",
        "status": status if isinstance(status, str) else "",
    }


def collect_pages(fetch_page: Any, item_key: str) -> list[dict[str, Any]]:
    page = 1
    items: list[dict[str, Any]] = []
    while True:
        payload = fetch_page(page)
        batch = payload.get(item_key, [])
        if not isinstance(batch, list):
            raise RuntimeError(f"unexpected {item_key} payload")
        items.extend(item for item in batch if isinstance(item, dict))
        paging = payload.get("paging")
        total = len(items)
        page_size = 500
        if isinstance(paging, dict):
            if isinstance(paging.get("total"), int):
                total = paging["total"]
            if isinstance(paging.get("pageSize"), int) and paging["pageSize"] > 0:
                page_size = paging["pageSize"]
        if not batch or page * page_size >= total:
            return items
        page += 1


def location(path: str, line: int | None) -> str:
    if line is None:
        return path or "(unknown)"
    return f"{path}:{line}"


def severity_rank(severity: str) -> int:
    try:
        return SEVERITY_ORDER.index(severity)
    except ValueError:
        return len(SEVERITY_ORDER)


def build_report(
    *,
    project_key: str,
    generated_at: str,
    measures: dict[str, str],
    quality_gate: dict[str, Any] | None,
    issues: list[dict[str, Any]],
    hotspots: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "projectKey": project_key,
        "generatedAt": generated_at,
        "note": NOTE,
        "measures": measures,
        "qualityGate": quality_gate,
        "issues": sorted(issues, key=lambda item: (severity_rank(str(item.get("severity"))), item.get("component"), item.get("line") or 0, item.get("rule"))),
        "hotspots": sorted(hotspots, key=lambda item: (item.get("component"), item.get("line") or 0, item.get("rule"))),
    }


def render_markdown(report: dict[str, Any]) -> str:
    issues = report["issues"]
    hotspots = report["hotspots"]
    lines = [
        "# SonarQube report",
        "",
        "Machine-readable twin: `issues.json` (schemaVersion 1).",
        "",
        str(report["note"]),
        "",
        "## Measures",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    measures = report["measures"]
    if measures:
        for metric in sorted(measures):
            lines.append(f"| {metric} | {measures[metric]} |")
    else:
        lines.append("| — | — |")
    lines.extend(["", "## Quality gate", ""])
    gate = report.get("qualityGate")
    if not isinstance(gate, dict) or not gate:
        lines.append("Unavailable.")
    elif "error" in gate:
        lines.append(f"Unavailable: {gate['error']}")
    else:
        lines.append(str(gate.get("status", "UNKNOWN")))
        conditions = gate.get("conditions")
        if isinstance(conditions, list) and conditions:
            lines.extend(["", "| Metric | Status | Comparator | Threshold | Actual |", "| --- | --- | --- | --- | --- |"])
            for condition in conditions:
                if not isinstance(condition, dict):
                    continue
                lines.append(
                    "| {metricKey} | {status} | {comparator} | {errorThreshold} | {actualValue} |".format(
                        metricKey=condition.get("metricKey", ""),
                        status=condition.get("status", ""),
                        comparator=condition.get("comparator", ""),
                        errorThreshold=condition.get("errorThreshold", ""),
                        actualValue=condition.get("actualValue", ""),
                    )
                )
    counts = Counter(str(issue.get("severity")) for issue in issues)
    lines.extend(["", f"## Issues ({len(issues)})", ""])
    if counts:
        summary = ", ".join(f"{name} {counts[name]}" for name in SEVERITY_ORDER if counts[name])
        extras = sorted(name for name in counts if name not in SEVERITY_ORDER)
        if extras:
            summary = ", ".join(part for part in (summary, ", ".join(f"{name} {counts[name]}" for name in extras)) if part)
        lines.extend([summary, ""])
    if not issues:
        lines.append("No open issues.")
    else:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for issue in issues:
            grouped.setdefault((str(issue.get("severity")), str(issue.get("rule"))), []).append(issue)
        for (severity, rule), grouped_issues in sorted(grouped.items(), key=lambda item: (severity_rank(item[0][0]), item[0][1])):
            lines.append(f"### {severity} — {rule} ({len(grouped_issues)})")
            lines.append("")
            for issue in sorted(grouped_issues, key=lambda item: (item.get("component"), item.get("line") or 0)):
                lines.append(f"- `{location(str(issue.get('component')), issue.get('line'))}` {issue.get('message')}")
            lines.append("")
    lines.extend([f"## Hotspots ({len(hotspots)})", ""])
    hotspots_error = report.get("hotspotsError")
    if isinstance(hotspots_error, str) and hotspots_error:
        lines.append(f"Hotspot search failed: {hotspots_error}")
        lines.append("")
    if not hotspots:
        lines.append("No security hotspots.")
    else:
        for hotspot in hotspots:
            probability = hotspot.get("vulnerabilityProbability") or "UNKNOWN"
            lines.append(
                f"- `{location(str(hotspot.get('component')), hotspot.get('line'))}` "
                f"{probability} {hotspot.get('rule')} {hotspot.get('message')}"
            )
    lines.append("")
    return "\n".join(lines)


class SonarClient:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def get(self, path: str, query: dict[str, str]) -> dict[str, Any]:
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "Authorization": basic_header(self.token, "")},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read()
        except urllib.error.HTTPError as caught:
            detail = caught.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"{path} failed with HTTP {caught.code}: {detail}") from caught
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError(f"{path} returned a non-object payload")
        return payload

    def wait_ce(self, task_id: str, *, attempts: int = 120, pause_seconds: float = 5) -> None:
        for _ in range(attempts):
            payload = self.get("/api/ce/task", {"id": task_id})
            task = payload.get("task")
            status = task.get("status") if isinstance(task, dict) else None
            if status == "SUCCESS":
                return
            if status in {"FAILED", "CANCELED"}:
                raise RuntimeError(f"compute engine task {task_id} {status}")
            time.sleep(pause_seconds)
        raise RuntimeError(f"compute engine task {task_id} did not finish")

    def issues(self) -> list[dict[str, Any]]:
        def fetch_page(page: int) -> dict[str, Any]:
            return self.get(
                "/api/issues/search",
                {"componentKeys": PROJECT_KEY, "resolved": "false", "ps": "500", "p": str(page)},
            )

        return collect_pages(fetch_page, "issues")

    def hotspots(self) -> list[dict[str, Any]]:
        def fetch_page(page: int) -> dict[str, Any]:
            return self.get(
                "/api/hotspots/search",
                {"projectKey": PROJECT_KEY, "ps": "500", "p": str(page)},
            )

        return collect_pages(fetch_page, "hotspots")

    def measures(self) -> dict[str, str]:
        found: dict[str, str] = {}
        for metrics in (CLASSIC_METRICS, SOFTWARE_QUALITY_METRICS):
            try:
                payload = self.get(
                    "/api/measures/component",
                    {"component": PROJECT_KEY, "metricKeys": ",".join(metrics)},
                )
            except RuntimeError:
                continue
            component = payload.get("component")
            raw_measures = component.get("measures") if isinstance(component, dict) else None
            if not isinstance(raw_measures, list):
                continue
            for measure in raw_measures:
                if not isinstance(measure, dict):
                    continue
                metric = measure.get("metric")
                value = measure.get("value")
                if isinstance(metric, str) and isinstance(value, str):
                    found[metric] = value
        return found

    def quality_gate(self) -> dict[str, Any] | None:
        try:
            payload = self.get("/api/qualitygates/project_status", {"projectKey": PROJECT_KEY})
        except RuntimeError as caught:
            return {"error": str(caught)}
        status = payload.get("projectStatus")
        return status if isinstance(status, dict) else {"error": "missing projectStatus"}


def read_ce_task_id(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"missing scanner report: {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("ceTaskId="):
            task_id = line.split("=", 1)[1].strip()
            if task_id:
                return task_id
    raise RuntimeError(f"scanner report has no ceTaskId: {path}")


def write_report(out_dir: Path, report: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "issues.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out_dir / "issues.md").write_text(render_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--token-file", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--report-task", type=Path, default=Path(".scannerwork") / "report-task.txt")
    args = parser.parse_args()
    token = args.token_file.read_text(encoding="utf-8").strip()
    if not token:
        print("empty analysis token", file=sys.stderr)
        return 1
    try:
        client = SonarClient(args.url, token)
        client.wait_ce(read_ce_task_id(args.report_task))
        try:
            raw_hotspots = client.hotspots()
            hotspots_error = None
        except RuntimeError as caught:
            raw_hotspots = []
            hotspots_error = str(caught)
        report = build_report(
            project_key=PROJECT_KEY,
            generated_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            measures=client.measures(),
            quality_gate=client.quality_gate(),
            issues=[normalize_issue(item, PROJECT_KEY) for item in client.issues()],
            hotspots=[normalize_hotspot(item, PROJECT_KEY) for item in raw_hotspots],
        )
        if hotspots_error is not None:
            report["hotspotsError"] = hotspots_error
        write_report(args.out, report)
    except (RuntimeError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as caught:
        print(str(caught), file=sys.stderr)
        return 1
    print(f"wrote {args.out / 'issues.json'} and {args.out / 'issues.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
