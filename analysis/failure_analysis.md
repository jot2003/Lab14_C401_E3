# Bao cao Phan tich That bai (Failure Analysis Report)
> Tac gia: Nguyen Thanh Nam (2A202600205) - Task D14-T04
> Ngay: 21/04/2026
> Dataset: `data/golden_set.jsonl` - 53 test cases
> Phien ban phan tich: Agent_V2_Optimized

---

## 1. Tong quan benchmark (lan chay moi nhat)

| Chi so | Gia tri |
|---|---|
| Tong so cases | 53 |
| Pass (score >= 3.0) | 43 (81.1%) |
| Fail (score < 3.0) | 10 (18.9%) |
| Review (requires_manual_review) | 3 (5.7%) |
| Avg score (V2) | **3.7406 / 5.0** |
| Hit Rate (retrieval) | 1.0000 |
| Agreement Rate (judge) | 0.9033 |
| Manual Review Rate | 0.0566 |
| Gate decision | **RELEASE** |

**Nhan xet:** He thong da vuot moi nguong target (avg_score >= 3.6, pass_rate >= 0.75, hit_rate >= 0.90, agreement_rate >= 0.88). Cai thien chinh den tu: (1) sua logic hit_rate/MRR cho adversarial/OOS cases (expected_ids=[] → 1.0), (2) nang cap retrieval bang IDF-weighted scoring va title bonus.

---

## 2. Phan nhom loi (failure clustering)

| Nhom loi | So luong | Dau hieu |
|---|---|---|
| Low faithfulness | ~5 cases | `faithfulness < 0.5`, answer gom nhieu context nhung chua focus |
| Judge disagreement gap >= 1 | 3 cases | score giua 2 judge lech >= 1 diem → manual review |
| Adversarial borderline | ~2 cases | case ambiguous/conflicting nhan diem 2-3 |

**Tac dong:** Khong con retrieval miss cases. Fail cases con lai tap trung vao borderline scoring va case kho (ambiguous, multi-hop). Day la ket qua tot cho he thong keyword-based.

---

## 3. 5 Whys cho 2 case tieu bieu

### Case A - "Is a high score always better?" (ambiguous case)
1. Symptom: score 2-3, answer chua phan biet ro metric types.
2. Why 1: extractive answer lay context chung, thieu phan biet cost vs quality.
3. Why 2: keyword retrieval khong phan biet "score" context (cost vs quality).
4. Why 3: khong co intent classification truoc retrieval.
5. Root cause: extractive RAG khong xu ly tot cau hoi can suy luan tong hop.

### Case B - Judge disagreement cases
1. Symptom: 2 judge cho diem lech > 1 diem.
2. Why 1: answer dung nhung chua day du → GPT-4o danh 4, GPT-4o-mini danh 2.
3. Why 2: rubric completeness nhay cam voi cach dien dat.
4. Why 3: chua co case-type-aware calibration.
5. Root cause: borderline answers trigger different thresholds across models.

---

## 4. Tong hop root causes theo layer

| Layer | Van de hien tai | Muc do |
|---|---|---|
| Retrieval | Da cai thien: IDF + title bonus → hit_rate = 1.0 | Resolved |
| Context grounding | Faithfulness thap o mot so case explain/compare | Medium |
| Judge calibration | Co disagreement o 3 case borderline | Low |
| Answer generation | Extractive approach gioi han chat luong multi-hop | Medium |

---

## 5. Ke hoach cai tien

### P0 (da hoan thanh)
- ✅ Sua hit_rate/MRR logic cho empty expected_ids (adversarial/OOS).
- ✅ Nang cap retrieval bang IDF-weighted scoring + title bonus.
- ✅ Dat target: avg_score=3.74, pass_rate=0.81, hit_rate=1.0, agreement=0.90.

### P1
- Them semantic reranking (embedding-based) de cai thien multi-hop cases.
- Bo sung tie-break strategy khi judge gap >= 1.
- Them breakdown metric theo difficulty/type.

### P2
- Cascade judge strategy (mini truoc, 4o cho case can escalation) de giam chi phi.
- Cache judge responses theo hash(question + answer).
- Chuyen tu extractive sang abstractive generation (LLM-based) cho chat luong cao hon.

---

## 6. Regression gate summary (lan chay moi nhat)

| Version | avg_score | hit_rate | agreement_rate | manual_review_rate | Decision |
|---|---|---|---|---|---|
| Agent_V1_Base | 3.6981 | 1.0000 | 1.0000 | 0.0000 | Baseline |
| Agent_V2_Optimized | 3.7406 | 1.0000 | 0.9033 | 0.0566 | **RELEASE** |

**Ket luan:** V2 vuot nguong gate va dat moi target metric. Delta = +0.042 so voi V1. He thong san sang deploy.
