import re
from typing import List, Dict, Any, Optional, Tuple
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """
    
    ACTION_RE = re.compile(
        r"^\s*Action:\s*([a-zA-Z_]\w*)\s*\((.*)\)\s*$",
        re.MULTILINE,
    )
    FINAL_RE = re.compile(r"Final Answer:\s*(.*)", re.DOTALL)

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return (
            "You are a Smart Checkout ReAct Agent.\n"
            "You can only use these tools:\n"
            f"{tool_descriptions}\n\n"
            "Rules:\n"
            "- If you need a tool, output exactly:\n"
            "  Thought: ...\n"
            "  Action: tool_name(arguments)\n"
            "- Output exactly one Action line per step.\n"
            "- Do NOT write Observation by yourself.\n"
            "- Never fabricate tool results.\n"
            "- Use only the listed tool names.\n"
            "- Never use markdown code fences.\n"
            "- If the user asks an off-topic question, immediately refuse by starting with: Final Answer: [Your apology]\n"
            "- When enough information is available for a checkout, output:\n"
            "  Final Answer: [Your friendly response here]\n\n"
            "For valid checkout requests, your Final Answer MUST be formatted as a friendly, user-readable summary or receipt (e.g., using bullet points) and clearly show ALL of the following details:\n"
            "- Item name & Quantity\n"
            "- Unit Price & Subtotal (VND)\n"
            "- Discount applied (%), Discount Amount (VND), & Discounted Subtotal (VND)\n"
            "- Shipping Fee (VND)\n"
            "- Final Total (VND)\n"
            "- Stock status (e.g., In stock / Not enough)\n"
        )

    def parse_action(self, text: str) -> Optional[Tuple[str, str]]:
        match = self.ACTION_RE.search(text or "")
        if not match:
            return None
        return match.group(1).strip(), match.group(2).strip()

    def parse_final(self, text: str) -> Optional[str]:
        match = self.FINAL_RE.search(text or "")
        if not match:
            return None
        return match.group(1).strip()

    @staticmethod
    def _strip_quotes(value: str) -> str:
        value = value.strip()
        if len(value) >= 2 and (
            (value[0] == '"' and value[-1] == '"')
            or (value[0] == "'" and value[-1] == "'")
        ):
            return value[1:-1].strip()
        return value

    def parse_args_for_tool(self, tool_name: str, raw: str) -> List[Any]:
        raw = (raw or "").strip()

        if tool_name in {"check_stock", "get_discount"}:
            # Support both: check_stock("iPhone") and check_stock(item_name="iPhone")
            arg = raw.split("=", 1)[-1].strip() if "=" in raw else raw
            return [self._strip_quotes(arg)]

        if tool_name == "calc_shipping":
            # Support both positional and named arguments.
            parts = [part.strip() for part in raw.split(",", 1)]
            if len(parts) != 2:
                raise ValueError("calc_shipping requires 2 arguments")

            left = parts[0].split("=", 1)[-1].strip()
            right = parts[1].split("=", 1)[-1].strip()

            weight = float(left)
            destination = self._strip_quotes(right)
            return [weight, destination]

        raise ValueError(f"unsupported_tool={tool_name}")

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        current_prompt = f"User input: {user_input}\n"
        system_prompt = self.get_system_prompt()
        steps = 0

        while steps < self.max_steps:
            step_no = steps + 1
            try:
                result = self.llm.generate(current_prompt, system_prompt=system_prompt)
            except Exception as exc:
                logger.error(f"LLM generate failed at step {step_no}: {exc}", exc_info=False)
                logger.log_event("AGENT_END", {"steps": steps, "status": "llm_error"})
                return f"Final Answer: error=llm_failure, message={str(exc)}"

            content = ""
            usage = None
            latency_ms = None
            if isinstance(result, dict):
                content = str(result.get("content", "")).strip()
                usage = result.get("usage")
                latency_ms = result.get("latency_ms")
            else:
                content = str(result).strip()

            self.history.append(
                {
                    "step": step_no,
                    "prompt": current_prompt,
                    "response": content,
                }
            )

            logger.log_event(
                "LLM_STEP",
                {
                    "step": step_no,
                    "response": content,
                    "usage": usage,
                    "latency_ms": latency_ms,
                },
            )

            final_answer = self.parse_final(content)
            if final_answer:
                logger.log_event("AGENT_END", {"steps": step_no, "status": "success"})
                return f"Final Answer: {final_answer}"

            action = self.parse_action(content)
            if not action:
                observation = "error=parse_failed, message=missing_action_or_final_answer"
                logger.log_event(
                    "AGENT_PARSE_ERROR",
                    {"step": step_no, "response": content},
                )
                current_prompt += f"\n{content}\nObservation: {observation}\n"
                steps += 1
                continue

            tool_name, raw_args = action
            observation = self._execute_tool(tool_name, raw_args)

            logger.log_event(
                "TOOL_CALL",
                {
                    "step": step_no,
                    "tool": tool_name,
                    "raw_args": raw_args,
                    "observation": observation,
                },
            )

            current_prompt += f"\n{content}\nObservation: {observation}\n"
            steps += 1

        logger.log_event("AGENT_END", {"steps": steps, "status": "max_steps_exceeded"})
        return "Final Answer: error=max_steps_exceeded, message=unable_to_reach_final_answer"

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Helper method to execute tools by name.
        """
        tool = next((tool for tool in self.tools if tool.get("name") == tool_name), None)
        if tool is None:
            return f"error=unknown_tool, tool={tool_name}"

        try:
            parsed_args = self.parse_args_for_tool(tool_name, args)
            output = tool["func"](*parsed_args)
            return str(output)
        except Exception as exc:
            logger.error(f"Tool execution failed: {tool_name}({args}) -> {exc}", exc_info=False)
            return f"error=tool_execution_failed, tool={tool_name}, message={str(exc)}"
