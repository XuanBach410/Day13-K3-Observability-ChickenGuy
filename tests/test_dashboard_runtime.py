from __future__ import annotations

from pathlib import Path

from app.dashboard import build_dashboard, evaluate_alerts, evaluate_slos


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_builds_configured_six_panels() -> None:
    dashboard = build_dashboard(REPO_ROOT / "data" / "logs.jsonl")

    assert [panel["id"] for panel in dashboard["panels"]] == [
        "latency",
        "traffic",
        "errors",
        "cost",
        "tokens",
        "quality",
    ]
    assert dashboard["panels"][0]["values"]["p95"] > 0


def test_slo_and_alert_evaluation_from_fixture() -> None:
    dashboard = build_dashboard(REPO_ROOT / "data" / "alert_violation_fixture.jsonl")

    slos = evaluate_slos(dashboard["metrics"])
    alerts = evaluate_alerts(dashboard["metrics"])

    assert {slo["status"] for slo in slos} == {"breach"}
    assert {alert["status"] for alert in alerts} == {"firing"}
