# Alerts and Runbooks

Each alert is based on an SLO or a user-visible symptom. Use `data/logs.jsonl`
as the dashboard source of truth, then pivot to traces only when a
`correlation_id` or trace metadata is available.

## latency-p95-slo-breach

- Alert name: `latency_p95_slo_breach`
- Severity: critical
- SLI/SLO: `latency_p95_ms`
- Condition: `latency_p95_ms > 3000 for 5m`
- User impact: users wait too long for chat responses.
- Owner: dashboard-slo-alert

Investigation flow:

1. Open the dashboard and confirm the Latency percentiles panel is breaching the P95 threshold.
2. Find recent `response_sent` log records where `latency_ms > 3000`.
3. Pick the slowest record and copy its `correlation_id`.
4. Inspect the matching trace if available, focusing on slow RAG, tool, or model spans.
5. Inspect all logs with the same `correlation_id` to verify request metadata and payload summary.
6. Identify the root cause: slow retrieval, slow tool call, model delay, or retries.
7. Remediate by disabling the active incident, reducing retrieval scope, adding timeout/circuit breaker, or rolling back the prompt/version that increased latency.
8. Confirm the dashboard P95 returns below 3000 ms.

## error-rate-slo-breach

- Alert name: `error_rate_slo_breach`
- Severity: critical
- SLI/SLO: `error_rate_pct`
- Condition: `error_rate_pct > 2 for 5m`
- User impact: users receive failed chat responses.
- Owner: dashboard-slo-alert

Investigation flow:

1. Open the dashboard and confirm the Error rate and breakdown panel is breaching 2 percent.
2. Check the error breakdown by `error_type` to identify the dominant failure mode.
3. Locate `request_failed` logs for that `error_type` and copy a representative `correlation_id`.
4. Inspect the trace if available to locate the failed model, RAG, or tool span.
5. Inspect matching logs to confirm request feature, model, environment, and sanitized payload summary.
6. Identify whether the root cause is dependency failure, invalid input handling, timeout, or regression.
7. Remediate by disabling the failing incident, rolling back the dependency/prompt, or adding a graceful fallback.
8. Confirm `error_rate_pct` drops below 2 percent and no new error type dominates.

## daily-cost-slo-breach

- Alert name: `daily_cost_slo_breach`
- Severity: warning
- SLI/SLO: `daily_cost_usd`
- Condition: `daily_cost_usd > 2.5 for 15m`
- User impact: service cost exceeds the lab budget guardrail.
- Owner: dashboard-slo-alert

Investigation flow:

1. Open the dashboard and confirm the Cost over time panel exceeds the USD threshold.
2. Compare the Cost and Input/output tokens panels to see whether the spike is token driven.
3. Locate recent `response_sent` records with high `cost_usd`, `tokens_in`, or `tokens_out`.
4. Copy the highest-cost `correlation_id` and inspect the trace if available.
5. Inspect logs for repeated requests, unusually large prompts, verbose outputs, or expensive model usage.
6. Identify whether the root cause is traffic burst, prompt expansion, retrieval bloat, or model/config change.
7. Remediate by disabling cost-spike incident, reducing context size, capping output tokens, or routing to a cheaper model.
8. Confirm total evaluated cost is back under 2.5 USD.

## quality-score-slo-breach

- Alert name: `quality_score_slo_breach`
- Severity: warning
- SLI/SLO: `quality_score_avg`
- Condition: `quality_score_avg < 0.75 for 10m`
- User impact: users receive lower-confidence or less relevant answers.
- Owner: dashboard-slo-alert

Investigation flow:

1. Open the dashboard and confirm the Quality proxy panel is below 0.75.
2. Locate recent `response_sent` records with low `quality_score`.
3. Copy a low-quality record's `correlation_id`.
4. Inspect the trace if available and check prompt metadata, retrieved docs, and model response spans.
5. Inspect matching logs for feature, model, payload summary, and answer preview.
6. Identify whether the root cause is missing retrieval context, prompt version regression, or bad input distribution.
7. Remediate by rolling back prompt label/version, improving retrieval filters, or adding fallback context.
8. Confirm average quality score returns to at least 0.75.
