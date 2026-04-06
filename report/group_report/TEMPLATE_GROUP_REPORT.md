# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: E403-Team24
- **Team Members**: 2A202600238_Nguyễn_Văn_Thức, 2A202600275_Phạm_Xuân_Khang, 2A202600267_Phạm_Thành_Duy, 2A202600210-Nguyễn_Thị_Ngọc_Thư
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

This repository implements a **Smart Checkout ReAct agent** that answers shopping or checkout queries by grounding calculations in deterministic tools (stock/price, coupon discount, shipping fee), and compares it side-by-side with a baseline chatbot that answers directly without tools.

- **Success Rate**: Agent **60/61 = 98.34%** vs Chatbot **44/49 = 89.79%** (computed from `logs/2026-04-06.log` end events: `AGENT_END` / `CHATBOT_END` with `status=success`).  
  Note: in this repo, chatbot “success” means “returned a response”, not correctness (it has no tools/data to reliably compute totals).
- **Key Outcome**: The agent reliably solves multi-step checkout math by calling **`check_stock` → `get_discount` → `calc_shipping`** and assembling a grounded final answer (example trace in `logs/2026-04-06.log` for `item=iPhone; qty=2; coupon=WINNER; city=Hanoi`).

---

## 2. System Architecture and Tooling
<img src="https://res.cloudinary.com/dczdnu2ba/image/upload/v1775488444/Screenshot_2026-04-06_180052_hkvitn.png" alt="System Architecture" width="400">
### 2.1 ReAct Loop Implementation
Implemented in `src/agent/agent.py` as a bounded loop (`max_steps`) that:

- Calls the provider via `llm.generate(prompt, system_prompt=...)`
- Parses the model output into either:
  - **v2 structured JSON message** (Pydantic schema) using `src/agent/parsing.py` (`parse_message`)
  - **v1 regex fallback** for legacy `Action:` / `Final Answer:` text
- Executes tools from `TOOLS` and appends `Observation: ...` to the prompt
- Terminates on `Final Answer:` (or `{ "type": "final", ... }`) or fails safely on `max_steps`

Telemetry is emitted at each stage (`AGENT_START`, `LLM_STEP`, `TOOL_CALL`, `AGENT_END`) to `logs/*.log` via `src/telemetry/logger.py`.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `check_stock` | `check_stock(item_name: str)` | Retrieve deterministic stock, unit price (VND), and weight per unit for a product (`src/tools/inventory.py`). |
| `get_discount` | `get_discount(coupon_code: str)` | Retrieve discount percent for a coupon code (`src/tools/coupons.py`). |
| `calc_shipping` | `calc_shipping(weight_kg: float, destination: str)` | Compute shipping fee (VND) from weight and destination city (`src/tools/shipping.py`). |

### 2.3 LLM Providers Used
- **Primary**: OpenAI (`src/core/openai_provider.py`) — default model `gpt-4o` (also shown in `logs/2026-04-06.log`).
- **Secondary (Backup)**: Google Gemini (`src/core/gemini_provider.py`) — default `gemini-1.5-flash` (selectable via `DEFAULT_PROVIDER` / Streamlit UI in `app.py`).

---

## 3. Telemetry and Performance Dashboard

Metrics below are computed from `logs/2026-04-06.log` over `LLM_METRIC` events (emitted by `src/telemetry/metrics.py`).  
Important: `cost_estimate` is a **mock** calculation in code: \( \text{cost} = \frac{\text{total\_tokens}}{1000} \times 0.01 \).

- **Average Latency (P50)**: **1271ms** (per-request latency percentile on `LLM_METRIC.latency_ms`, \(n=179\)).
- **Max Latency (P99)**: **~5175ms** (P99 on `LLM_METRIC.latency_ms`).
- **Average Tokens per Task**: **Agent ~1253.29 tokens/task** (sum of `LLM_METRIC.total_tokens` per `AGENT_START..AGENT_END`, averaged over 55 completed agent tasks in the log).
- **Total Cost of Test Suite**: **$0.78049** (sum of `LLM_METRIC.cost_estimate` across all logged requests in `logs/2026-04-06.log`).

---

## 4. Root Cause Analysis (RCA) - Failure Traces

*Deep dive into why the agent failed.*

### Case Study: Max Steps Exceeded (Non-compliant Model Output)
- **Input**: `item=iPhone; qty=1; coupon=NONE; city=Hanoi` (tested via `tests/test_agent_scenarios.py` with a deterministic `ScriptedLLM`)
- **Observation**: The model repeatedly produced non-action content (e.g., `Thought: still thinking...`), which the agent could not parse into a tool call or final answer; the loop terminated with `error=max_steps_exceeded`.
- **Root Cause**: The agent is intentionally strict about requiring either a tool call or a final answer each step. When the model violates the expected output contract, the agent logs `AGENT_PARSE_ERROR` and continues until `max_steps` is reached.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2
- **Diff**: Introduced a stricter JSON-based messaging contract in `ReActAgent.get_system_prompt()` (action vs final), and added a **v2 Pydantic parser** (`src/agent/parsing.py`) with robust first-JSON extraction; kept regex parsing as a fallback for backward compatibility.
- **Result**: Improved robustness when models include extra lines around the JSON object, while preserving compatibility with text-format `Action:` traces (both paths exist in `src/agent/agent.py` and are covered by scenario tests in `tests/test_agent_scenarios.py`).

### Experiment 2 (Bonus): Chatbot vs Agent
| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Simple Q (general product price) | Responds generically (no deterministic grounding) | May answer, but often requests checkout-form inputs | Draw |
| Multi-step checkout total | Cannot compute deterministically (no tools) | Calls tools and computes grounded totals (e.g., iPhone qty + coupon + shipping) | **Agent** |

---

## 6. Production Readiness Review

*Considerations for taking this system to a real-world environment.*

- **Security**: Secrets are expected via environment variables (`.env.example`), and provider keys are loaded from env (`app.py`, `demo_agent.py`). Tool inputs are normalized/validated (e.g., Pydantic normalization in `src/tools/inventory.py`; schema validation in `src/agent/parsing.py`).
- **Guardrails**: Bounded loop via `max_steps` with safe fallback (`error=max_steps_exceeded`) and strict tool whitelist (tools only from `src/tools/registry.py` and JSON schema `Literal[...]` in `src/agent/parsing.py`).
- **Scaling**: Observability already exists (structured JSON logs and per-request metrics). For more complex workflows, the current loop can be extended to support branching policies and richer evaluation using the same telemetry foundation (`src/telemetry/logger.py`, `src/telemetry/metrics.py`).

---

