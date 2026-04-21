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
| Pass (score >= 3.0) | 38 (71.7%) |
| Fail (score < 3.0) | 12 (22.6%) |
| Review (requires_manual_review) | 3 (5.7%) |
| Avg score (V2) | **3.4717 / 5.0** |
| Hit Rate (retrieval) | 0.8679 |
| Agreement Rate (judge) | 0.8585 |
| Manual Review Rate | 0.0566 |
| GPT-4o avg | 3.5472 |
| GPT-4o-mini avg | 3.3962 |
| Gate decision | **RELEASE** |

**Nhan xet:** He thong da vuot nguong release (avg_score >= 3.0) va pass du 5 dieu kien gate. Ty le pass tang ro so voi cac lan truoc, nhung van con nhom cau hoi fail do retrieval miss va grounding chua du chat.

---

## 2. Phan nhom loi (failure clustering)

| Nhom loi | So luong | Dau hieu |
|---|---|---|
| Retrieval miss | 4 cases | `hit_rate = 0`, cau tra loi thieu context can thiet |
| Low faithfulness | 7 cases | `faithfulness < 0.5`, grounding yeu |
| Judge disagreement gap >= 1 | 7 cases | score giua 2 judge lech >= 1 diem |
| Low score factual cases | 12 cases | final_score < 3 du retrieval khong phai luc nao fail |

**Tac dong:** Nhom fail hien tai khong con do placeholder response toan bo, ma tap trung vao "case kho / retrieval miss / grounding yeu". Day la dau hieu he thong da chuyen tu loi kien truc sang loi chat luong theo case.

---

## 3. 5 Whys cho 3 case tieu bieu

### Case A - "How does RAG reduce hallucinations compared to a standard LLM?"
1. Symptom: score thap (2.5), faithfulness 0.4579.  
2. Why 1: answer co noi dung lien quan nhung thieu y chinh ve grounding mechanism.  
3. Why 2: context trich xuat khong bao phu du phan "comparison" giua RAG va standard LLM.  
4. Why 3: retrieval top-k dua tren token overlap, de bo sot y nghia semantic.  
5. Why 4: chua co reranking theo semantic relevance.  
6. Root cause: retrieval + context assembly chua toi uu cho cau hoi explain/compare.

### Case B - Nhom retrieval miss (hit_rate = 0)
1. Symptom: retrieved_ids khong trung expected_ids.  
2. Why 1: keyword overlap khong du de bat dung doc trong case multi-hop.  
3. Why 2: expected_retrieval_ids co khi yeu cau 2 doc, nhung top-k khong uu tien dung cap doc.  
4. Why 3: scoring retrieval hien tai chua co trong so cho doc "must-have".  
5. Why 4: chua co bo loc theo intent (factual vs comparative vs adversarial).  
6. Root cause: retrieval strategy don gian, thieu semantic rerank va intent-aware weighting.

### Case C - Judge disagreement >= 1
1. Symptom: 2 judge cho diem lech lon o mot so case border-line.  
2. Why 1: cau tra loi co thanh phan dung nhung chua day du -> moi model danh gia nguong pass/fail khac nhau.  
3. Why 2: rubric completeness va accuracy nhay cam voi cach dien dat.  
4. Why 3: chua co calibration theo type case (adversarial, factual, multi-hop).  
5. Why 4: conflict resolution hien tai dung median/mean, chua co tie-break judge.  
6. Root cause: calibration judge cho nhom case bien gioi chua du sau.

---

## 4. Tong hop root causes theo layer

| Layer | Van de hien tai | Muc do |
|---|---|---|
| Retrieval | Miss mot so case kho, top-k theo token overlap chua du | High |
| Context grounding | Faithfulness thap o mot nhom case explain/compare | High |
| Judge calibration | Co disagreement o case borderline | Medium |
| Cost/performance | Dang su dung live judges, chi phi co the toi uu tiep | Medium |

---

## 5. Ke hoach cai tien

### P0 (ngan han, tac dong cao)
- Them semantic reranking sau retrieval de giam miss cases (`hit_rate=0`).
- Tinh chinh context assembly cho cau hoi compare/explain (bat buoc giu cau then chot).
- Lap lai benchmark va target: pass_rate > 0.80, agreement_rate >= 0.88.

### P1
- Them breakdown metric theo difficulty/type de khoanh vung fail nhanh.
- Bo sung tie-break strategy khi judge gap >= 1 (escalate model/secondary rubric).

### P2
- Cascade judge strategy (mini truoc, 4o cho case can escalation) de giam chi phi.
- Cache judge responses theo hash(question + answer) de tranh cham lap.

---

## 6. Regression gate summary (lan chay moi nhat)

| Version | avg_score | hit_rate | agreement_rate | manual_review_rate | Decision |
|---|---|---|---|---|---|
| Agent_V1_Base | 3.3962 | 0.8679 | 1.0000 | 0.0000 | Baseline |
| Agent_V2_Optimized | 3.4717 | 0.8679 | 0.8585 | 0.0566 | **RELEASE** |

**Ket luan:** V2 vuot nguong gate va du dieu kien release. Muc uu tien tiep theo la giam fail cases o nhom retrieval miss/low-faithfulness de nang pass rate va on dinh agreement.
