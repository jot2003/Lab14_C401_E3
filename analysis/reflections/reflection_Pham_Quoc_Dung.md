# Báo cáo cá nhân - Phạm Quốc Dũng (D14-T03: Multi-Judge Consensus)

## 1) Checklist báo cáo cá nhân cần chuẩn bị

- Phạm vi công việc được giao và file chịu trách nhiệm.
- Minh chứng kỹ thuật bằng commit, mô-đun đã sửa, logic đã triển khai.
- Kết quả định lượng sau khi chạy pipeline (điểm, agreement, tỷ lệ review tay, quyết định gate).
- Chiều sâu kỹ thuật: nêu rõ cách tính, trade-off và các rủi ro còn tồn tại.
- Vấn đề phát sinh và cách xử lý cụ thể trong quá trình tích hợp.
- Kế hoạch cải tiến nếu có thêm thời gian.

## 2) Phạm vi công việc được giao

- Nhiệm vụ chính: D14-T03 (Multi-Judge Consensus).
- File chính phụ trách: `engine/llm_judge.py`.
- File tích hợp liên quan: `engine/runner.py`, `main.py`.

## 3) Đóng góp kỹ thuật (Engineering Contribution)

- Triển khai lớp `LLMJudge` hỗ trợ chấm bởi nhiều model judge (`gpt-4o`, `gpt-4o-mini`).
- Xây dựng 2 luồng chấm điểm: luồng online gọi OpenAI API qua `AsyncOpenAI` và luồng fallback heuristic để đảm bảo pipeline không bị dừng khi thiếu API key hoặc lỗi mạng.
- Chuẩn hóa output của judge theo schema thống nhất gồm `final_score`, `agreement_rate`, `max_score_gap`, `conflict_resolved_by`, `requires_manual_review`, `individual_scores`, `judge_details`.
- Tích hợp logic đa giám khảo vào pipeline benchmark: `runner` gọi `evaluate_multi_judge()` cho từng test case, `main` tổng hợp thêm `manual_review_rate` và `judge_model_avg_scores`.
- Minh chứng commit liên quan đến D14-T03: `9183208`, `939e56f`, `4792980`.

## 4) Chiều sâu kỹ thuật (Technical Depth)

- Công thức đồng thuận:
- `max_gap = max(scores) - min(scores)`.
- `agreement_rate = max(0, 1 - max_gap / 4)`.
- Thang điểm 1-5 được chuẩn hóa về 0-1 để dễ theo dõi độ nhất quán giữa judge.
- Chiến lược xử lý xung đột:
- Nếu `max_gap <= 1.0` thì lấy trung bình (`mean`).
- Nếu `max_gap > 1.0` thì lấy `median` và bật `requires_manual_review = true`.
- Tư duy độ tin cậy: multi-judge giúp giảm thiên lệch từ 1 model đơn lẻ, fallback heuristic giúp hệ thống bền vững khi môi trường thiếu khóa hoặc API gián đoạn.

## 5) Kết quả định lượng (theo lần chạy mới nhất)

- Tổng số case: `53`.
- `avg_score`: `3.7217`.
- `agreement_rate`: `0.8939`.
- `manual_review_rate`: `0.0566`.
- `pass_rate`: `0.8113` (43 pass, 7 fail).
- Chi phí ước tính cho judge: `judge_calls = 106`, `estimated_usd = 0.075843`, `cost_per_case_usd = 0.001431`.
- Kết quả regression gate: `RELEASE` (đạt toàn bộ ngưỡng).

## 6) Vấn đề phát sinh và cách xử lý (Problem Solving)

- Vấn đề 1: Merge conflict tại `engine/runner.py` khi đồng bộ từ `main`.
- Cách xử lý: giữ cả retrieval trace mới của T02 và status logic của D14-T03 để không mất tính tương thích.
- Vấn đề 2: Sai khác định dạng phản hồi từ LLM judge.
- Cách xử lý: thêm parser JSON an toàn, chuẩn hóa subscore, giới hạn score về [1, 5].
- Vấn đề 3: Rủi ro hệ thống dừng khi thiếu `OPENAI_API_KEY`.
- Cách xử lý: fallback heuristic và gắn cờ `fallback_reason` để truy vết.

## 7) Bài học rút ra

- Muốn đánh giá ổn định phải ưu tiên schema output rõ ràng trước khi tối ưu prompt.
- Multi-judge chỉ hữu ích khi có cơ chế hợp nhất điểm minh bạch và kiểm soát xung đột.
- Số liệu cost cần đi kèm quality để quyết định phát hành mang tính kỹ thuật thay vì cảm tính.

## 8) Kế hoạch cải tiến nếu có thêm thời gian

- Bổ sung phân tích agreement theo từng loại câu hỏi (fact-check, adversarial, multi-hop).
- Áp dụng chiến lược cascade để giảm chi phí (mini judge trước, judge lớn khi gap cao).
- Đánh giá thêm chỉ số inter-rater reliability nâng cao (ví dụ Cohen's Kappa) để so sánh với agreement_rate.
