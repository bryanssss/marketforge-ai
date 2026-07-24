from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from typing import Any

from app.core.schemas import ReportRequest


def _flatten_metrics(result: dict[str, Any]) -> dict[str, Any]:
    for key in ("metrics", "summary", "forecast_metrics"):
        value = result.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _markdown(payload: ReportRequest) -> str:
    result = payload.result
    metrics = _flatten_metrics(result)
    generated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    lines = [f"# {payload.title}", "", f"Generated: `{generated}`", "", f"Template: `{payload.template}`", ""]
    if payload.template == "executive":
        lines.extend(["## Executive Summary", "", "This report summarises the most important MarketForge evidence and limitations.", ""])
    elif payload.template == "risk":
        lines.extend(["## Risk Review", "", "> Scenario and historical risk estimates are not guarantees of future losses or safety.", ""])
    elif payload.template == "model_card":
        lines.extend(["## Model Card", "", "This document records model identity, settings, evidence and intended use.", ""])
    else:
        lines.extend(["## Research Report", "", "This report records settings, evidence and reproducibility metadata.", ""])

    lines.extend(["## Key Metrics", ""])
    if metrics:
        lines.extend(["| Metric | Value |", "|---|---:|"])
        for key, value in metrics.items():
            if isinstance(value, (dict, list)):
                continue
            lines.append(f"| {key.replace('_', ' ').title()} | {value} |")
    else:
        lines.append("No standard metric block was found in the supplied result.")

    notes = result.get("notes", [])
    if notes:
        lines.extend(["", "## Evidence Notes", ""])
        lines.extend([f"- {item}" for item in notes])

    if payload.include_raw_settings:
        settings = result.get("settings") or result.get("metadata") or {}
        lines.extend(["", "## Settings and Metadata", "", "```json", json.dumps(settings, indent=2, default=str), "```"])

    lines.extend(
        [
            "",
            "## Important Limitations",
            "",
            "- Financial markets are uncertain and non-stationary.",
            "- Historical simulations do not guarantee future performance.",
            "- Forecast intervals can be miscalibrated.",
            "- This report is research and educational material, not financial advice.",
            "",
        ]
    )
    return "\n".join(lines)


def generate_report(payload: ReportRequest) -> tuple[str, str]:
    markdown = _markdown(payload)
    if payload.format == "markdown":
        return markdown, "text/markdown; charset=utf-8"
    paragraphs = []
    in_code = False
    for line in markdown.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            paragraphs.append("<pre>" if in_code else "</pre>")
        elif in_code:
            paragraphs.append(html.escape(line))
        elif line.startswith("# "):
            paragraphs.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            paragraphs.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            paragraphs.append(f"<p>• {html.escape(line[2:])}</p>")
        elif line.startswith("> "):
            paragraphs.append(f"<blockquote>{html.escape(line[2:])}</blockquote>")
        elif line and not line.startswith("|"):
            paragraphs.append(f"<p>{html.escape(line)}</p>")
    document = "<!doctype html><html><head><meta charset='utf-8'><title>MarketForge Report</title>" \
        "<style>body{font:16px system-ui;max-width:900px;margin:40px auto;padding:0 20px;line-height:1.6}pre{white-space:pre-wrap;background:#f4f4f4;padding:16px}blockquote{border-left:4px solid #999;padding-left:16px}</style>" \
        "</head><body>" + "\n".join(paragraphs) + "</body></html>"
    return document, "text/html; charset=utf-8"
