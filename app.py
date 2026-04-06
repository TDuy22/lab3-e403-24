import os
import sys
import time
import streamlit as st
from dotenv import load_dotenv

# Ensure project root is on sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.agent.chatbot import SimpleChatbot
from src.agent.agent import ReActAgent
from src.tools import TOOLS
from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.core.local_provider import LocalProvider
from src.telemetry.metrics import tracker

load_dotenv()

st.set_page_config(page_title="Lab 3: Chatbot vs ReAct Agent", page_icon="🤖", layout="wide")

def _build_provider(provider_name: str, model_name: str):
    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        return OpenAIProvider(model_name=model_name or "gpt-4o", api_key=api_key)
    elif provider_name == "google":
        api_key = os.getenv("GEMINI_API_KEY")
        model = model_name or "gemini-1.5-flash"
        if model == "gpt-4o":
             model = "gemini-1.5-flash"
        return GeminiProvider(model_name=model, api_key=api_key)
    elif provider_name == "local":
        model_path = os.getenv("LOCAL_MODEL_PATH", "")
        abs_model_path = os.path.abspath(os.path.join(ROOT_DIR, model_path))
        return LocalProvider(model_path=abs_model_path)
    raise ValueError(f"Unknown provider: {provider_name}")

st.sidebar.title("Configuration")
mode = st.sidebar.radio("Select Mode", ["Basic Chatbot", "ReAct Agent"])

default_provider = os.getenv("DEFAULT_PROVIDER", "openai").lower()
if default_provider == "gemini":
    default_provider = "google"

provider_name = st.sidebar.selectbox("LLM Provider", ["openai", "google", "local"], index=["openai", "google", "local"].index(default_provider) if default_provider in ["openai", "google", "local"] else 0)
model_name = st.sidebar.text_input("Model Name", value=os.getenv("DEFAULT_MODEL", "gpt-4o"))
max_steps = st.sidebar.slider("Max Steps (ReAct)", min_value=1, max_value=10, value=5)

st.title(f"🤖 {mode} Demo")
st.markdown("Compare the reasoning capability of a standard Chatbot vs a ReAct Agent with Tools.")

# Demo Prompts
st.sidebar.subheader("Demo Scenarios")
if st.sidebar.button("Scenario 1: Happy Path"):
    st.session_state.demo_input = "item=iPhone; qty=2; coupon=WINNER; city=Hanoi"
if st.sidebar.button("Scenario 2: Out of stock"):
    st.session_state.demo_input = "item=MacBook; qty=999; coupon=SAVE10; city=HCMC"
if st.sidebar.button("Scenario 3: Simple Chat"):
    st.session_state.demo_input = "What is the capital of Vietnam?"
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []

user_input = st.chat_input("Enter your query...")

if "demo_input" in st.session_state:
    user_input = st.session_state.demo_input
    del st.session_state.demo_input

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
         with st.chat_message("assistant"):
            st.write(msg["content"])
            if "metrics" in msg:
                cols = st.columns(4)
                cols[0].metric("Tokens", msg["metrics"]["tokens"])
                cols[1].metric("Latency", f"{msg['metrics']['latency']} ms")
                cols[2].metric("Steps", msg["metrics"]["steps"])
                cols[3].metric("Cost", f"${msg['metrics']['cost']:.4f}")
            if "history" in msg and msg["history"]:
                with st.expander(f"Show {msg['mode']} Trace / History"):
                    for step in msg["history"]:
                        st.text(f"Step {step['step']}:\n{step['response']}")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)
    
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        status_placeholder.info("Processing...")
        
        try:
            llm = _build_provider(provider_name, model_name)
            
            # Reset metrics for this run
            tracker.session_metrics = []
            start_time = time.time()
            
            if mode == "Basic Chatbot":
                agent = SimpleChatbot(llm=llm)
            else:
                agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=max_steps)
                
            response = agent.run(user_input)
            
            # Aggregate metrics
            total_tokens = sum(m.get("total_tokens", 0) for m in tracker.session_metrics)
            total_cost = sum(m.get("cost_estimate", 0) for m in tracker.session_metrics)
            total_latency = int((time.time() - start_time) * 1000)
            steps = len(agent.history)
            
            metrics = {
                "tokens": total_tokens,
                "latency": total_latency,
                "steps": steps,
                "cost": total_cost
            }
            
            status_placeholder.empty()
            st.write(response)
            
            cols = st.columns(4)
            cols[0].metric("Tokens", total_tokens)
            cols[1].metric("Latency", f"{total_latency} ms")
            cols[2].metric("Steps", steps)
            cols[3].metric("Cost", f"${total_cost:.4f}")
            
            if agent.history:
                with st.expander(f"Show {mode} Trace / History"):
                    for step in agent.history:
                        st.text(f"Step {step['step']}:\n{step['response']}")
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "metrics": metrics,
                "history": agent.history,
                "mode": mode
            })
            
        except Exception as e:
            st.error(f"Error: {str(e)}")