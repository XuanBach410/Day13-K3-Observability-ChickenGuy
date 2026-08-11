from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio
from app.dashboard import build_dashboard, evaluate_alerts, evaluate_slos


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    if isinstance(value, dict):
        return html.escape(json.dumps(value, ensure_ascii=False))
    return html.escape(str(value))


def render_html(dashboard: dict[str, Any], slos: list[dict[str, Any]], alerts: list[dict[str, Any]]) -> str:
    panel_cards = []
    for panel in dashboard["panels"]:
        values = "".join(
            f"<tr><th>{html.escape(str(key))}</th><td>{_fmt(value)}</td></tr>"
            for key, value in panel["values"].items()
        )
        threshold = panel["threshold"]
        panel_cards.append(
            f"""
            <section class="panel {panel['threshold_status']}">
              <h2>{html.escape(panel['title'])}</h2>
              <p class="meta">Unit: {html.escape(panel['unit'])} | Time range: {panel['time_range_minutes']}m</p>
              <table>{values}</table>
              <p class="threshold">Threshold: {html.escape(threshold['aggregation'])} {html.escape(threshold['operator'])} {threshold['value']}</p>
            </section>
            """
        )

    slo_rows = "".join(
        f"<tr><td>{html.escape(slo['name'])}</td><td>{_fmt(slo['current_value'])}</td><td>{html.escape(slo['operator'])} {slo['objective']}</td><td class='{slo['status']}'>{slo['status']}</td></tr>"
        for slo in slos
    )
    alert_rows = "".join(
        f"<tr><td>{html.escape(alert['name'])}</td><td>{html.escape(alert['severity'])}</td><td>{html.escape(alert['metric'])}</td><td>{_fmt(alert['current_value'])}</td><td>{html.escape(alert['operator']) if 'operator' in alert else html.escape(alert['condition'])}</td><td class='{alert['status']}'>{alert['status']}</td><td>{html.escape(alert['runbook'])}</td></tr>"
        for alert in alerts
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="{dashboard['refresh_seconds']}">
  <title>{html.escape(dashboard['title'])}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; background: #f6f7f9; color: #1f2933; }}
    header {{ margin-bottom: 18px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
    .panel {{ background: white; border: 1px solid #d8dee6; border-left: 5px solid #2f80ed; border-radius: 6px; padding: 14px; }}
    .panel.breach {{ border-left-color: #c8372d; }}
    h1 {{ margin: 0 0 6px; font-size: 24px; }}
    h2 {{ margin: 0 0 8px; font-size: 17px; }}
    .meta, .threshold {{ color: #52616b; font-size: 13px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ border-bottom: 1px solid #edf0f3; padding: 7px 4px; text-align: left; vertical-align: top; }}
    th {{ width: 38%; color: #52616b; font-weight: 600; }}
    .ok {{ color: #176b3a; font-weight: 700; }}
    .breach, .firing {{ color: #a32418; font-weight: 700; }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(dashboard['title'])}</h1>
    <div class="meta">Source: {html.escape(dashboard['source'])} | Time range: {dashboard['time_range_minutes']}m | Refresh: {dashboard['refresh_seconds']}s | Records: {dashboard['record_count']}</div>
  </header>
  <main class="grid">{''.join(panel_cards)}</main>
  <section>
    <h2>SLO Status</h2>
    <table><tr><th>SLO</th><th>Current</th><th>Objective</th><th>Status</th></tr>{slo_rows}</table>
  </section>
  <section>
    <h2>Alerts</h2>
    <table><tr><th>Name</th><th>Severity</th><th>Metric</th><th>Current</th><th>Condition</th><th>Status</th><th>Runbook</th></tr>{alert_rows}</table>
  </section>
</body>
</html>
"""


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Render the Day 13 dashboard from JSONL logs.")
    parser.add_argument("--logs", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "submission" / "evidence" / "dashboard.html")
    args = parser.parse_args()

    dashboard = build_dashboard(args.logs)
    slos = evaluate_slos(dashboard["metrics"])
    alerts = evaluate_alerts(dashboard["metrics"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(dashboard, slos, alerts), encoding="utf-8")
    print(f"Dashboard rendered: {args.output}")
    print(f"Panels: {len(dashboard['panels'])}/6 | alerts firing: {sum(1 for alert in alerts if alert['status'] == 'firing')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
