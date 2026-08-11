from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio
from app.dashboard import COMPARATORS, build_dashboard, evaluate_alerts, evaluate_slos, load_yaml


EXPECTED_ALERT_KEYS = {
    "name",
    "severity",
    "metric",
    "operator",
    "threshold",
    "condition",
    "type",
    "owner",
    "runbook",
}


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Validate SLO and alert contracts.")
    parser.add_argument("--logs", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    args = parser.parse_args()

    try:
        slo_config = load_yaml(REPO_ROOT / "config" / "slo.yaml")
        alert_config = load_yaml(REPO_ROOT / "config" / "alert_rules.yaml")
        dashboard = build_dashboard(args.logs)
        slos = evaluate_slos(dashboard["metrics"])
        alerts = evaluate_alerts(dashboard["metrics"])
    except Exception as exc:
        print(f"KHONG HOP LE: {exc}")
        return 1

    sli_names = set(slo_config.get("slis", {}))
    alert_rules = alert_config.get("alerts")
    if not isinstance(alert_rules, list) or len(alert_rules) < 3:
        print("KHONG HOP LE: config/alert_rules.yaml must define at least 3 alerts")
        return 1

    for rule in alert_rules:
        missing = EXPECTED_ALERT_KEYS - set(rule)
        if missing:
            print(f"KHONG HOP LE: alert {rule.get('name', '<unknown>')} missing {sorted(missing)}")
            return 1
        if rule["metric"] not in sli_names:
            print(f"KHONG HOP LE: alert {rule['name']} metric is not an SLI")
            return 1
        if rule["operator"] not in COMPARATORS:
            print(f"KHONG HOP LE: alert {rule['name']} operator is invalid")
            return 1
        if rule["threshold"] != slo_config["slis"][rule["metric"]]["objective"]:
            print(f"KHONG HOP LE: alert {rule['name']} threshold must match SLO objective")
            return 1

    print(f"HOP LE: {len(slos)} SLO, {len(alerts)} alert rule. Alerts firing: {sum(1 for alert in alerts if alert['status'] == 'firing')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
