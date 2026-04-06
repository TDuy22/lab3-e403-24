# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Văn Thức
- **Student ID**: 2A202600238
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**:
  - `src/agent/parsing.py` (commit `636d50c`: Add parsing for llm)
  - `src/tools/data.py` (commit `e2d33c9`: Add data done)
  - `src/telemetry/logger.py` + small integration update in `app.py` (commit `8833d94`: Edit logger)
  - `.gitignore` (commits `636d50c`, `4efb656`: add ignore entries related to parsing output/artifacts)
- **Code Highlights**:
  - **Robust JSON extraction for LLM outputs**: I added `_extract_first_json_object()` to safely parse the *first* JSON object even when the model prints extra text before or after. This reduces format drift causing parsing failures in ReAct runs.
  - **Typed action or final schemas with Pydantic**: `ActionMessage`/`FinalMessage` + `TypeAdapter` enforce a strict message contract, and `parse_action()`/`parse_final()` act as compatibility wrappers for the agent loop.
  - **Centralized structured logging path**: `IndustryLogger` resolves `LOG_DIR` to an absolute path under the repo root to prevent logs written to a random cwd when running from Streamlit with CLI.
  - **Dataset contribution**: updated and added catalog and coupon or shipping constants in `src/tools/data.py` to support tool calls with consistent inventory metadata (price, stock, weight).
- **Documentation**:
  - In the ReAct loop, the agent must reliably convert LLM outputs into either an **Action** (tool call) or a **Final** answer. My work in `src/agent/parsing.py` focuses on making that conversion robust by:
    - extracting valid JSON even with extra text,
    - validating the message type (`action` vs `final`),
    - converting tool arguments into the correct positional parameter list via `parse_args_for_tool()`.
  - My work in `src/telemetry/logger.py` ensures every step, tool-call is logged as a JSON-line event, enabling debugging of failures across steps (LLM output → parse → tool call → observation → next step).

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: The agent got stuck because it **could not parse the LLM output** (the LLM returned only a `Thought` line or free-form natural language), which caused repeated steps and eventually ended with `max_steps_exceeded`.
- **Log Source**: Extracted from `logs/2026-04-06.log` (events):
  - `AGENT_PARSE_ERROR` where the response contains only `"Thought: still thinking..."` (step 1/2/3)
  - `AGENT_END` with `status=max_steps_exceeded` after exceeding the step limit
  - There is also a case `error=unknown_tool` when the model calls `weather_lookup` (the tool does not exist)
- **Diagnosis**:
  - **Format drift**: The LLM output did not follow the schema expected by the agent (Action/Final). When parsing fails, the agent cannot execute a tool call, so it keeps querying the LLM in the next step and can loop.
  - **Tool mismatch**: For out-of-domain queries (e.g., weather), the model “hallucinated” the `weather_lookup` tool, and the system recorded `error=unknown_tool`.
- **Solution**:
  - Increased robustness in the parsing layer by:
    - extracting the **first JSON object** (if any) from mixed text output,
    - validating the schema with Pydantic (`ActionMessage`/`FinalMessage`) and returning `None` when invalid so the system can log the failure clearly.
  - Improved logging to make RCA faster:
    - ensured the log file is always written inside the repo’s `logs/` directory (avoiding cwd-dependent paths).
  - Kept the `max_steps` guardrail to prevent infinite loops and fail safely when the model does not follow the required format.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: With ReAct, the `Thought` block helps the model plan more explicitly (need stock/price → need discount → need shipping), which leads to a more coherent sequence of `Action`s. A plain chatbot tends to answer directly, so it can be generic or miss key numbers if it lacks tools/observations.
2.  **Reliability**: The agent can perform *worse* than the chatbot when:
    - the output **drifts from the expected format** (cannot be parsed), causing cascading failures (retries/loops, `max_steps_exceeded`);
    - the query is **out of domain**, leading the model to call a non-existent tool (`unknown_tool`);
    - the tool expects an exact item name; if the user provides a near-match, it may return `unknown_item`, degrading UX without good normalization.
3.  **Observation**: Observations are “environment feedback” that ground the agent in real data (e.g., `unit_price_vnd`, `in_stock`, `weight_kg_per_unit`, `shipping_fee_vnd`). When observations contain errors (`unknown_tool`, `unknown_item`), the agent should change strategy (ask for clarification/suggest valid items) or fail safely instead of fabricating numbers.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Standardize the message contract (JSON schema) across providers and add retry/backoff around LLM/tool-call steps; split the parse/tool/observe pipeline into independent modules so adding many tools is straightforward.
- **Safety**: Add an intent router and domain-based tool allowlist to prevent tool hallucination (e.g., calling `weather_lookup`); define a policy for parse failures (fallback to a safe final response instead of looping).
- **Performance**: Cache tool results (for example catalog/coupon lookup) and optimize prompts (fewer tokens, only include necessary tool schemas); if the tool set becomes large, use retrieval to select relevant tools instead of listing all tool descriptions every run.

---
