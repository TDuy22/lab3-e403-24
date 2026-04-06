import time
from typing import Dict, Any
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class SimpleChatbot:
    """
    A basic baseline chatbot that just sends the prompt to the LLM without any tools.
    """
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.history = []

    def get_system_prompt(self) -> str:
        return (
            "You are a helpful e-commerce assistant. "
            "Please answer the user's questions directly to the best of your ability. "
            "You do not have access to any external tools or real-time data."
        )

    def run(self, user_input: str) -> str:
        logger.log_event("CHATBOT_START", {"input": user_input, "model": self.llm.model_name})
        
        system_prompt = self.get_system_prompt()
        current_prompt = f"User input: {user_input}"
        
        try:
            result = self.llm.generate(current_prompt, system_prompt=system_prompt)
        except Exception as exc:
            logger.error(f"LLM generate failed: {exc}", exc_info=False)
            logger.log_event("CHATBOT_END", {"status": "llm_error"})
            return f"Error: {str(exc)}"

        content = ""
        usage = None
        latency_ms = None
        
        if isinstance(result, dict):
            content = str(result.get("content", "")).strip()
            usage = result.get("usage")
            latency_ms = result.get("latency_ms")
            
            # Import tracker here to log telemetry
            from src.telemetry.metrics import tracker
            provider_name = result.get("provider", "unknown")
            if usage and latency_ms:
                tracker.track_request(provider_name, self.llm.model_name, usage, latency_ms)
        else:
            content = str(result).strip()

        self.history.append({
            "step": 1,
            "prompt": current_prompt,
            "response": content
        })

        logger.log_event(
            "LLM_STEP",
            {
                "step": 1,
                "response": content,
                "usage": usage,
                "latency_ms": latency_ms,
            },
        )
        
        logger.log_event("CHATBOT_END", {"status": "success"})
        return content
