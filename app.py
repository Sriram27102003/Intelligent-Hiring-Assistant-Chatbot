"""
TalentScout Hiring Assistant Chatbot
Uses Groq API (free, fast, no strict quota).
"""

import streamlit as st
from groq import Groq
import os
from conversation_manager import ConversationManager
from data_handler import DataHandler

st.set_page_config(
    page_title="TalentScout | Hiring Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #0f1117; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f2e 0%, #0f1117 100%);
        border-right: 1px solid #2d3748;
    }
    [data-testid="stChatMessage"] { border-radius: 12px; margin-bottom: 8px; padding: 4px; }
    [data-testid="stChatInput"] textarea {
        background-color: #1a1f2e !important;
        color: #e2e8f0 !important;
        border: 1px solid #4a5568 !important;
        border-radius: 12px !important;
    }
    .progress-container { background: #2d3748; border-radius: 10px; height: 8px; margin: 8px 0; overflow: hidden; }
    .progress-bar { background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; border-radius: 10px; }
    .logo-text { font-size: 1.5rem; font-weight: 800; background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .field-chip { display: inline-block; background: #2d3748; color: #a0aec0; border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; margin: 2px; }
    .field-chip.done { background: #1c4532; color: #68d391; }
</style>
""", unsafe_allow_html=True)


def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "manager" not in st.session_state:
        st.session_state.manager = ConversationManager()
    if "data_handler" not in st.session_state:
        st.session_state.data_handler = DataHandler()
    if "conversation_ended" not in st.session_state:
        st.session_state.conversation_ended = False
    if "greeted" not in st.session_state:
        st.session_state.greeted = False
    if "api_key_set" not in st.session_state:
        st.session_state.api_key_set = bool(os.environ.get("GROQ_API_KEY", ""))


def render_api_key_screen():
    st.markdown("## 🔑 Enter your Groq API Key")
    st.markdown("""
    TalentScout now uses **Groq** — completely free, no quota issues, very fast!

    **How to get a free Groq API key:**
    1. Go to 👉 **https://console.groq.com**
    2. Sign up with Google or Email (free)
    3. Click **"API Keys"** → **"Create API Key"**
    4. Copy and paste it below
    """)

    api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")

    if st.button("✅ Save & Start", use_container_width=True):
        if api_key.strip():
            os.environ["GROQ_API_KEY"] = api_key.strip()
            st.session_state.api_key_set = True
            st.rerun()
        else:
            st.error("Please enter a valid API key.")

    st.info("🔒 Your key is stored only in this browser session and never saved to disk.")


def render_sidebar():
    manager = st.session_state.manager
    with st.sidebar:
        st.markdown('<div class="logo-text">🤖 TalentScout</div>', unsafe_allow_html=True)
        st.markdown("*Intelligent Hiring Assistant*")
        st.divider()

        stage = manager.get_stage()
        stage_labels = {
            "greeting": ("Greeting", 10),
            "gathering_info": ("Gathering Info", 33),
            "tech_stack": ("Tech Stack", 60),
            "technical_questions": ("Technical Questions", 80),
            "closing": ("Closing", 100),
        }
        label, pct = stage_labels.get(stage, ("Active", 50))

        st.markdown("**Session Progress**")
        st.markdown(f'<div class="progress-container"><div class="progress-bar" style="width:{pct}%"></div></div>', unsafe_allow_html=True)
        st.markdown(f"Stage: **{label}** ({pct}%)")
        st.divider()

        info = manager.candidate_info
        fields = {
            "Full Name": info.get("full_name"),
            "Email": info.get("email"),
            "Phone": info.get("phone"),
            "Experience": info.get("years_experience"),
            "Desired Position": info.get("desired_position"),
            "Location": info.get("location"),
            "Tech Stack": ", ".join(info.get("tech_stack", [])) or None,
        }

        st.markdown("**Candidate Profile**")
        for field, value in fields.items():
            if value:
                st.markdown(f'<span class="field-chip done">✓ {field}</span>', unsafe_allow_html=True)
                st.caption(f"  {value}")
            else:
                st.markdown(f'<span class="field-chip">○ {field}</span>', unsafe_allow_html=True)

        st.divider()
        qa = manager.qa_progress
        if qa["total"] > 0:
            st.markdown(f"**Technical Q&A**: {qa['answered']}/{qa['total']} answered")

        if st.button("🔄 Start New Session", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def get_ai_response(user_message: str) -> str:
    """Get response from Groq (free & fast)."""
    manager = st.session_state.manager
    api_key = os.environ.get("GROQ_API_KEY", "")

    if not api_key:
        return "❌ API key not found. Please restart and enter your Groq API key."

    try:
        client = Groq(api_key=api_key)
        system_prompt = manager.get_system_prompt()

        # Build message history
        messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        error_msg = str(e)
        if "invalid_api_key" in error_msg.lower() or "401" in error_msg:
            return "❌ Invalid API key. Please restart and enter a valid Groq API key."
        elif "rate_limit" in error_msg.lower() or "429" in error_msg:
            return "⚠️ Rate limit hit. Please wait a moment and try again."
        else:
            return f"⚠️ Error: {error_msg}"


def handle_user_input(user_input: str):
    manager = st.session_state.manager
    data_handler = st.session_state.data_handler

    EXIT_KEYWORDS = {"exit", "quit", "bye", "goodbye", "end", "stop"}
    if any(kw in user_input.lower().split() for kw in EXIT_KEYWORDS):
        st.session_state.conversation_ended = True
        farewell = manager.get_farewell_message()
        data_handler.save_session(manager.candidate_info, st.session_state.messages)
        return farewell

    manager.extract_and_update_info(user_input)
    response = get_ai_response(user_input)
    manager.process_ai_response(response, user_input)
    return response


def main():
    init_session()

    if not st.session_state.api_key_set:
        render_api_key_screen()
        return

    render_sidebar()

    st.markdown("## 💼 TalentScout Hiring Assistant")
    st.markdown("*Your intelligent first step in the recruitment journey*")
    st.divider()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not st.session_state.greeted:
        greeting = st.session_state.manager.get_greeting()
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.greeted = True
        with st.chat_message("assistant"):
            st.markdown(greeting)

    if st.session_state.conversation_ended:
        st.info("✅ Session complete. Thank you for using TalentScout! Our team will review your profile and reach out within 3–5 business days.")
        return

    if user_input := st.chat_input("Type your message here…"):
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                response = handle_user_input(user_input)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

        if st.session_state.conversation_ended:
            st.rerun()


if __name__ == "__main__":
    main()
