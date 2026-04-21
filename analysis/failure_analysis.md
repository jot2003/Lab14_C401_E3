# Báo cáo Phân tích Thất bại (Failure Analysis Report)
> **Tác giả:** Nguyễn Thành Nam (2A202600205) — Task D14-T04  
> **Ngày:** 21/04/2026  
> **Dataset:** `data/golden_set.jsonl` — 53 test cases  
> **Phiên bản Agent phân tích:** Agent_V2_Optimized

---

## 1. Tổng quan Benchmark

| Chỉ số | Giá trị |
|---|---|
| Tổng số cases | 53 |
| Pass (score ≥ 3.0) | 20 (37.7%) |
| Fail (score < 3.0) | 33 (62.3%) |
| Điểm RAGAS — Faithfulness | 0.90 |
| Điểm RAGAS — Relevancy | 0.80 |
| Hit Rate (Retrieval) | 1.00 ✅ |
| MRR (Retrieval) | 0.50 |
| LLM-Judge trung bình (V2) | **2.94 / 5.0** |
| LLM-Judge — GPT-4o | 3.02 / 5.0 |
| LLM-Judge — GPT-4o-mini | 2.87 / 5.0 |
| Agreement Rate (2 judges) | 0.963 (96.3%) |
| Manual Review Rate | 0.0% |

**Nhận xét tổng quan:** Pipeline metric hiện tại cho thấy Retrieval đạt tốt theo chỉ số đang log (`Hit Rate = 1.00`, `MRR = 0.50`). Tuy nhiên vẫn có rủi ro ở lớp mapping ID/semantic relevance (ID dạng filename vs logical doc ID), nên phần cần ưu tiên khắc phục vẫn là **Generation**, đồng thời chuẩn hóa lại cách đo Retrieval để tránh hiểu sai.

---

## 2. Phân nhóm lỗi (Failure Clustering)

| Nhóm lỗi | Số lượng | Accuracy subscore | Nguyên nhân xác định |
|---|---|---|---|
| **Placeholder Response** | 53/53 (100%) | 0.05–0.15 | Agent trả về template `[Câu trả lời mẫu]` thay vì nội dung thực |
| **ID Mismatch (Retrieval)** | 53/53 (100%) | — | `retrieved_ids` = `policy_handbook.pdf` không khớp `expected_ids` (doc-specific IDs) |
| **Low Accuracy Token Overlap** | 53/53 (100%) | avg 0.056 | Answer tokens gần như không overlap với ground truth |
| **Completeness False Positive** | 53/53 (100%) | completeness = 1.0 | Heuristic judge chấm completeness cao vì độ dài tương đương, không kiểm tra nội dung |
| **No API Key — Fallback Mode** | 53/53 (100%) | — | Không có `OPENAI_API_KEY` → toàn bộ judge chạy heuristic_local, không phải LLM thật |

---

## 3. Phân tích 5 Whys — 3 Case tệ nhất

### Case #1: "What are the four main components of a RAG system?"
**Score: 2.71/5.0 — Accuracy: 0.056**

1. **Symptom:** Agent trả về `[Câu trả lời mẫu]`, score accuracy chỉ 0.056/1.0 — gần như không có token overlap với ground truth.
2. **Why 1:** LLM không sinh ra câu trả lời thực — `answer_text` là chuỗi template cố định.
3. **Why 2:** `MainAgent.query()` không gọi LLM thật mà trả về placeholder hardcode (`"[Câu trả lời mẫu]"`).
4. **Why 3:** Module `agent/main_agent.py` chưa được implement — chỉ là stub để hệ thống chạy được mà không cần API key.
5. **Why 4:** Không có `.env` file chứa `OPENAI_API_KEY` → agent không thể kết nối LLM backend.
6. **Root Cause:** **Generation pipeline chưa implement** — `MainAgent` là stub, không tích hợp LLM thật. Đây là lỗi kiến trúc cấp module, không phải lỗi prompting hay chunking.

---

### Case #2: "How does RAG reduce hallucinations compared to a standard LLM?"
**Score: 2.80/5.0 — Accuracy: 0.095**

1. **Symptom:** Agent trả lời đúng format tiếng Việt nhưng nội dung câu trả lời là `[Câu trả lời mẫu]` — hoàn toàn không đề cập đến hallucination, grounding, hay so sánh LLM vs RAG.
2. **Why 1:** Accuracy chỉ 0.095 vì answer tokens (`trả`, `lời`, `mẫu`) không overlap với ground truth (`grounding`, `context`, `hallucination`).
3. **Why 2:** Heuristic judge tính overlap bằng token matching — câu hỏi phức tạp multi-concept cần LLM judge thật để đánh giá semantic similarity.
4. **Why 3:** Không có `OPENAI_API_KEY` → judge fallback về heuristic, không thể đánh giá semantic.
5. **Why 4:** `expected_ids = ["doc_rag_intro", "doc_hallucination"]` (2 docs) nhưng `retrieved_ids = ["policy_handbook.pdf"]` — sai hoàn toàn, agent không truy xuất đúng tài liệu.
6. **Root Cause:** **Hai lỗi song song:** (a) Agent stub không sinh câu trả lời thực; (b) Retrieval ID format chưa đồng bộ giữa golden set và agent output — `expected_ids` dùng logical document IDs, còn `retrieved_ids` trả về filename, làm tăng rủi ro sai lệch khi diễn giải chất lượng retrieval.

---

### Case #3: "Can a RAG system eliminate hallucinations entirely?"
**Score: 2.88/5.0 — Multi-doc expected, single doc retrieved**

1. **Symptom:** Câu hỏi yêu cầu kiến thức từ 2 tài liệu (`doc_rag_intro` + `doc_hallucination`), nhưng Agent chỉ truy xuất 1 tài liệu (`policy_handbook.pdf`) và đưa ra câu trả lời placeholder.
2. **Why 1:** Agent không biết cần join context từ nhiều document — generation không nhận được đủ thông tin.
3. **Why 2:** Retrieval stage chỉ trả về 1 document thay vì top-K relevant documents.
4. **Why 3:** `MainAgent` stub không implement multi-doc retrieval strategy — trả về cố định 1 file.
5. **Why 4:** Golden dataset không được thiết kế align với nguồn tài liệu thực trong vector store.
6. **Root Cause:** **Ingestion pipeline thiếu đồng bộ với golden dataset** — document IDs trong `expected_retrieval_ids` không tương ứng với ID thực trong vector store. Cần chuẩn hóa ID scheme trong cả SDG pipeline và ingestion pipeline.

---

## 4. Tóm tắt Root Causes theo Layer

| Layer | Lỗi phát hiện | Mức độ ảnh hưởng |
|---|---|---|
| **Agent/Generation** | `MainAgent` là stub, trả về placeholder — chưa implement LLM call | 🔴 Critical (100% cases fail) |
| **Retrieval ID Mapping** | `retrieved_ids` dùng filename, `expected_ids` dùng logical doc ID — chưa đồng bộ cách định danh | 🟠 High (rủi ro lệch interpretation metric) |
| **Ingestion/Vector Store** | Document IDs trong vector store không đồng bộ với golden dataset | 🟠 High |
| **Judge Evaluation** | Heuristic judge chấm completeness = 1.0 sai do không kiểm tra semantic | 🟡 Medium |
| **Configuration** | Thiếu `OPENAI_API_KEY` → không thể chạy live LLM judge | 🟡 Medium |

---

## 5. Kế hoạch cải tiến (Action Plan)

### Ưu tiên P0 — Phải fix trước khi release:
- [ ] **Implement `MainAgent.query()`** với LLM call thực (GPT-4o-mini) và context injection từ retrieved documents.
- [ ] **Chuẩn hóa Document ID scheme** — đồng bộ logical IDs giữa SDG pipeline (`synthetic_gen.py`), ingestion pipeline, và vector store index.
- [ ] **Setup `.env`** với `OPENAI_API_KEY` để judge chạy live thay vì heuristic fallback.

### Ưu tiên P1 — Nâng cao chất lượng:
- [ ] **Thêm Multi-doc Retrieval** — cấu hình `top_k=5` và merge context từ nhiều chunk trước khi generation.
- [ ] **Thay Heuristic Judge** bằng LLM-based semantic judge — heuristic token overlap không đo được semantic similarity, gây false positive trên completeness.
- [ ] **Thêm Reranking step** (Cross-encoder) sau retrieval để nâng MRR từ 0.5 lên > 0.7.

### Ưu tiên P2 — Tối ưu chi phí:
- [ ] **Cascade Judge Strategy** — chạy `gpt-4o-mini` trước ($0.00015/1K tokens), chỉ escalate sang `gpt-4o` khi score gap > 1.0 → tiết kiệm ~35% chi phí eval.
- [ ] **Cache judge results** — dùng hash(question + answer) làm cache key để tránh re-judge identical responses.
- [ ] **Semantic Chunking** thay vì Fixed-size chunking — giảm noise trong context, tăng accuracy mà không cần tăng top_k (giảm token cost).

---

## 6. Regression Gate Summary

| Phiên bản | avg_score | hit_rate | agreement_rate | Quyết định |
|---|---|---|---|---|
| Agent_V1_Base | ~2.868 | 1.0 | ~0.963 | — (baseline) |
| Agent_V2_Optimized | 2.944 | 1.0 | 0.963 | **ROLLBACK** ❌ |

**Lý do ROLLBACK:** V2 `avg_score = 2.944 < 3.0` (ngưỡng tối thiểu) mặc dù delta dương (+0.076). Hệ thống chưa đạt chất lượng tối thiểu để release — cần implement `MainAgent` thật trước.

> **Ghi chú kỹ thuật (D14-T04):** Logic Regression Gate trong `main.py` đã được nâng cấp từ "chỉ xét delta" thành **5-threshold multi-gate** gồm: `min_avg_score=3.0`, `min_hit_rate=0.8`, `min_agreement_rate=0.7`, `max_manual_review=0.10`, `min_score_delta=-0.05`. Bất kỳ threshold nào fail → ROLLBACK.
