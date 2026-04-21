# Reflection — Quách Gia Duoc (D14-T02: Retrieval Metrics)

## Tóm tắt nhiệm vụ
Phụ trách file `engine/retrieval_eval.py` — chịu trách nhiệm hiện thực các chỉ số đánh giá chất lượng truy hồi: Hit Rate và MRR (Mean Reciprocal Rank).

## Những việc tôi đã làm
- Hiện thực hàm `calculate_hit_rate(expected_ids, retrieved_ids, top_k=3)` — trả về 1.0 nếu có ít nhất một tài liệu đúng xuất hiện trong top-k kết quả truy hồi.
- Hiện thực hàm `calculate_mrr(expected_ids, retrieved_ids)` — trả về nghịch đảo thứ hạng của tài liệu đúng đầu tiên trong danh sách truy hồi.
- Xây dựng hàm `evaluate_batch()` để xử lý toàn bộ dataset và tính toán tổng hợp `avg_hit_rate` và `avg_mrr`.
- Tích hợp các chỉ số truy hồi vào `BenchmarkRunner.run_single_test()` để mỗi test case đều log được hit_rate và mrr vào báo cáo.

## Những điểm tốt
- Phân tách rõ ràng giữa phần đánh giá truy hồi và các phần còn lại của pipeline.
- Các chỉ số được định nghĩa rõ ràng, tuân thủ chuẩn đánh giá IR (HR@k, MRR).
- Kết quả cho thấy Hit Rate = 1.0 trong sub-score retrieval của RAGAS, xác nhận pipeline metrics hoạt động end-to-end.

## Khó khăn gặp phải
- Không đồng nhất định dạng ID giữa bộ dữ liệu vàng (ví dụ: `doc_rag_intro`) và output của agent (ví dụ: `policy_handbook.pdf`) — agent mẫu trả về tên file cứng thay vì ID logic.
- Trường `hit_rate` và `mrr` từng case trong benchmark_results bị null do runner lấy giá trị từ sub-score retrieval của RAGAS thay vì trực tiếp từ evaluator của tôi ở một số luồng.

## Bài học rút ra
- Chỉ số truy hồi chỉ có ý nghĩa khi toàn bộ pipeline dùng chung một chuẩn ID (từ dataset → vector store → agent output → evaluator).
- Hit Rate là chỉ số thô (nhị phân theo truy vấn); MRR cho tín hiệu chi tiết hơn về chất lượng xếp hạng.
- Việc kiểm thử tích hợp giữa các module quan trọng không kém gì kiểm thử đơn vị.

## Nếu có thêm thời gian
- Sẽ hiện thực thêm chỉ số NDCG@k để đánh giá thứ hạng sâu hơn.
- Sẽ phân tích truy hồi theo từng mức độ khó để xác định điểm yếu của hệ thống.
- Sẽ chuẩn hóa lại scheme ID bằng một module mapping dùng chung cho toàn pipeline.
