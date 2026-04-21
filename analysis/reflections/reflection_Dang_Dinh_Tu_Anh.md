# Reflection — Đặng Đình Tú Anh (D14-T01: Tạo Dataset Tổng hợp – SDG)

## Tóm tắt nhiệm vụ
Chịu trách nhiệm toàn bộ `data/synthetic_gen.py` — xây dựng luồng SDG và tạo golden evaluation dataset với ≥50 test cases chất lượng cao, bao gồm cả các trường hợp thông thường lẫn adversarial.

## Những gì tôi đã làm

- Thiết kế corpus gồm 12 tài liệu kiến thức bao phủ các chủ đề: kiến trúc RAG, framework RAGAS, các chỉ số đánh giá retrieval (Hit Rate, MRR), LLM-as-Judge, Multi-Judge Consensus, Regression Testing, SDG, phát hiện Hallucination, chiến lược Chunking, tối ưu chi phí, phân tích lỗi (Failure Analysis), và Position Bias.
- Tạo 41 test cases thông thường (dễ/trung bình/khó) với `expected_retrieval_ids` ánh xạ chính xác đến từng tài liệu trong corpus.
- Tạo 12 adversarial/red-teaming cases: prompt injection, jailbreak, goal hijacking, out-of-context, câu hỏi mơ hồ, thông tin mâu thuẫn, hallucination trigger, latency stress (đầu vào cực dài), multi-hop reasoning và câu hỏi đính chính.
- Tổng cộng: **53 JSONL entries hợp lệ** với đầy đủ các trường `question`, `expected_answer`, `context`, `metadata.expected_retrieval_ids`.
- Triển khai pipeline async (`asyncio`) để hỗ trợ gọi OpenAI song song khi dùng `--openai`, đảm bảo tốc độ sinh dữ liệu không bị nghẽn cổ chai I/O.
- Thêm flag `--openai` (dùng `gpt-4o-mini` để augment) và `--count N` để kiểm soát số lượng mục tiêu.
- Tích hợp bước tự kiểm tra JSONL ngay sau khi ghi file — script thoát với exit code 1 nếu có dòng lỗi.

## Đóng góp kỹ thuật (Engineering Contribution)

> **Git commits:** [`8608681`](../../commit/860868122fb1a0d9a3cd172db7fa8a6dc1791d52) `feat: enhance .gitignore and implement synthetic data generation script` · [`0e97452`](../../commit/0e9745285a64d7358ff0015ad6ff5036d7fddf43) `fix: clean up .gitignore by removing unnecessary report and analysis directories`

Module `synthetic_gen.py` là **điều kiện tiên quyết** của toàn pipeline: nếu dataset sai định dạng hoặc thiếu `expected_retrieval_ids`, cả bước Retrieval Eval (D14-T02) lẫn Judge (D14-T03) đều không thể cho kết quả có ý nghĩa.

Các quyết định thiết kế phức tạp:
- **Async generation** (`8608681`)**:** Dùng `asyncio.gather()` để gọi OpenAI song song theo từng document trong corpus, tránh chờ tuần tự và đáp ứng yêu cầu < 2 phút cho 50+ cases.
- **Ground-truth ID mapping** (`8608681`)**:** Mỗi case có `expected_retrieval_ids` là list các `doc_id` — hỗ trợ tính Hit Rate@k và MRR chính xác ở tầng retrieval, kể cả các câu hỏi multi-hop cần nhiều tài liệu.
- **Adversarial schema chuẩn hóa** (`8608681`)**:** Các case red-team có `"expected_retrieval_ids": []` (trống) để retrieval evaluator biết rằng không có tài liệu nào cần được tìm thấy — tránh làm sai lệch chỉ số Hit Rate tổng thể.

## Chiều sâu kỹ thuật (Technical Depth)

**MRR (Mean Reciprocal Rank):**
MRR = mean(1/rank_i) với rank_i là vị trí (1-indexed) của tài liệu liên quan đầu tiên trong kết quả retrieval của câu hỏi thứ i. MRR = 1.0 khi tài liệu đúng luôn ở vị trí 1; MRR = 0.5 khi luôn ở vị trí 2. Tôi thiết kế dataset sao cho các câu hỏi dễ có đúng 1 `expected_retrieval_id`, còn câu hỏi multi-hop có 2–3 để thử thách hệ thống retrieval ở mức cao hơn.

**Cohen's Kappa:**
Kappa = (P_o − P_e) / (1 − P_e), trong đó P_o là tỉ lệ đồng thuận thực tế và P_e là tỉ lệ đồng thuận kỳ vọng theo xác suất ngẫu nhiên. Kappa > 0.8 = đồng thuận rất cao; < 0.6 = không đáng tin cậy. Tôi xây dựng các trường hợp kiểm tra với ground-truth rõ ràng để các judge model có thể đạt Kappa cao — trường hợp mơ hồ được gắn nhãn `type: ambiguous` để tách riêng khi phân tích độ tin cậy.

**Position Bias:**
Đây là xu hướng của judge LLM thiên vị câu trả lời xuất hiện đầu tiên, bất kể chất lượng. Trong dataset, tôi đưa vào câu hỏi `correction` (người dùng đính chính thông tin sai) để kiểm tra xem agent có bị ảnh hưởng bởi thứ tự thông tin trong context hay không. Cách phát hiện: chạy evaluation với hoán đổi thứ tự A–B và B–A, nếu điểm thay đổi đáng kể thì bias tồn tại.

**Trade-off Chi phí – Chất lượng:**
Dùng `gpt-4o-mini` thay vì `gpt-4o` cho bước augment SDG giúp giảm ~10× chi phí với chất lượng chấp nhận được cho việc tạo câu hỏi từ context đã có sẵn. Tuy nhiên, các case adversarial phức tạp (hallucination trigger, multi-hop) được viết tay để đảm bảo độ chính xác — đây là ví dụ thực tế của chiến lược dùng model nhỏ cho filtering, model lớn (hoặc human) cho edge cases.

## Giải quyết vấn đề (Problem Solving)

**Vấn đề 1 — Phân phối độ khó lệch:**
Phiên bản đầu có quá nhiều câu hỏi dễ vì các prompt đơn giản tập trung vào fact-check. Giải pháp: phân loại rõ ràng 3 mức (easy/medium/hard) và ràng buộc mỗi tài liệu phải có ít nhất 1 câu hard dạng reasoning hoặc critical-thinking, tránh hiệu ứng ceiling (tất cả đều đạt điểm tối đa).

**Vấn đề 2 — Adversarial cases thiếu expected answer chuẩn:**
Ban đầu expected answer cho out-of-context chỉ là chuỗi rỗng, khiến judge không thể đánh giá. Giải pháp: định nghĩa expected answer là câu từ chối lịch sự + giải thích phạm vi hệ thống (ví dụ: "Tôi không có thông tin về chủ đề đó trong knowledge base").

**Vấn đề 3 — Encoding trên Windows** (`0e97452`)**:**
Script gặp lỗi `UnicodeEncodeError` khi in ký tự Unicode ra console Windows. Giải pháp: thêm `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` ở đầu file — fix được hội nhập vào main branch qua commit `0e97452`.

## Điều tôi học được

- Chất lượng dataset tổng hợp quyết định trực tiếp tính hợp lệ của evaluation — "garbage in, garbage out" áp dụng đặc biệt mạnh ở đây vì mọi chỉ số downstream đều phụ thuộc vào ground truth.
- Thiết kế adversarial cases đòi hỏi phải hiểu cả capability lẫn failure mode của agent, không chỉ đơn thuần là nghĩ ra câu hỏi khó.
- Ground-truth ID rõ ràng theo từng tài liệu giúp attribution error (phân biệt lỗi retrieval vs. lỗi generation) trở nên khả thi và có ý nghĩa.
- Async pipeline không chỉ là tối ưu hiệu năng — nó là yêu cầu bắt buộc khi gọi LLM API ở quy mô hàng chục/trăm cases.

## Nếu có thêm thời gian

- Thêm paraphrase variants bằng OpenAI để tăng đa dạng ngôn ngữ mà không thay đổi nội dung.
- Triển khai stratified sampling để đảm bảo phân phối cân bằng giữa các mức độ khó và loại câu hỏi.
- Bổ sung multi-hop cases yêu cầu lý luận qua 3+ tài liệu, kiểm tra giới hạn của retrieval pipeline khi cần kết hợp nhiều nguồn.
- Tích hợp schema validation tự động (Pydantic) để đảm bảo mọi case đều hợp lệ trước khi ghi file.
