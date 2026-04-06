# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Thị Ngọc Thư
- **Student ID**: 2A202600210
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase.*

- **Modules Implemented**: ReAct loop (while-loop reasoning logic)
- **Code Highlights**:
	- Tôi đã sửa lại vòng lặp ReAct để đảm bảo agent có thể lặp qua nhiều bước `Thought -> Action -> Observation`.
	- Agent không dừng sớm khi chưa đạt `Final Answer`.
	- Điều kiện dừng được kiểm soát hợp lý để hỗ trợ multi-step reasoning.
- **Documentation**:
	- ReAct loop đóng vai trò trung tâm của agent, điều phối toàn bộ quá trình reasoning.
	- Sau khi sửa, luồng hoạt động là:
		1. Sinh `Thought`
		2. Chọn `Action`
		3. Gọi tool
		4. Nhận `Observation`
		5. Lặp lại đến khi có `Final Answer`
	- Việc sửa loop giúp agent thực hiện multi-step reasoning đúng theo thiết kế của ReAct.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event encountered during the lab.*

- **Problem Description**: Agent chỉ thực hiện bước đầu tiên và không tiếp tục các bước tiếp theo để đưa ra `Final Answer`.
- **Log Source**: Log hệ thống cho thấy agent dừng sau step 1, không tiếp tục vòng lặp.
- **Diagnosis**:
	- Tool đọc sai dữ liệu.
	- Format trả về không đúng như mong đợi của agent.
	- Agent không hiểu `Observation`, dẫn đến không thể sinh `Thought` tiếp theo.
- **Solution**:
	- Sửa lại format dữ liệu trả về từ tool.
	- Đảm bảo output của tool phù hợp với prompt expectation.
	- Kết hợp với việc sửa ReAct loop để agent tiếp tục chạy đến khi có `Final Answer`.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: ReAct Agent khác Chatbot ở chỗ có thêm bước `Thought`, giúp mô hình suy nghĩ từng bước thay vì trả lời trực tiếp. Điều này cải thiện reasoning và khả năng xử lý bài toán nhiều bước.
2. **Reliability**: ReAct Agent có thể hoạt động kém hơn Chatbot khi tool lỗi hoặc trả dữ liệu sai, và khi format không đúng khiến agent không hiểu `Observation`.
3. **Observation**: `Observation` là feedback quan trọng từ môi trường. Agent dựa vào thông tin này để quyết định bước tiếp theo, nên nếu dữ liệu sai hoặc không rõ ràng thì toàn bộ reasoning bị ảnh hưởng.

- **Overall Insight**:
	- So với Chatbot, ReAct có khả năng gọi dữ liệu từ nguồn bên ngoài.
	- ReAct có thể tương tác với các bước trước đó.
	- ReAct giúp tăng độ chính xác và giảm hallucination.

---

## IV. Future Improvements (5 Points)

*How to scale this system toward production-level AI agent operation.*

- **Scalability**: Tích hợp thêm nhiều tools và tối ưu hóa pipeline xử lý.
- **Safety**: Thêm các safety guard để kiểm soát hành vi agent, tránh gọi tool sai hoặc sinh output không mong muốn.
- **Performance**:
	- Sử dụng Vector Database để truy xuất thông tin nhanh hơn.
	- Hỗ trợ agent trong tìm kiếm ngữ cảnh và dữ liệu liên quan.

---