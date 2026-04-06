# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Phạm Xuân Khang
- **Student ID**: 2A202600275
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

### 1) Commit evidence from git logs

From `.git/logs/refs/heads/khangkk`, key commits include:

- `feat: implement tools for stock checking, discount retrieval, and shipping calculation`
- `Implement SimpleChatbot and ReActAgent with telemetry tracking for usage and latency`
- `Refactor app.py to remove mode selection and streamline chatbot vs ReAct Agent comparison`
- `Enhance ReActAgent and inventory tools with JSON parsing and normalization`

These commits map directly to my two main contribution areas:
- Tooling implementation (tool layer + registry + deterministic behavior)
- Comparative UI/UX and runtime telemetry for Basic Chatbot vs ReAct Agent

### 2) Modules implemented / contributed

- Tool/data layer:
  - `src/tools/data.py`
  - `src/tools/inventory.py`
  - `src/tools/coupons.py`
  - `src/tools/shipping.py`
  - `src/tools/registry.py`
  - `src/tools/__init__.py`
- Agent and baseline integration:
  - `src/agent/chatbot.py`
  - `src/agent/agent.py`
  - `src/agent/parsing.py`
- Demo comparison interface:
  - `app.py`
- Test support and scenario validation:
  - `tests/test_tools.py`
  - `tests/test_agent_scenarios.py`

### 3) Code highlights

- Implemented deterministic tools with parse-friendly `key=value` outputs and explicit error contracts (`error=...`) to support robust ReAct observations.
- Added inventory normalization and validation flow to reduce item-name mismatch in natural user input.
- Integrated telemetry (`usage`, `latency`, `cost_estimate`) in both baseline chatbot and ReAct agent.
- Built a Streamlit comparison interface showing:
  - side-by-side outputs for Basic Chatbot vs ReAct Agent
  - per-system metrics (tokens, latency, steps, estimated cost)
  - ReAct trace expander for debugging/teaching

### 4) How this contribution interacts with the ReAct loop

My tools provide the environment-facing actions in the `Thought -> Action -> Observation` cycle. The ReAct agent consumes deterministic observations to produce grounded final answers, while the UI makes the reasoning quality difference visible versus a tool-less chatbot baseline.

---

## II. Debugging Case Study (10 Points)

### Problem Description

In multiple out-of-domain or underspecified queries, the model returned free-form natural language instead of strict action/final format, causing parser failures and repeated loops until `max_steps_exceeded`.

### Log Source

Observed from `logs/2026-04-06.log`:
- repeated `AGENT_PARSE_ERROR`
- eventual `AGENT_END` with `status=max_steps_exceeded`
- contrast case with successful happy-path final checkout math

### Diagnosis

Root cause was format drift: model outputs did not consistently follow the required schema for parsing. Even with strict prompting, some responses were conversational and lacked machine-parseable `Action`/`Final` structure.

### Solution

- Added stronger parsing support using JSON/Pydantic message schema and compatibility fallback.
- Kept `max_steps` guardrail to prevent infinite loops.
- Added scenario tests for off-topic and fallback behavior to prevent regressions.
- Improved UX by exposing traces and metrics in the Streamlit app for faster RCA in class demos.

Outcome: reliability improved for both valid checkout paths and failure containment (fail-safe behavior with observable telemetry).

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**
   The baseline chatbot is fluent but often speculative. ReAct is stronger for multi-step tasks because it explicitly calls tools and uses real observations before finalizing answers.

2. **Reliability**
   ReAct can perform worse than chatbot in ambiguous/off-domain prompts when output format drifts and parsing becomes brittle. However, with better parser design + guardrails, ReAct remains safer for factual checkout calculations.

3. **Observation impact**
   Observations are the key differentiator. Once stock/discount/shipping observations are fed back into the loop, final responses become auditable and reproducible, not just plausible text.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Execute Basic Chatbot and ReAct agent truly concurrently (async/threaded calls) to improve comparison fairness and demo responsiveness.
- **Safety**: Add an intent gate before the ReAct loop to route off-domain requests directly to a safe final response.
- **Performance**: Separate metric trackers per panel/request and compute provider-specific cost models instead of a single mock formula.
- **Data quality**: Keep deterministic dataset and expected math strictly aligned with Team Plan for instructor reproducibility.

---

> [!NOTE]
> This report emphasizes my strongest contribution areas: **Tool implementation** and **the comparison interface between native chatbot and ReAct agent**, supported by git-log evidence and runtime telemetry traces.
