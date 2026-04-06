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

default_provider = os.getenv("DEFAULT_PROVIDER", "openai").lower()
if default_provider == "gemini":
    default_provider = "google"

provider_name = st.sidebar.selectbox("LLM Provider", ["openai", "google", "local"], index=["openai", "google", "local"].index(default_provider) if default_provider in ["openai", "google", "local"] else 0)
model_name = st.sidebar.text_input("Model Name", value=os.getenv("DEFAULT_MODEL", "gpt-4o"))
max_steps = st.sidebar.slider("Max Steps (ReAct)", min_value=1, max_value=10, value=5)

st.title("🤖 Chatbot vs ReAct Agent Comparison")
st.markdown("Compare the reasoning capability of a standard Chatbot vs a ReAct Agent with Tools.")

user_input = st.chat_input("Enter your query...")

if user_input:
    st.markdown(f"**You:** {user_input}")
    
    # ---------------------------------------------------------
    # TOP: Basic Chatbot
    # ---------------------------------------------------------
    st.subheader("Basic Chatbot")
    chatbot_placeholder = st.empty()
    chatbot_placeholder.info("Basic Chatbot is processing...")
    
    try:
        llm_chat = _build_provider(provider_name, model_name)
        tracker.session_metrics = [] # Reset metrics
        
        start_time_chat = time.time()
        chat_agent = SimpleChatbot(llm=llm_chat)
        chat_response = chat_agent.run(user_input)
        chat_latency = int((time.time() - start_time_chat) * 1000)
        
        chat_tokens = sum(m.get("total_tokens", 0) for m in tracker.session_metrics)
        chat_cost = sum(m.get("cost_estimate", 0) for m in tracker.session_metrics)
        
        chatbot_placeholder.empty()
        st.write(chat_response)
        st.markdown(f"<span style='font-size:0.8em; color:gray;'>Tokens: {chat_tokens} | Latency: {chat_latency}ms | Steps: 1 | Cost: ${chat_cost:.4f}</span>", unsafe_allow_html=True)
        
    except Exception as e:
        chatbot_placeholder.error(f"Error: {str(e)}")

    st.divider()

    # ---------------------------------------------------------
    # BOTTOM: ReAct Agent
    # ---------------------------------------------------------
    st.subheader("ReAct Agent")
    react_placeholder = st.empty()
    react_placeholder.info("ReAct Agent is processing...")
    
    try:
        llm_react = _build_provider(provider_name, model_name)
        tracker.session_metrics = [] # Reset metrics for react
        
        start_time_react = time.time()
        react_agent = ReActAgent(llm=llm_react, tools=TOOLS, max_steps=max_steps)
        react_response = react_agent.run(user_input)
        react_latency = int((time.time() - start_time_react) * 1000)
        
        react_tokens = sum(m.get("total_tokens", 0) for m in tracker.session_metrics)
        react_cost = sum(m.get("cost_estimate", 0) for m in tracker.session_metrics)
        react_steps = len(react_agent.history)
        
        react_placeholder.empty()
        st.write(react_response)
        st.markdown(f"<span style='font-size:0.8em; color:gray;'>Tokens: {react_tokens} | Latency: {react_latency}ms | Steps: {react_steps} | Cost: ${react_cost:.4f}</span>", unsafe_allow_html=True)
        
        if react_agent.history:
            with st.expander("Show ReAct Trace"):
                for step_info in react_agent.history:
                    st.text(f"Step {step_info['step']}:\n{step_info['response']}")
                    
    except Exception as e:
        react_placeholder.error(f"Error: {str(e)}")
