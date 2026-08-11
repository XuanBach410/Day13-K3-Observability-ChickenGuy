# Operational Alerts & Runbook

Mỗi alert dựa trên triệu chứng người dùng (symptom-based) và SLO, cung cấp quy trình 7 bước điều tra chi tiết (Metrics -> Traces -> Spans -> Logs -> Root Cause -> Mitigation -> Escalation).

---

## Alert 1: High Latency P95

- **Tên**: `high_latency_p95`
- **Severity**: `critical`
- **SLI/SLO liên quan**: Latency P95 <= 3000ms (SLO target: 99.5%)
- **Điều kiện và thời gian duy trì**: `p95(latency_ms) > 3000ms` duy trì liên tục trong 5 phút.
- **Ảnh hưởng tới người dùng**: Người dùng gặp phản hồi chậm từ chatbot/API (`/chat`), gây trải nghiệm kém hoặc timeout.
- **Ba bước kiểm tra đầu tiên**:
  1. **Metrics**: Mở panel *Latency percentiles* trên Dashboard để xác định khoảng thời gian latency spike và kiểm tra xem có tập trung vào feature/model nào không (`feature="refund"` hoặc `feature="qa"`).
  2. **Traces & Spans**: Truy cập Langfuse console, lọc theo time range của alert và sắp xếp theo duration giảm dần. Mở trace waterfall để xác định span chậm (ví dụ: `retrieve` / RAG retrieval hay LLM generation).
  3. **Logs**: Copy `correlation_id` từ trace chậm, query trong `data/logs.jsonl` để lấy toàn bộ log lifecycle (`request_received`, `response_sent`) và kiểm tra `latency_ms` chi tiết.
- **Mitigation tạm thời**:
  - Nếu do incident `rag_slow` gây ra trong mock/lab environment, kiểm tra và tắt incident via API: `POST /incidents/rag_slow/disable`.
  - Trong production real setup: Bật cache cho RAG retrieval context, áp dụng request timeout (ví dụ: 2000ms cho RAG step), hoặc tự động fallback sang static KB response.
- **Escalation**: Báo cho **Trần Xuân Bách** (Integration Lead) và **Phạm Thị Phương Linh** (Metrics Lead) nếu latency không hạ sau khi áp dụng mitigation trong 10 phút.
- **Owner**: Phạm Thị Phương Linh

---

## Alert 2: High Error Rate

- **Tên**: `high_error_rate`
- **Severity**: `warning`
- **SLI/SLO liên quan**: Error Rate <= 2.0% (SLO target: 99.0%)
- **Điều kiện và thời gian duy trì**: `error_rate_pct > 2%` duy trì liên tục trong 5 phút.
- **Ảnh hưởng tới người dùng**: Người dùng nhận HTTP 500/Internal Server Error khi gửi yêu cầu trò chuyện.
- **Ba bước kiểm tra đầu tiên**:
  1. **Metrics**: Mở panel *Error rate and breakdown* trên Dashboard để kiểm tra `error_rate_pct` và phân bối `error_type` (ví dụ: `ToolFailure`, `TimeoutError`, `HTTPException`).
  2. **Traces & Spans**: Vào Langfuse, filter traces theo status `ERROR` hoặc HTTP 500 tag. Mở trace để xem span gây ra lỗi.
  3. **Logs**: Tìm log records có `event="request_failed"`, lọc `error_type` và `payload.detail`. Đối chiếu `correlation_id` để biết request input.
- **Mitigation tạm thời**:
  - Nếu do incident `tool_fail` trong lab: Tắt incident via API `POST /incidents/tool_fail/disable`.
  - Với lỗi upstream model API / connection failure: Chuyển sang fallback model provider hoặc áp dụng circuit breaker pattern.
- **Escalation**: Báo cho **Trần Xuân Bách** (Integration Lead) để kiểm tra API middleware & downstream integrations.
- **Owner**: Phạm Thị Phương Linh

---

## Alert 3: Quality Drop

- **Tên**: `quality_drop`
- **Severity**: `warning`
- **SLI/SLO liên quan**: Quality Score Avg >= 0.75 (SLO target: 95.0%)
- **Điều kiện và thời gian duy trì**: `mean(quality_score) < 0.75` trong cửa sổ 10 phút.
- **Ảnh hưởng tới người dùng**: Phản hồi chatbot có chất lượng thấp, thiếu ngữ cảnh retrieved docs hoặc chứa nhãn redaction không phù hợp.
- **Ba bước kiểm tra đầu tiên**:
  1. **Metrics**: Kiểm tra panel *Quality proxy* trên Dashboard để xác định xu hướng suy giảm điểm quality score.
  2. **Traces & Spans**: Mở Langfuse traces có `quality_score` thấp, kiểm tra metadata `prompt_version`, `prompt_label`, và `prompt_name` để xem có sự cố regression sau khi release prompt mới hay không.
  3. **Logs**: Lọc các log event `response_sent` có `quality_score < 0.75`, kiểm tra `payload.answer_preview` và `feature`.
- **Mitigation tạm thời**:
  - Nếu mới đổi sang prompt version candidate: Thực hiện rollback prompt label `production` về phiên bản `v1`/`baseline` an toàn ngay trên Langfuse hoặc qua config `.env`.
- **Escalation**: Báo cho **Trịnh Quốc Trọng** (QA Lead) và **Phạm Thị Phương Linh** (Metrics Lead) để đánh giá lại prompt benchmarks.
- **Owner**: Phạm Thị Phương Linh
