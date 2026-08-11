from __future__ import annotations

import json
import operator
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from .metrics import percentile


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DASHBOARD_CONFIG = REPO_ROOT / "config" / "dashboard.yaml"
DEFAULT_SLO_CONFIG = REPO_ROOT / "config" / "slo.yaml"
DEFAULT_ALERT_CONFIG = REPO_ROOT / "config" / "alert_rules.yaml"
DEFAULT_LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"

COMPARATORS = {
    "lt": operator.lt,
    "lte": operator.le,
    "gt": operator.gt,
    "gte": operator.ge,
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a YAML object")
    return payload


def load_logs(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def filter_time_window(records: list[dict[str, Any]], minutes: int) -> list[dict[str, Any]]:
    timestamps = [_parse_ts(record.get("ts")) for record in records]
    valid_timestamps = [ts for ts in timestamps if ts is not None]
    if not valid_timestamps:
        return records

    end = max(valid_timestamps)
    start = end - timedelta(minutes=minutes)
    windowed: list[dict[str, Any]] = []
    for record in records:
        ts = _parse_ts(record.get("ts"))
        if ts is None or start <= ts <= end:
            windowed.append(record)
    return windowed


def _numbers(records: list[dict[str, Any]], field: str) -> list[float]:
    values: list[float] = []
    for record in records:
        value = record.get(field)
        if isinstance(value, (int, float)):
            values.append(float(value))
    return values


def _minute_bucket(record: dict[str, Any]) -> str:
    ts = _parse_ts(record.get("ts"))
    if ts is None:
        return "unknown"
    return ts.replace(second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def calculate_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    request_records = [record for record in records if record.get("event") == "request_received"]
    response_records = [record for record in records if record.get("event") == "response_sent"]
    failed_records = [record for record in records if record.get("event") == "request_failed"]

    latencies = [int(value) for value in _numbers(response_records, "latency_ms")]
    costs = _numbers(response_records, "cost_usd")
    quality_scores = _numbers(response_records, "quality_score")
    tokens_in = [int(value) for value in _numbers(response_records, "tokens_in")]
    tokens_out = [int(value) for value in _numbers(response_records, "tokens_out")]

    traffic_by_minute: dict[str, int] = defaultdict(int)
    for record in request_records:
        traffic_by_minute[_minute_bucket(record)] += 1

    cost_by_minute: dict[str, float] = defaultdict(float)
    for record in response_records:
        value = record.get("cost_usd")
        if isinstance(value, (int, float)):
            cost_by_minute[_minute_bucket(record)] += float(value)

    error_breakdown = Counter(
        str(record.get("error_type") or "unknown") for record in failed_records
    )
    request_count = len(request_records)
    active_rate_per_minute = max(traffic_by_minute.values(), default=0)
    failed_count = len(failed_records)
    error_rate_pct = (failed_count / request_count * 100) if request_count else 0.0

    return {
        "request_count": request_count,
        "rate_per_minute": active_rate_per_minute,
        "latency_p50_ms": percentile(latencies, 50),
        "latency_p95_ms": percentile(latencies, 95),
        "latency_p99_ms": percentile(latencies, 99),
        "error_count": failed_count,
        "error_rate_pct": round(error_rate_pct, 4),
        "error_breakdown": dict(error_breakdown),
        "cost_total_usd": round(sum(costs), 6),
        "cost_by_minute_usd": {k: round(v, 6) for k, v in sorted(cost_by_minute.items())},
        "tokens_in_total": sum(tokens_in),
        "tokens_out_total": sum(tokens_out),
        "quality_score_avg": round(sum(quality_scores) / len(quality_scores), 4)
        if quality_scores
        else 0.0,
        "traffic_by_minute": dict(sorted(traffic_by_minute.items())),
        "success_rate_pct": round(100 - error_rate_pct, 4) if request_count else 100.0,
        "daily_cost_usd": round(sum(costs), 6),
    }


def evaluate_threshold(value: float, operator_name: str, threshold: float) -> str:
    comparator = COMPARATORS[operator_name]
    return "ok" if comparator(value, threshold) else "breach"


def build_dashboard(
    log_path: Path = DEFAULT_LOG_PATH,
    config_path: Path = DEFAULT_DASHBOARD_CONFIG,
) -> dict[str, Any]:
    config = load_yaml(config_path)["dashboard"]
    records = filter_time_window(load_logs(log_path), int(config["time_range_minutes"]))
    metrics = calculate_metrics(records)

    panels = []
    for panel in config["panels"]:
        panel_id = panel["id"]
        values = _panel_values(panel_id, metrics)
        threshold = panel["threshold"]
        threshold_value = float(threshold["value"])
        threshold_metric = _threshold_metric(panel_id, threshold["aggregation"], metrics)
        panels.append(
            {
                "id": panel_id,
                "title": panel["title"],
                "unit": panel["unit"],
                "time_range_minutes": config["time_range_minutes"],
                "source": panel["source"],
                "fields": panel["fields"],
                "aggregations": panel["aggregations"],
                "values": values,
                "threshold": threshold,
                "threshold_status": evaluate_threshold(
                    float(threshold_metric), threshold["operator"], threshold_value
                ),
            }
        )

    return {
        "title": config["title"],
        "time_range_minutes": config["time_range_minutes"],
        "refresh_seconds": config["refresh_seconds"],
        "source": str(log_path),
        "record_count": len(records),
        "metrics": metrics,
        "panels": panels,
    }


def _panel_values(panel_id: str, metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "latency": {
            "p50": metrics["latency_p50_ms"],
            "p95": metrics["latency_p95_ms"],
            "p99": metrics["latency_p99_ms"],
        },
        "traffic": {
            "count": metrics["request_count"],
            "rate_per_minute": metrics["rate_per_minute"],
            "series": metrics["traffic_by_minute"],
        },
        "errors": {
            "error_rate_pct": metrics["error_rate_pct"],
            "count_by_value": metrics["error_breakdown"],
        },
        "cost": {
            "total": metrics["cost_total_usd"],
            "sum_by_minute": metrics["cost_by_minute_usd"],
        },
        "tokens": {
            "tokens_in": metrics["tokens_in_total"],
            "tokens_out": metrics["tokens_out_total"],
        },
        "quality": {"mean": metrics["quality_score_avg"]},
    }[panel_id]


def _threshold_metric(panel_id: str, aggregation: str, metrics: dict[str, Any]) -> float:
    lookup = {
        ("latency", "p95"): metrics["latency_p95_ms"],
        ("traffic", "rate_per_minute"): metrics["rate_per_minute"],
        ("errors", "error_rate_pct"): metrics["error_rate_pct"],
        ("cost", "total"): metrics["cost_total_usd"],
        ("tokens", "sum_by_field"): max(
            metrics["tokens_in_total"], metrics["tokens_out_total"]
        ),
        ("quality", "mean"): metrics["quality_score_avg"],
    }
    return float(lookup[(panel_id, aggregation)])


def evaluate_slos(
    metrics: dict[str, Any],
    slo_path: Path = DEFAULT_SLO_CONFIG,
) -> list[dict[str, Any]]:
    config = load_yaml(slo_path)
    slos: list[dict[str, Any]] = []
    for name, definition in config.get("slis", {}).items():
        objective = float(definition["objective"])
        operator_name = definition.get("operator") or (
            "gte" if name in {"quality_score_avg", "success_rate_pct"} else "lte"
        )
        value = float(metrics.get(name, 0.0))
        slos.append(
            {
                "name": name,
                "metric": name,
                "target": definition["target"],
                "objective": objective,
                "operator": operator_name,
                "current_value": value,
                "status": evaluate_threshold(value, operator_name, objective),
                "window": config.get("window"),
            }
        )
    return slos


def evaluate_alerts(
    metrics: dict[str, Any],
    alert_path: Path = DEFAULT_ALERT_CONFIG,
) -> list[dict[str, Any]]:
    config = load_yaml(alert_path)
    alerts: list[dict[str, Any]] = []
    for rule in config.get("alerts", []):
        metric = rule["metric"]
        operator_name = rule["operator"]
        threshold = float(rule["threshold"])
        current = float(metrics.get(metric, 0.0))
        breached = COMPARATORS[operator_name](current, threshold)
        alerts.append(
            {
                "name": rule["name"],
                "metric": metric,
                "threshold": threshold,
                "current_value": current,
                "status": "firing" if breached else "ok",
                "severity": rule["severity"],
                "operator": operator_name,
                "condition": rule["condition"],
                "duration": rule.get("duration"),
                "runbook": rule["runbook"],
            }
        )
    return alerts
