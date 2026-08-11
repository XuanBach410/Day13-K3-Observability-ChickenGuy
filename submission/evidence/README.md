# Evidence Index & Screenshots Guide — Team ChickenGuy

Danh mục bằng chứng tự động và hướng dẫn chụp screenshot UI cho nhóm **ChickenGuy**.

---

## 1. Automated Validation Outputs (Text Files)

- **`submission/evidence/02_validate_logs.txt`**: Kết quả chạy `python scripts/validate_logs.py` (Đạt 100/100).
- **`submission/evidence/10_validate_dashboard.txt`**: Kết quả chạy `python scripts/validate_dashboard.py` (Đạt 6/6 panels hợp lệ).

---

## 2. Screenshot Naming & Required UI Evidence Checklist

| File Name | Description / Requirement | Target Section in Report | Status |
|---|---|---|---|
| `01_health.png` | Response `/health` trả về `{"ok": true}` | System Health Check | Ready for UI capture |
| `03_log_correlation_id.png` | Log record trong `data/logs.jsonl` có `correlation_id` dạng `req-<8-hex-chars>` xuyên suốt lifecycle | Logging & Correlation ID | SAVED (.png) |
| `04_pii_redaction.png` | Bằng chứng log đã che PII (`[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]`, `[REDACTED_CCCD]`) | PII Protection | SAVED (.png) |
| `05_langfuse_10_traces.png` | Danh sách 10+ traces thực trên Langfuse Web UI/Console | Langfuse Tracing | SAVED (.png) |
| `06_trace_waterfall.png` | Trace waterfall view thể hiện các span (`retrieve`, `llm.generate`) | Span Investigation | SAVED (.png) |
| `07_prompt_v1_trace.png` | Trace hiển thị metadata `prompt_name=day13-chat`, `prompt_label=baseline`/`production`, `prompt_version=1` | Prompt Versioning v1 | Ready on Langfuse UI |
| `08_prompt_v2_trace.png` | Trace hiển thị metadata `prompt_name=day13-chat`, `prompt_label=candidate`, `prompt_version=2` | Prompt Versioning v2 | Ready on Langfuse UI |
| `09_prompt_rollback.png` | Screenshot thao tác chuyển label `production` về version 1 hoặc rollback prompt | Prompt Rollback | Ready on Langfuse UI |
| `11_dashboard_6_panels.png` | Dashboard 6 panels (Latency, Traffic, Errors, Cost, Tokens, Quality) dựng từ `data/logs.jsonl` hiển thị rõ threshold/SLO lines | Dashboard | SAVED (.png) |
| `12_challenge_metrics.png` | Dashboard/Metric graph thể hiện Latency P95 spike > 2000ms khi bật incident `rag_slow` cho feature `refund` | Challenge Incident | Ready on Dashboard UI |
| `13_challenge_trace.png` | Langfuse trace thể hiện span retrieval bị trễ ~2500ms khi `rag_slow` active | Challenge Trace | Ready on Langfuse UI |
| `14_challenge_logs.png` | Log line chứa `correlation_id` của challenge request bị chậm | Challenge Log Evidence | Ready in `data/logs.jsonl` |

---

## 3. Sample Log Line Evidences from `data/logs.jsonl`

### Correlation ID & Enrichment Context Example
```json
{
  "service": "api",
  "event": "request_received",
  "correlation_id": "req-5c8b783f",
  "user_id_hash": "867738e76862",
  "session_id": "k3-challenge-s02",
  "feature": "refund",
  "model": "claude-sonnet-4-5",
  "env": "dev",
  "ts": "2026-08-11T03:07:04.252069Z",
  "payload": {"message_preview": "What proof is required for a refund?"}
}
```

### PII Redaction Example
```json
{
  "service": "api",
  "event": "request_received",
  "correlation_id": "req-e0550ae6",
  "payload": {"message_preview": "What is the policy for PII and credit card [REDACTED_CREDIT_CARD]?"}
}
```
