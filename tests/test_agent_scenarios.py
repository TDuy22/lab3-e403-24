from typing import Any, Dict, Generator, List, Optional

from src.agent.agent import ReActAgent
from src.core.llm_provider import LLMProvider
from src.tools import TOOLS


class ScriptedLLM(LLMProvider):
    """Deterministic fake LLM for scenario testing."""

    def __init__(
        self,
        outputs: Optional[List[str]] = None,
        error_on_call: Optional[int] = None,
        error_message: str = "api_unavailable",
    ):
        super().__init__(model_name="scripted-llm")
        self.outputs = outputs or []
        self.error_on_call = error_on_call
        self.error_message = error_message
        self.calls = 0
        self.prompts: List[str] = []

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        self.calls += 1
        self.prompts.append(prompt)

        if self.error_on_call is not None and self.calls == self.error_on_call:
            raise RuntimeError(self.error_message)

        if not self.outputs:
            content = "Final Answer: fallback"
        elif self.calls - 1 < len(self.outputs):
            content = self.outputs[self.calls - 1]
        else:
            content = self.outputs[-1]

        return {
            "content": content,
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
            "latency_ms": 1,
            "provider": "scripted",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        yield ""


def test_unrelated_topic_returns_final_answer_without_stuck():
    llm = ScriptedLLM(
        outputs=[
            "Final Answer: Sorry, I only support smart checkout requests such as item/qty/coupon/city.",
        ]
    )
    agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=5)

    result = agent.run("Hom nay thoi tiet the nao?")

    assert result.startswith("Final Answer:")
    assert "only support smart checkout" in result
    assert llm.calls == 1


def test_unknown_tool_call_is_handled_and_agent_recovers():
    llm = ScriptedLLM(
        outputs=[
            "Thought: I should call a weather tool.\nAction: weather_lookup(\"Hanoi\")",
            "Final Answer: This is not a checkout request. Please provide item, qty, coupon, city.",
        ]
    )
    agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=5)

    result = agent.run("Thoi tiet Ha Noi")

    assert result.startswith("Final Answer:")
    assert "not a checkout request" in result
    assert llm.calls == 2
    assert "error=unknown_tool" in llm.prompts[1]


def test_llm_api_failure_returns_safe_final_answer():
    llm = ScriptedLLM(error_on_call=1, error_message="network_timeout")
    agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=5)

    result = agent.run("item=iPhone; qty=1; coupon=NONE; city=Hanoi")

    assert result.startswith("Final Answer:")
    assert "error=llm_failure" in result
    assert "network_timeout" in result


def test_exceed_max_steps_returns_fallback_not_stuck():
    llm = ScriptedLLM(outputs=["Thought: still thinking..."])
    agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=3)

    result = agent.run("item=iPhone; qty=1; coupon=NONE; city=Hanoi")

    assert result.startswith("Final Answer:")
    assert "error=max_steps_exceeded" in result
    assert llm.calls == 3


def test_parse_failure_then_recover_with_final_answer():
    llm = ScriptedLLM(
        outputs=[
            "I forgot to follow format.",
            "Final Answer: Checkout summary is available. Please review totals below.",
        ]
    )
    agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=5)

    result = agent.run("item=iPhone; qty=1; coupon=NONE; city=Hanoi")

    assert result.startswith("Final Answer:")
    assert "Checkout summary" in result
    assert llm.calls == 2
    assert "error=parse_failed" in llm.prompts[1]
