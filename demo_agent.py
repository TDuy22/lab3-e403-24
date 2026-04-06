import argparse
import os
import sys
from typing import List, Dict, Any

from dotenv import load_dotenv

# Ensure project root is on sys.path when running this file directly.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.agent.agent import ReActAgent


def _load_tools() -> List[Dict[str, Any]]:
    try:
        from src.tools import TOOLS  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "Cannot import TOOLS from src.tools. "
            "Please implement tools first (see TEAM_PLAN Member 1)."
        ) from exc
    return TOOLS


def _resolve_provider_name(raw: str) -> str:
    provider = (raw or "openai").strip().lower()
    if provider == "gemini":
        provider = "google"
    if provider not in {"openai", "google", "local"}:
        raise ValueError("DEFAULT_PROVIDER must be one of: openai, google, local")
    return provider


def _build_provider(provider: str, model_name: str):
    if provider == "openai":
        from src.core.openai_provider import OpenAIProvider

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing in .env")
        return OpenAIProvider(model_name=model_name or "gpt-4o", api_key=api_key)

    if provider == "google":
        from src.core.gemini_provider import GeminiProvider

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing in .env")

        selected_model = model_name or "gemini-1.5-flash"
        if selected_model == "gpt-4o":
            selected_model = "gemini-1.5-flash"
        return GeminiProvider(model_name=selected_model, api_key=api_key)

    model_path = os.getenv("LOCAL_MODEL_PATH", "").strip()
    if not model_path:
        raise ValueError("LOCAL_MODEL_PATH is missing in .env")

    from src.core.local_provider import LocalProvider

    abs_model_path = os.path.abspath(os.path.join(ROOT_DIR, model_path))
    return LocalProvider(model_path=abs_model_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Lab 3 ReAct agent demo")
    parser.add_argument(
        "--input",
        default="item=iPhone; qty=2; coupon=WINNER; city=Hanoi",
        help="Demo input in format: item=<name>; qty=<int>; coupon=<code|none>; city=<city>",
    )
    parser.add_argument(
        "--provider",
        default=None,
        choices=["openai", "google", "gemini", "local"],
        help="Override provider from .env",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override model name from .env",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=5,
        help="Maximum ReAct loop steps",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()

    provider_from_env = os.getenv("DEFAULT_PROVIDER", "openai")
    provider_name = _resolve_provider_name(args.provider or provider_from_env)
    model_name = args.model or os.getenv("DEFAULT_MODEL", "")

    try:
        llm = _build_provider(provider_name, model_name)
        tools = _load_tools()
        agent = ReActAgent(llm=llm, tools=tools, max_steps=args.max_steps)
        result = agent.run(args.input)
        print(result)
        return 0
    except Exception as exc:
        print(f"Runner error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
