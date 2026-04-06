# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: [Dien ho ten]
- **Student ID**: [Dien MSSV]
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

Trong Lab 3, vai tro chinh cua toi la **Member 2**: xay dung va on dinh hoa vong lap ReAct trong `src/agent/agent.py`, dam bao agent co the ket thuc an toan va tra ket qua theo dung format.

- **Modules Implemented / Refined**:
  - `src/agent/agent.py`: hoan thien ReAct loop (Thought -> Action -> Observation -> Final Answer).
  - `tests/test_agent_scenarios.py`: bo test tinh huong cho vong lap agent (off-topic, unknown tool, llm error, max steps, parse recovery).
  - Phoi hop voi test-case team plan qua duong dan demo va test tool (`demo_agent.py`, `tests/test_tools.py`).

- **Code Highlights (Member 2 focus)**:
  - Viet lai `get_system_prompt()` theo huong rang buoc chat: moi step chi co 1 Action, khong tu viet Observation, khong tu y bia tool result, bat buoc Final Answer khi du thong tin.
  - Them logic parse va dieu khien trong `run()`:
    - Kiem tra `parse_final()` truoc de dung dung luc.
    - Neu parse loi thi chen `Observation: error=parse_failed...` de model tu sua o step tiep theo.
    - Neu tool khong ton tai hoac chay loi thi tra ve observation loi co cau truc (`error=...`) thay vi crash.
    - Them fallback cuoi cung: `Final Answer: error=max_steps_exceeded...` de tranh loop vo han.
  - Tich hop telemetry event trong loop (`AGENT_START`, `LLM_STEP`, `TOOL_CALL`, `AGENT_PARSE_ERROR`, `AGENT_END`) de phuc vu debug va danh gia.

- **Member 2 Test Cases theo TEAM_PLAN**:
  1. Happy path:
     - Input: `item=iPhone; qty=2; coupon=WINNER; city=Hanoi`
     - Agent goi du 3 tools can thiet (`check_stock`, `get_discount`, `calc_shipping`) va ket thuc voi tong `42539600` VND.
  2. Invalid coupon:
     - Input: `item=iPhone; qty=2; coupon=FREE100; city=Hanoi`
     - He thong phat hien `error=unknown_coupon` o tool layer; agent co the fallback ve 0% hoac yeu cau nguoi dung nhap lai ma hop le.
  3. Out-of-stock / unknown item:
     - Input: `item=MacBook; qty=999; coupon=SAVE10; city=HCMC` (hoac item ngoai catalog).
     - Agent phai thong bao khong du dieu kien xu ly don va ket thuc bang Final Answer than thien.

- **Documentation / ReAct interaction**:
  - Prompt dieu khien hanh vi model.
  - Parsing + dispatch bien output LLM thanh hanh dong co the thi hanh.
  - Tool observation duoc feed nguoc vao prompt de tao step tiep theo co can cu.
  - Ket qua cuoi cung duoc dinh dang theo business fields cua checkout scenario.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**:
  - Agent bi lap parse error voi cau hoi off-topic. Model tra loi apology thuong, khong bat dau bang `Final Answer:` nen parser khong nhan dien duoc diem dung.
  - He qua: agent tiep tuc lap den het `max_steps` va tra `error=max_steps_exceeded`.

- **Log Source**:
  - `logs/2026-04-06.log`
  - Cum su kien that bai:
    - `AGENT_START` input off-topic (ve tin tuc chien su).
    - Nhieu lan `AGENT_PARSE_ERROR` lien tiep (step 1 -> step 5).
    - Ket thuc bang `AGENT_END` voi `status=max_steps_exceeded`.
  - Cu the trong log co 2 pha:
    - Pha truoc khi prompt du chat: run bi parse error lien tuc den step 5.
    - Pha sau khi prompt duoc tighten: cung input off-topic, model tra ngay `Final Answer: ...` va `AGENT_END` thanh cong o step 1.

- **Diagnosis**:
  - Nguyen nhan goc la khe ho trong system prompt: da co noi "off-topic thi tu choi", nhung chua ep chat dau ra phai bat dau bang `Final Answer:` cho truong hop tu choi.
  - Parser trong agent la parser theo protocol (`Action:` hoac `Final Answer:`), vi vay neu model "noi chuyen tu do" thi se gay parse miss.

- **Solution**:
  - Cap nhat `get_system_prompt()` trong `src/agent/agent.py`:
    - Them rule off-topic: "immediately refuse by starting with Final Answer".
    - Nhan manh format Action/Final va cam markdown fence.
  - Giu co che an toan trong `run()`:
    - Parse error -> Observation loi co cau truc de model tu chinh.
    - Co max_steps fallback de chan loop vo han.
  - Bo sung test scenario de khoa hanh vi:
    - `test_unrelated_topic_returns_final_answer_without_stuck`
    - `test_exceed_max_steps_returns_fallback_not_stuck`
    - `test_parse_failure_then_recover_with_final_answer`

- **Outcome**:
  - Failure mode "off-topic -> parse loop" duoc giam ro ret.
  - Agent dat hanh vi quy uoc protocol on dinh hon, de telemetry de phan tich va de cham diem phan Trace Quality.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**:
   - Chatbot thuong tra loi mot lan theo "tri nho tham so" de bi sai trong bai toan nhieu buoc.
   - ReAct agent buoc model chia nho bai toan: lay stock/price -> lay discount -> tinh shipping -> tong hop final. Moi buoc co Observation xac thuc, nen tinh "grounded" cao hon.

2. **Reliability (khi nao agent te hon chatbot)**:
   - Agent co the te hon o cau hoi don gian/off-topic neu protocol parse qua nghiem va prompt chua chat, dan den parse retry va tang do tre.
   - Chatbot thuong "tra loi ngay" nen nhanh hon o tac vu Q&A don gian khong can tool.

3. **Observation feedback**:
   - Observation la "chan ly moi truong" de chong hallucination.
   - Vi du, khi tool tra `error=unknown_item`, agent co the ket thuc an toan thay vi tiep tuc doan gia/phi ship.
   - Day la diem khac biet cot loi giua "noi" (chatbot) va "hanh dong co chung cu" (agent).

---

## IV. Future Improvements (5 Points)

- **Scalability**:
  - Tach tac vu thanh 2 lop model: model nho de classify intent va route tool; model lon de tong hop final answer.
  - Chuyen tool calls sang co che async va queue (nhat la khi so tool tang).

- **Safety**:
  - Them schema validator truoc khi goi tool (JSON schema/Pydantic cho Action payload) de chong sai dinh dang.
  - Them policy guard truoc va sau loop (input guard + output guard) de chan off-domain request va response lech protocol.

- **Performance / Production path**:
  - Cache observation cho cac truy van lap lai (gia, coupon, phi ship).
  - Them bo telemetry tong hop P50/P95 latency, token/tool-call ratio, cost theo test suite.
  - Huong mo rong den production-level RAG/multi-agent:
    - Mot planner agent lap ke hoach call tool.
    - Mot executor agent chay tool.
    - Mot verifier agent kiem tra consistency truoc khi tra Final Answer.

---

> [!NOTE]
> De nop bai theo guideline lop hoc, doi ten file thanh `REPORT_[YOUR_NAME].md` truoc khi submit.