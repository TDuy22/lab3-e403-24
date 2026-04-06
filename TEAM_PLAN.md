## Lab 3 Demo Plan: Smart Checkout ReAct Agent (3 hours, 4 members)

This plan is for a simple ReAct agent that answers:

**User input (demo format)**  
`item=<name>; qty=<int>; coupon=<code|none>; city=<city>`

**Agent output (Final Answer must include)**
- item, qty
- unit_price_vnd, subtotal_vnd
- discount_percent, discount_amount_vnd, discounted_subtotal_vnd
- shipping_fee_vnd
- total_vnd
- stock check result (enough / not enough)

---

## Shared Rules (everyone must follow)

### 1) Tool calling format (for the LLM)
The agent uses this exact ReAct loop:
- `Thought: ...`
- `Action: tool_name(args)`
- `Observation: ...`
- `Final Answer: ...`

### 2) Tool output format (parse-friendly)
All tools should return a single-line string of **key=value** pairs, separated by comma+space.

Good example:  
`item=iPhone, in_stock=50, unit_price_vnd=25000000, weight_kg_per_unit=0.24`

Avoid free-form paragraphs or JSON.

### 3) Demo scenario + deterministic data
Currency: VND  
Shipping formula: `shipping_fee_vnd = 30000 + weight_kg * 20000`  
Allowed cities: Hanoi, HCMC, Da Nang (case-insensitive)

Catalog (case-insensitive keys):
- iPhone: price 25,000,000; stock 50; weight 0.24 kg
- MacBook: price 35,000,000; stock 10; weight 1.2 kg

Coupons:
- WINNER: 15%
- SAVE10: 10%

Expected happy-path math (for teacher):  
Input: `item=iPhone; qty=2; coupon=WINNER; city=Hanoi`
- subtotal = 2 * 25,000,000 = 50,000,000
- discounted_subtotal = 50,000,000 * (1 - 0.15) = 42,500,000
- weight = 2 * 0.24 = 0.48 kg
- shipping = 30,000 + 0.48 * 20,000 = 39,600
- total = 42,539,600 VND

---

## Member Assignments (parallel)

## Member 1 — Tools + Fixed Data (Owner: `src/tools/`)

### Goal
Implement deterministic tools and a `TOOLS` registry so the agent can call them.

### Inputs (what you start from)
- The shared user input format: `item=...; qty=...; coupon=...; city=...`
- The deterministic scenario + data above
- Tool calling format: `Action: tool_name(args)`

### Outputs (what you must deliver)
- `src/tools/data.py`
- `src/tools/inventory.py` (implements `check_stock`)
- `src/tools/coupons.py` (implements `get_discount`)
- `src/tools/shipping.py` (implements `calc_shipping`)
- `src/tools/registry.py` (exports `TOOLS`)
- `src/tools/__init__.py` (re-export `TOOLS`)

### Definition of Done
- Each tool returns a single line of parse-friendly `key=value` pairs.
- Unknown inputs return a single line starting with `error=...`.
- `from src.tools import TOOLS` works from repo root (e.g. `python -m ...`).

### Step-by-step instructions + code

#### Step 1: Create fixed data (`src/tools/data.py`)

```python
CATALOG = {
    "iphone": {
        "display_name": "iPhone",
        "unit_price_vnd": 25_000_000,
        "stock": 50,
        "weight_kg_per_unit": 0.24,
    },
    "macbook": {
        "display_name": "MacBook",
        "unit_price_vnd": 35_000_000,
        "stock": 10,
        "weight_kg_per_unit": 1.2,
    },
}

COUPONS = {"WINNER": 15, "SAVE10": 10}

SHIPPING_BASE_VND = 30_000
SHIPPING_PER_KG_VND = 20_000
ALLOWED_CITIES = {"hanoi", "hcmc", "da nang"}
```

#### Step 2: Implement `check_stock` (`src/tools/inventory.py`)

```python
from src.tools.data import CATALOG


def check_stock(item_name: str) -> str:
    key = item_name.strip().lower()
    if key not in CATALOG:
        known = "|".join(v["display_name"] for v in CATALOG.values())
        return f"error=unknown_item, item_name={item_name.strip()}, known_items={known}"

    row = CATALOG[key]
    return (
        f"item={row['display_name']}, in_stock={row['stock']}, "
        f"unit_price_vnd={row['unit_price_vnd']}, weight_kg_per_unit={row['weight_kg_per_unit']}"
    )
```

#### Step 3: Implement `get_discount` (`src/tools/coupons.py`)

```python
from src.tools.data import COUPONS


def get_discount(coupon_code: str) -> str:
    code = coupon_code.strip().upper()
    if code in {"", "NONE"}:
        return "coupon=NONE, discount_percent=0"
    if code not in COUPONS:
        valid = "|".join(sorted(COUPONS.keys()))
        return f"error=unknown_coupon, coupon={code}, valid={valid}"
    return f"coupon={code}, discount_percent={COUPONS[code]}"
```

#### Step 4: Implement `calc_shipping` (`src/tools/shipping.py`)

```python
from src.tools.data import ALLOWED_CITIES, SHIPPING_BASE_VND, SHIPPING_PER_KG_VND


def calc_shipping(weight_kg: float, destination: str) -> str:
    dest = destination.strip().lower()
    if dest not in ALLOWED_CITIES:
        return f"error=unknown_destination, destination={destination.strip()}, allowed=Hanoi|HCMC|Da Nang"
    if weight_kg < 0:
        return "error=invalid_weight, message=weight_kg_must_be_non_negative"

    fee = SHIPPING_BASE_VND + (weight_kg * SHIPPING_PER_KG_VND)
    return f"destination={destination.strip()}, weight_kg={weight_kg}, shipping_fee_vnd={int(fee)}"
```

#### Step 5: Create the registry (`src/tools/registry.py`)

```python
from src.tools.inventory import check_stock
from src.tools.coupons import get_discount
from src.tools.shipping import calc_shipping

TOOLS = [
    {
        "name": "check_stock",
        "description": (
            "Get stock, unit price (VND), and weight per unit for an item. "
            "Input: item_name (string). Example: check_stock('iPhone'). "
            "Output keys: item, in_stock, unit_price_vnd, weight_kg_per_unit. "
            "If unknown: returns error=unknown_item."
        ),
        "func": check_stock,
    },
    {
        "name": "get_discount",
        "description": (
            "Get discount percent for a coupon code. "
            "Input: coupon_code (string). Example: get_discount('WINNER') or get_discount('NONE'). "
            "Output keys: coupon, discount_percent. If invalid: error=unknown_coupon."
        ),
        "func": get_discount,
    },
    {
        "name": "calc_shipping",
        "description": (
            "Compute shipping fee (VND) using total weight in kg and destination city. "
            "Input: weight_kg (float), destination (string). Example: calc_shipping(0.48, 'Hanoi'). "
            "Allowed destinations: Hanoi, HCMC, Da Nang. Output keys: shipping_fee_vnd."
        ),
        "func": calc_shipping,
    },
]
```

#### Step 6: Re-export from `src/tools/__init__.py`

```python
from src.tools.registry import TOOLS

__all__ = ["TOOLS"]
```

---

## Member 2 — Agent Loop + System Prompt (Owner: `src/agent/agent.py`)

### Goal
Implement the core ReAct loop: LLM → Action → Tool → Observation → repeat → Final Answer.

### Inputs (what you start from)
- `src/agent/agent.py` skeleton
- `TOOLS` registry from Member 1
- Provider classes in `src/core/*_provider.py` implementing `LLMProvider`

### Outputs (what you must deliver)
- A strict `get_system_prompt()` that forces consistent formatting
- A working `run()` loop that terminates on `Final Answer:`
- Tool execution integrated via `tool['func']`

### Definition of Done
- For input `item=iPhone; qty=2; coupon=WINNER; city=Hanoi`, the agent solves in <= 3 tool calls.
- The agent always returns a `Final Answer:` within `max_steps`.

### Step-by-step instructions (what to implement)

#### Step 1: Tighten the system prompt
In `get_system_prompt()`, add rules like:
- output exactly one Action line when tools are needed
- never fabricate tool results
- never wrap outputs in markdown fences

Example rules (paste into prompt text):

```text
Rules:
- If you need a tool, output exactly:
  Thought: ...
  Action: tool_name(arguments)
- Do NOT write Observation yourself.
- Use only the tools listed (no new tool names).
- When you have enough information, output:
  Final Answer: ...
```

#### Step 2: Implement the loop in `run()`
Algorithm:
1. `prompt = user_input`
2. Call LLM: `llm.generate(prompt, system_prompt=...)`
3. If response contains `Final Answer:` → return it
4. Else parse `Action:` → tool name + args
5. Execute tool → `observation`
6. Append `\nObservation: {observation}\n` to prompt and repeat
7. Stop at `max_steps` with a safe fallback

Implementation note:
- Member 3 provides `parse_action(...)` and `parse_final(...)`.

---

## Member 3 — Parsing + Dispatch Robustness (Supports Member 2)

### Goal
Make parsing and tool invocation reliable, even if LLM output contains extra lines/whitespace.

### Inputs (what you start from)
- Sample LLM outputs from your provider
- Tool calling convention (only support 3 tools for demo)

### Outputs (what you must deliver)
- `parse_action(text) -> (tool_name, raw_args) | None`
- `parse_final(text) -> final_answer | None`
- `parse_args_for_tool(tool_name, raw_args) -> list`
- A recommended `_execute_tool()` approach using `TOOLS`

### Definition of Done
- Your parser extracts Action even with extra spaces/newlines.
- Your arg parsing handles:
  - `check_stock("iPhone")`
  - `get_discount("WINNER")`
  - `calc_shipping(0.48, "Hanoi")`

### Code examples (Member 2 can paste)

```python
import re

ACTION_RE = re.compile(r"^Action:\s*([a-zA-Z_]\w*)\s*\((.*)\)\s*$", re.MULTILINE)
FINAL_RE = re.compile(r"Final Answer:\s*(.*)", re.DOTALL)


def parse_action(text: str):
    m = ACTION_RE.search(text)
    if not m:
        return None
    return m.group(1), m.group(2)


def parse_final(text: str):
    m = FINAL_RE.search(text)
    return m.group(1).strip() if m else None


def parse_args_for_tool(tool_name: str, raw: str):
    raw = raw.strip()
    if tool_name in {"check_stock", "get_discount"}:
        return [raw.strip().strip('"').strip("'")]
    if tool_name == "calc_shipping":
        parts = [p.strip() for p in raw.split(",")]
        weight = float(parts[0])
        dest = parts[1].strip().strip('"').strip("'")
        return [weight, dest]
    return []
```

Dispatch recommendation:
- In `_execute_tool`, find `tool = next(t for t in tools if t["name"] == tool_name)`
- Call `tool["func"](*args)`

---

## Member 4 — Demo Runner + Prompts + “Teacher Story”

### Goal
Provide a one-command demo that is stable and easy to present live.

### Inputs (what you start from)
- Working tools (Member 1)
- Working agent (Members 2–3)
- `.env` configured provider (OpenAI/Gemini/Local)

### Outputs (what you must deliver)
- `demo_agent.py` (recommended at repo root) or `tests/test_agent_demo.py`
- 3–5 copy/paste demo inputs + expected behaviors
- 2–3 minute talk track

### Definition of Done
- One command runs the demo reliably on the teacher’s machine.
- Demo includes 1 success + 2 failure cases.

### Step-by-step instructions + code

#### Step 1: Create a runner script
Start from this pattern and adapt provider choice to your `.env`:

```python
import os
import sys
from dotenv import load_dotenv

# Ensure project root on sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.tools import TOOLS
from src.agent.agent import ReActAgent

# Choose provider that matches your .env (example below)
from src.core.openai_provider import OpenAIProvider


def main():
    load_dotenv()

    llm = OpenAIProvider()
    agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=5)

    user_input = "item=iPhone; qty=2; coupon=WINNER; city=Hanoi"
    print(agent.run(user_input))


if __name__ == "__main__":
    main()
```

If import paths fail, use `python -m` execution from repo root instead of running files directly.

#### Step 2: Demo prompts (copy/paste)
1) Happy path  
`item=iPhone; qty=2; coupon=WINNER; city=Hanoi`  
Expected: breakdown + total `42539600` (VND).

2) Invalid coupon  
`item=iPhone; qty=2; coupon=FREE100; city=Hanoi`  
Expected: agent reacts to `error=unknown_coupon` and proceeds with 0% or asks user to retry.

3) Out of stock  
`item=MacBook; qty=999; coupon=SAVE10; city=HCMC`  
Expected: agent detects insufficient stock and stops with a helpful message.

#### Step 3: 2–3 minute talk track
- Chatbot may “guess” totals.
- ReAct agent *acts*: calls tools for stock/discount/shipping.
- Observations are fed back, so the final answer is grounded.
- Logs/traces prove decisions (“trace is truth”).

---

## Integration Checklist (15 minutes before demo)
- `from src.tools import TOOLS` works
- `uv run python tests/test_tools_demo.py` prints correct key=value outputs
- Agent stops with `Final Answer:` before `max_steps`
- Happy path computes total = **42,539,600 VND**

---

## One-line summary
- Member 1: `src/tools/*` + `TOOLS`
- Member 2: ReAct loop in `src/agent/agent.py`
- Member 3: parsing + dispatch robustness
- Member 4: demo runner + prompts + presentation

