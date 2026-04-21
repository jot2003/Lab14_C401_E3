# Reflection cá nhân — Hoàng Kim Trí Thành
## Vai trò phụ trách: D14-T05 (Final Integration, Quality Gate, Submission Readiness)

## 1) Bối cảnh và phạm vi công việc
Trong Lab Day14, em đảm nhiệm vai trò tích hợp cuối cùng của toàn nhóm. Nhiệm vụ chính không phải viết một module đơn lẻ, mà là đảm bảo tất cả phần của các thành viên ghép lại thành một hệ thống đánh giá AI hoàn chỉnh, chạy được từ đầu đến cuối và đủ điều kiện nộp bài.

Phạm vi em chịu trách nhiệm gồm:
- Tích hợp toàn bộ pipeline: sinh dữ liệu -> benchmark -> đánh giá -> xuất báo cáo.
- Kiểm tra tính nhất quán giữa các artifacts (JSON report, failure analysis, reflections).
- Chạy quality gate cuối trước khi quyết định GO/NO-GO.
- Chuẩn hóa nội dung nộp bài theo đúng checklist trong README và rubric.

## 2) Những việc kỹ thuật em đã làm

### 2.1. Tích hợp và xác thực luồng chạy end-to-end
Em chạy đi chạy lại chuỗi lệnh chuẩn nhiều vòng để xác nhận không còn lỗi tích hợp:
- `python data/synthetic_gen.py`
- `python main.py`
- `python check_lab.py`

Mục tiêu của em là mỗi lần re-run đều tái tạo được artifacts hợp lệ và không phát sinh lỗi do thay đổi chéo giữa các module.

### 2.2. Chốt quality gate trước khi nộp
Em đối chiếu trực tiếp output của `main.py` với `reports/summary.json` để xác nhận:
- `avg_score`, `hit_rate`, `agreement_rate`, `manual_review_rate` khớp dữ liệu.
- `gate_decision` phản ánh đúng ngưỡng trong regression gate.

Em ưu tiên tính trung thực dữ liệu: không “làm đẹp” report, chỉ dùng số từ lần chạy thật gần nhất.

### 2.3. Xử lý vấn đề tương thích môi trường
Trong quá trình tích hợp, nhóm gặp lỗi encoding trên Windows (cp1252) khi in emoji/Unicode. Em tham gia xử lý để script không crash khi chạy thực tế trên máy demo, nhờ đó tránh rủi ro fail ngay lúc trình bày.

### 2.4. Đồng bộ artifacts nộp bài
Em rà các file bắt buộc và xác nhận đủ:
- `reports/summary.json`
- `reports/benchmark_results.json`
- `analysis/failure_analysis.md`
- `analysis/reflections/reflection_[Tên_SV].md` cho đủ thành viên

Ngoài việc “có file”, em còn kiểm tra tính nhất quán nội dung giữa các file để tránh mâu thuẫn số liệu.

### 2.5. Hỗ trợ phần trình bày demo
Em cùng hệ thống AI hỗ trợ tạo thêm:
- Script demo một lệnh chạy từ đầu đến cuối.
- Biểu đồ so sánh model judge để thuyết trình dễ hiểu hơn.
Mục tiêu là giảm thao tác thủ công khi demo và tăng tính thuyết phục bằng bằng chứng định lượng.

## 3) Kết quả đạt được trong phần việc D14-T05
- Pipeline chạy ổn định end-to-end.
- Bộ artifacts nộp bài đầy đủ theo checklist.
- Quality gate có quyết định rõ ràng, đọc được lý do.
- Check script pass, giảm rủi ro lỗi thủ tục khi chấm.
- Nội dung reflection cá nhân của các thành viên được tập hợp đủ và đồng bộ.

## 4) Khó khăn lớn và cách em xử lý

### Khó khăn 1: Dữ liệu report dễ lệch sau mỗi lần chạy lại
Do benchmark có gọi model và có yếu tố dao động nhẹ, số liệu có thể đổi giữa các lần run. Nếu không chốt theo một lần chạy “chuẩn cuối” thì rất dễ lệch giữa summary và failure analysis.

**Cách em xử lý:**  
Luôn chạy lại full pipeline trước khi chốt, sau đó cập nhật các file phụ thuộc theo đúng snapshot mới nhất.

### Khó khăn 2: Tích hợp công việc nhiều thành viên
Mỗi bạn sửa một phần khác nhau (dataset, retrieval, judge, regression), khi ghép vào rất dễ phát sinh xung đột logic hoặc schema.

**Cách em xử lý:**  
Em ưu tiên kiểm tra interface giữa module (đầu vào/đầu ra), nhất là các field trong report JSON và format cần cho check script.

### Khó khăn 3: Áp lực thời gian trước demo
Giai đoạn cuối thường có nhiều thay đổi dồn dập, dễ phát sinh lỗi “phút 89”.

**Cách em xử lý:**  
Giữ nguyên tắc “chạy thật -> đối chiếu thật -> mới commit/push”, không để quyết định dựa trên cảm giác.

## 5) Bài học rút ra
- Tích hợp hệ thống là nơi lộ lỗi nhiều nhất; module chạy riêng lẻ chưa chắc chạy tốt khi ghép.
- Quality gate cuối là bắt buộc, không thể bỏ qua nếu muốn nộp bài an toàn.
- Tính nhất quán dữ liệu trong báo cáo quan trọng không kém việc code đúng.
- Demo tốt cần “ít thao tác, nhiều bằng chứng”: lệnh chạy rõ, số liệu rõ, kết luận rõ.

## 6) Tự đánh giá mức độ đóng góp
Em đánh giá phần đóng góp của mình tập trung vào:
- Đảm bảo hệ thống đạt trạng thái submission-ready.
- Giảm rủi ro tích hợp và rủi ro thủ tục.
- Chốt đầu ra cuối cùng để nhóm có thể demo và nộp bài tự tin hơn.

Nếu không có vai trò D14-T05, nhóm vẫn có thể có code tốt theo từng phần, nhưng rất dễ mất điểm do lệch artifact, thiếu nhất quán hoặc fail ở bước xác thực cuối.

## 7) Nếu có thêm thời gian, em sẽ làm gì
- Thêm CI pipeline chạy tự động `synthetic_gen -> main -> check_lab` cho mỗi lần merge.
- Tạo schema validation bắt buộc cho các file JSON report.
- Bổ sung dashboard mini cho demo (pass/fail/review theo nhóm case).
- Chuẩn hóa checklist pre-submit thành script duy nhất để giảm sai sót thao tác.
