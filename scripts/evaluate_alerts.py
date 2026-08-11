from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio
from app.dashboard import build_dashboard, evaluate_alerts, evaluate_slos


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Evaluate SLOs and alerts from dashboard logs.")
    parser.add_argument("--logs", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    args = parser.parse_args()

    dashboard = build_dashboard(args.logs)
    slos = evaluate_slos(dashboard["metrics"])
    alerts = evaluate_alerts(dashboard["metrics"])
    if args.json:
        print(json.dumps({"slos": slos, "alerts": alerts}, ensure_ascii=False, indent=2))
    else:
        for slo in slos:
            print(
                f"SLO {slo['name']}: {slo['current_value']} {slo['operator']} {slo['objective']} => {slo['status']}"
            )
        for alert in alerts:
            print(
                f"ALERT {alert['name']}: {alert['status']} | {alert['metric']}={alert['current_value']} | {alert['condition']} | {alert['runbook']}"
            )
    return 1 if any(alert["status"] == "firing" for alert in alerts) else 0


if __name__ == "__main__":
    raise SystemExit(main())
