# Báo cáo cá nhân: Lab 3 - Chatbot vs ReAct Agent

- **Họ và tên**: [Phạm Thành Duy]
- **MSSV**: [2A202600267]
- **Ngày**: 2026-04-06

---

## I. Đóng góp kỹ thuật (15 điểm)

Trong Lab 3, vai trò chính của tôi là **Member 2**: xây dựng và ổn định hóa vòng lặp ReAct trong `src/agent/agent.py`, đảm bảo agent có thể kết thúc an toàn và trả kết quả đúng format.

- **Module đã triển khai / tinh chỉnh**:
  - `src/agent/agent.py`: hoàn thiện ReAct loop (Thought -> Action -> Observation -> Final Answer).
  - `tests/test_agent_scenarios.py`: bổ sung test tình huống cho vòng lặp agent (off-topic, unknown tool, llm error, max steps, parse recovery).
  - Phối hợp với test-case theo team plan qua đường dẫn demo và test tool (`demo_agent.py`, `tests/test_tools.py`).

- **Điểm nhấn kỹ thuật (trọng tâm Member 2)**:
  - Viết lại `get_system_prompt()` theo hướng ràng buộc chặt: mỗi step chỉ có 1 Action, không tự viết Observation, không tự ý bịa tool result, bắt buộc Final Answer khi đủ thông tin.
  - Thêm logic parse và điều khiển trong `run()`:
    - Kiểm tra `parse_final()` trước để dừng đúng lúc.
    - Nếu parse lỗi thì chèn `Observation: error=parse_failed...` để model tự sửa ở step tiếp theo.
    - Nếu tool không tồn tại hoặc chạy lỗi thì trả về observation lỗi có cấu trúc (`error=...`) thay vì crash.
    - Thêm fallback cuối cùng: `Final Answer: error=max_steps_exceeded...` để tránh loop vô hạn.
  - Tích hợp telemetry event trong loop (`AGENT_START`, `LLM_STEP`, `TOOL_CALL`, `AGENT_PARSE_ERROR`, `AGENT_END`) để phục vụ debug và đánh giá.

- **Test case của Member 2 theo TEAM_PLAN**:
  1. Happy path:
     - Input: `item=iPhone; qty=2; coupon=WINNER; city=Hanoi`
     - Agent gọi đủ 3 tools cần thiết (`check_stock`, `get_discount`, `calc_shipping`) và kết thúc với tổng `42539600` VND.
  2. Invalid coupon:
     - Input: `item=iPhone; qty=2; coupon=FREE100; city=Hanoi`
     - Hệ thống phát hiện `error=unknown_coupon` ở tool layer; agent có thể fallback về 0% hoặc yêu cầu người dùng nhập lại mã hợp lệ.
  3. Out-of-stock / unknown item:
     - Input: `item=MacBook; qty=999; coupon=SAVE10; city=HCMC` (hoặc item ngoài catalog).
     - Agent phải thông báo không đủ điều kiện xử lý đơn và kết thúc bằng Final Answer thân thiện.

- **Mô tả tương tác trong ReAct loop**:
  - Prompt điều khiển hành vi model.
  - Parsing + dispatch biến output LLM thành hành động có thể thi hành.
  - Tool observation được feed ngược vào prompt để tạo step tiếp theo có căn cứ.
  - Kết quả cuối cùng được định dạng theo business fields của checkout scenario.

---

## II. Case Study gỡ lỗi (10 điểm)

- **Mô tả vấn đề**:
  - Agent bị lặp parse error với câu hỏi off-topic. Model trả lời apology thường, không bắt đầu bằng `Final Answer:` nên parser không nhận diện được điểm dừng.
  - Hệ quả: agent tiếp tục lặp đến hết `max_steps` và trả `error=max_steps_exceeded`.

- **Nguồn log**:
  - `logs/2026-04-06.log`
  - Cụm sự kiện thất bại:
    - `AGENT_START` input off-topic (về tin tức chiến sự).
    - Nhiều lần `AGENT_PARSE_ERROR` liên tiếp (step 1 -> step 5).
    - Kết thúc bằng `AGENT_END` với `status=max_steps_exceeded`.
  - Cụ thể trong log có 2 pha:
    - Pha trước khi prompt đủ chặt: run bị parse error liên tục đến step 5.
    - Pha sau khi prompt được tighten: cùng input off-topic, model trả ngay `Final Answer: ...` và `AGENT_END` thành công ở step 1.

- **Chẩn đoán nguyên nhân**:
  - Nguyên nhân gốc là khe hở trong system prompt: đã có nói "off-topic thì từ chối", nhưng chưa ép chặt đầu ra phải bắt đầu bằng `Final Answer:` cho trường hợp từ chối.
  - Parser trong agent là parser theo protocol (`Action:` hoặc `Final Answer:`), vì vậy nếu model "nói chuyện tự do" thì sẽ gây parse miss.

- **Giải pháp**:
  - Cập nhật `get_system_prompt()` trong `src/agent/agent.py`:
    - Thêm rule off-topic: "immediately refuse by starting with Final Answer".
    - Nhấn mạnh format Action/Final và cấm markdown fence.
  - Giữ cơ chế an toàn trong `run()`:
    - Parse error -> Observation lỗi có cấu trúc để model tự chỉnh.
    - Có max_steps fallback để chặn loop vô hạn.
  - Bổ sung test scenario để khóa hành vi:
    - `test_unrelated_topic_returns_final_answer_without_stuck`
    - `test_exceed_max_steps_returns_fallback_not_stuck`
    - `test_parse_failure_then_recover_with_final_answer`

- **Kết quả sau khi sửa**:
  - Failure mode "off-topic -> parse loop" được giảm rõ rệt.
  - Agent đạt hành vi quy ước protocol ổn định hơn, dễ telemetry để phân tích và dễ chấm điểm phần Trace Quality.

---

## III. Góc nhìn cá nhân: Chatbot vs ReAct (10 điểm)

1. **Reasoning**:
  - Chatbot thường trả lời một lần theo "trí nhớ tham số" nên dễ sai trong bài toán nhiều bước.
  - ReAct agent buộc model chia nhỏ bài toán: lấy stock/price -> lấy discount -> tính shipping -> tổng hợp final. Mỗi bước có Observation xác thực, nên tính "grounded" cao hơn.

2. **Reliability (khi nào agent tệ hơn chatbot)**:
  - Agent có thể tệ hơn ở câu hỏi đơn giản/off-topic nếu protocol parse quá nghiêm và prompt chưa chặt, dẫn đến parse retry và tăng độ trễ.
  - Chatbot thường "trả lời ngay" nên nhanh hơn ở tác vụ Q&A đơn giản không cần tool.

3. **Observation feedback**:
  - Observation là "chân lý môi trường" để chống hallucination.
  - Ví dụ, khi tool trả `error=unknown_item`, agent có thể kết thúc an toàn thay vì tiếp tục đoán giá/phí ship.
  - Đây là điểm khác biệt cốt lõi giữa "nói" (chatbot) và "hành động có chứng cứ" (agent).

---

## IV. Hướng cải tiến tương lai (5 điểm)

- **Scalability**:
  - Tách tác vụ thành 2 lớp model: model nhỏ để classify intent và route tool; model lớn để tổng hợp final answer.
  - Chuyển tool calls sang cơ chế async và queue (nhất là khi số tool tăng).

- **Safety**:
  - Thêm schema validator trước khi gọi tool (JSON schema/Pydantic cho Action payload) để chống sai định dạng.
  - Thêm policy guard trước và sau loop (input guard + output guard) để chặn off-domain request và response lệch protocol.

- **Performance / Production path**:
  - Cache observation cho các truy vấn lặp lại (giá, coupon, phí ship).
  - Thêm bộ telemetry tổng hợp P50/P95 latency, token/tool-call ratio, cost theo test suite.
  - Hướng mở rộng đến production-level RAG/multi-agent:
    - Một planner agent lập kế hoạch call tool.
    - Một executor agent chạy tool.
    - Một verifier agent kiểm tra consistency trước khi trả Final Answer.

---

> [!NOTE]
> File hiện tại đã đúng format nộp bài: `REPORT_Pham_Thanh_Duy.md`.