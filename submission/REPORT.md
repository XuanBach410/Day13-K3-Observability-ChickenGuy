# Báo cáo Day 13 Observability — Team ChickenGuy

## 1. Thông tin nhóm

- **Tên nhóm**: ChickenGuy
- **Repository URL**: https://github.com/XuanBach410/Day13-K3-Observability-ChickenGuy
- **Commit SHA cuối**: `4616fd50859c35390f24df5ee49a98b3381f7533`
- **Thành viên và vai trò**:
  1. **Trần Xuân Bách** — Nhóm trưởng, Integration Lead & Structured Logging (Correlation ID, contextvars, request lifecycle, trace metadata propagation).
  2. **Đinh Hoài Nam** — PII & Security Specialist (PII detection regex, recursive `scrub_event` processor, secret hygiene audit).
  3. **Phạm Thị Phương Linh** — Metrics, SLO & Alert Engineer (6-panel dashboard contract verification, symptom-based alert rules, operational runbooks).
  4. **Trịnh Quốc Trọng** — QA Lead, Incident Investigation & Report Owner (Public tests, validator verification, official Challenge K3 investigation, evidence index).

---

## 2. Kết quả kỹ thuật

- **Điểm `validate_logs.py`**: **100/100** (Full score: schema hợp lệ, correlation ID propagation đúng, log enrichment đầy đủ context, 0 PII leaks).
- **Tổng số traces**: 32+ log records & 10+ trace runs generated across test suites.
- **Số PII leak còn lại**: **0** (Email, VN phone numbers, CCCD, credit cards, passport patterns đều được redact thành `[REDACTED_<TYPE>]` trước khi persist vào log sink).
- **Link/đường dẫn dashboard**: Configured via `config/dashboard.yaml` and verified with `python scripts/validate_dashboard.py` (**HỢP LỆ: 6/6 panel**).

---

## 3. Logging và tracing

- **Evidence correlation ID**: Mỗi request tạo mới hoặc truyền qua header `x-request-id` có dạng `req-<8-hex-chars>` (ví dụ: `req-121a4481`, `req-e0550ae6`). Xem ảnh bằng chứng: [03_log_correlation_id.png](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/Day13-K3-Observability-ChickenGuy/submission/evidence/03_log_correlation_id.png).
- **Evidence PII redaction**: Tự động lọc qua processor `scrub_event` trước file sink `data/logs.jsonl`. Xem ảnh bằng chứng: [04_pii_redaction.png](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/Day13-K3-Observability-ChickenGuy/submission/evidence/04_pii_redaction.png).
  - Mẫu log thực tế: `{"service": "api", "payload": {"message_preview": "What is the policy for PII and credit card [REDACTED_CREDIT_CARD]?"}}`
- **Evidence trace waterfall**: Cấu trúc trace bao gồm `run` (Agent generation), `retrieve` (RAG document lookup), `FakeLLM.generate` (LLM call). Xem ảnh bằng chứng: [05_langfuse_10_traces.png](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/Day13-K3-Observability-ChickenGuy/submission/evidence/05_langfuse_10_traces.png) và [06_trace_waterfall.png](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/Day13-K3-Observability-ChickenGuy/submission/evidence/06_trace_waterfall.png).
- **Giải thích một span đáng chú ý**: Span `retrieve` trong `mock_rag.py` chịu trách nhiệm tra cứu ngữ cảnh. Khi incident `rag_slow` kích hoạt, span này tạm dừng (sleep) ~2500ms, làm tổng latency của request tăng vọt từ 155ms lên >2650ms.

---

## 4. Prompt versioning

- **Prompt name**: `day13-chat`
- **Version/label baseline**: Version 1 (Labels: `baseline`, `production`).
- **Version/label candidate**: Version 2 (Label: `candidate`).
- **Trace ID của mỗi version**:
  - Baseline (v1): `trace-prompt-v1-production` (`prompt_version="1"`, `prompt_label="production"`)
  - Candidate (v2): `trace-prompt-v2-candidate` (`prompt_version="2"`, `prompt_label="candidate"`)
- **Bằng chứng đổi label hoặc rollback**: Đã thực hiện switch label `production` sang version 2 và diễn giải thao tác rollback an toàn về version 1 khi phát hiện chất lượng phản hồi không đạt ngưỡng target. Xem chi tiết tại [docs/PROMPT_VERSIONING.md](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/Day13-K3-Observability-ChickenGuy/docs/PROMPT_VERSIONING.md).

---

## 5. Dashboard, SLO và alerts

- **Kết quả `validate_dashboard.py`**: **HỢP LỆ: 6/6 panel** có trong dashboard contract.
- **Evidence dashboard**: Tham chiếu file [10_validate_dashboard.txt](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/Day13-K3-Observability-ChickenGuy/submission/evidence/10_validate_dashboard.txt) và ảnh bằng chứng [11_dashboard_6_panels.png](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/Day13-K3-Observability-ChickenGuy/submission/evidence/11_dashboard_6_panels.png).
- **SLO đã chọn và lý do**:
  - `latency_p95_ms`: Objective <= 3000ms (Target: 99.5%) — Bảo đảm trải nghiệm thời gian thực cho người dùng.
  - `error_rate_pct`: Objective <= 2.0% (Target: 99.0%) — Đảm bảo độ tin cậy của API gateway.
  - `daily_cost_usd`: Objective <= $2.50 (Target: 100.0%) — Kiểm soát ngân sách vận hành LLM.
  - `quality_score_avg`: Objective >= 0.75 (Target: 95.0%) — Giữ chất lượng câu trả lời ổn định.
- **Alert rules và runbook**:
  - Cấu hình 3 quy tắc cảnh báo symptom-based trong `config/alert_rules.yaml` (`high_latency_p95`, `high_error_rate`, `quality_drop`).
  - Hướng dẫn vận hành chi tiết 7 bước điều tra (Metrics -> Traces -> Spans -> Logs -> Root Cause -> Mitigation -> Escalation) nằm tại [docs/alerts.md](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/Day13-K3-Observability-ChickenGuy/docs/alerts.md).

---

## 6. Điều tra challenge

- **Challenge ID**: `day13-k3-observability-v1` (Cohort K3, Seed 1303, Latency Threshold: 2000ms, Affected Feature: `refund`).
- **Triệu chứng từ metrics**:
  - Trong quá trình chạy load test với bộ câu hỏi `config/challenge.json`, chỉ số Latency P95 của feature `refund` tăng đột biến lên **2657ms–3446ms**, vượt ngưỡng SLO (2000ms). Xem ảnh bằng chứng: [12_challenge_metrics.png](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/Day13-K3-Observability-ChickenGuy/submission/evidence/12_challenge_metrics.png).
- **Trace ID liên quan**: Trace ID thu thập từ Langfuse có `tags=["lab", "refund", "claude-sonnet-4-5"]` với tổng duration ~2.66s. Xem ảnh bằng chứng: [13_challenge_trace.png](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/Day13-K3-Observability-ChickenGuy/submission/evidence/13_challenge_trace.png).
- **Log line/correlation ID liên quan**:
  - Log correlation IDs: `req-469fd94f`, `req-5c8b783f`, `req-45ccb790`, `req-7e7da748`, `req-b21f3a7c`. Xem ảnh bằng chứng: [14_challenge_logs.png](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/Day13-K3-Observability-ChickenGuy/submission/evidence/14_challenge_logs.png).
  - Mẫu log line:
    `{"service": "api", "latency_ms": 2658, "tokens_in": 29, "tokens_out": 123, "cost_usd": 0.001932, "quality_score": 0.9, "payload": {"answer_preview": "Starter answer..."}, "event": "response_sent", "session_id": "k3-challenge-s01", "feature": "refund", "model": "claude-sonnet-4-5", "correlation_id": "req-469fd94f", "user_id_hash": "026c7a407135", "level": "info", "ts": "2026-08-11T03:07:01.589266Z"}`
- **Root cause**:
  - Span `retrieve` gặp sự cố độ trễ do incident `rag_slow` bị kích hoạt trong bộ giả lập `app/mock_rag.py` (khi `STATE["rag_slow"] = True`, hàm `retrieve()` bị delay nhân tạo 2.5 giây).
- **Fix action**:
  - Tắt trạm sự cố via endpoint điều khiển: `POST /incidents/rag_slow/disable`.
  - Kết quả sau khi khắc phục: Latency của request hạ từ **2657ms** xuống **155ms** (đạt trạng thái bình thường).
- **Preventive measure**:
  1. Cấu hình timeout cho bước RAG retrieval (ví dụ: 1500ms).
  2. Bổ sung cache ngữ cảnh tra cứu cho các thắc mắc phổ biến về chính sách hoàn tiền (`refund`).
  3. Cài đặt cảnh báo `high_latency_p95` kích hoạt khi P95 > 2000ms trong 5 phút.

---

## 7. Đóng góp cá nhân

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| **Trần Xuân Bách** | Middleware correlation ID (`req-<8-hex>`), structlog contextvars binding (`user_id_hash`, `session_id`, `feature`, `model`, `env`), trace metadata correlation integration. | `4ffe871` | Cách truyền correlation ID xuyên suốt request lifecycle và liên kết log ↔ trace trong kiến trúc microservices/AI application. |
| **Đinh Hoài Nam** | Xây dựng bộ PII patterns (email, phone, credit card, CCCD, passport) và processor `scrub_event` lọc PII đệ quy trước khi ghi log. | `4ffe871` | Kỹ thuật bảo vệ dữ liệu nhạy cảm, nguyên tắc Redaction vs Hashing và quy chuẩn bảo mật log trong hệ thống production. |
| **Phạm Thị Phương Linh** | Thiết kế contract 6-panel dashboard (`config/dashboard.yaml`), cấu hình 3 quy tắc cảnh báo `config/alert_rules.yaml` và viết runbook điều tra tại `docs/alerts.md`. | `4ffe871` | Phương pháp xây dựng SLO/SLI chuẩn cho AI app, thiết kế alert dựa trên triệu chứng người dùng và quy trình khắc phục sự cố. |
| **Trịnh Quốc Trọng** | Đánh giá public tests, kiểm thử validator (`validate_logs.py` 100/100, `validate_dashboard.py` 6/6), thực thi điều tra Challenge K3 (`rag_slow`), tổng hợp REPORT.md và evidence index. | `4ffe871` | Quy trình điều tra sự cố chuẩn từ Metrics -> Traces -> Spans -> Logs -> Root Cause -> Mitigation -> Prevention. |
