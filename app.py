import html
import streamlit as st
from main import model_generate

st.set_page_config(
    page_title="Legal Lens",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# State
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []


# -----------------------------
# Helpers
# -----------------------------
def normalize_result(result):
    if isinstance(result, tuple):
        answer, sections = result
    else:
        answer, sections = result, []

    if isinstance(answer, tuple):
        answer = answer[0]

    if sections is None:
        sections = []

    unique_sections = []
    for sec in sections:
        if sec not in unique_sections:
            unique_sections.append(sec)

    return str(answer).strip(), unique_sections


def render_sources(sections):
    if not sections:
        return

    pills = "".join(
        f'<span class="source-pill">📄 {html.escape(str(sec))}</span>'
        for sec in sections
    )

    st.markdown(
        f"""
        <div class="sources-wrap">
            <div class="sources-title">Sources</div>
            <div class="source-pill-row">{pills}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def clear_chat():
    st.session_state.messages = []


# -----------------------------
# CSS
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg-1: #07090c;
    --bg-2: #0d1117;
    --panel: rgba(17, 21, 27, 0.92);
    --panel-2: rgba(25, 30, 37, 0.96);
    --panel-3: rgba(38, 43, 52, 0.98);
    --text: #f6f8fb;
    --muted: #97a3b3;
    --muted-2: #b7c0cb;
    --border: rgba(255,255,255,0.08);
    --border-soft: rgba(255,255,255,0.05);
    --shadow: 0 18px 60px rgba(0,0,0,0.28);
}

/* Global */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    color: var(--text);
    background:
        radial-gradient(circle at top left, rgba(80,120,255,0.06), transparent 22%),
        radial-gradient(circle at top right, rgba(255,255,255,0.035), transparent 18%),
        linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 100%);
}

/* Hide default Streamlit chrome */
#MainMenu, header, footer {
    visibility: hidden;
}

[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="collapsedControl"] {
    display: none !important;
}

/* Hide ugly default user avatar */
[data-testid="stChatMessageAvatarUser"] {
    display: none !important;
}

/* Main container */
.block-container {
    max-width: 980px;
    padding-top: 6.2rem;
    padding-bottom: 9rem;
}

/* Topbar */
.topbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999;
    height: 72px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(7, 9, 12, 0.72);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border-soft);
}

.topbar-inner {
    width: 100%;
    max-width: 1100px;
    padding: 0 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-icon {
    width: 42px;
    height: 42px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(180deg, #1c2129 0%, #2a3039 100%);
    border: 1px solid var(--border);
    box-shadow: 0 12px 28px rgba(0,0,0,0.24);
    font-size: 1rem;
}

.brand-text {
    line-height: 1.05;
}

.brand-title {
    font-size: 1rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.03em;
}

.brand-subtitle {
    margin-top: 4px;
    color: var(--muted);
    font-size: 0.78rem;
    font-weight: 500;
}

.brand-chip {
    padding: 9px 13px;
    border-radius: 999px;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    color: var(--muted-2);
    font-size: 0.8rem;
    font-weight: 600;
}

/* Top right new chat row */
.top-actions {
    margin-top: 0.15rem;
    margin-bottom: 1.5rem;
}

/* Buttons base */
div.stButton > button {
    width: 100%;
    min-height: 56px;
    border-radius: 18px;
    border: 1px solid var(--border);
    background: linear-gradient(180deg, rgba(25,29,36,0.96), rgba(16,20,26,0.98));
    color: #f4f7fb;
    font-weight: 600;
    font-size: 0.95rem;
    box-shadow: 0 12px 30px rgba(0,0,0,0.18);
    transition: 0.18s ease;
}

div.stButton > button:hover {
    transform: translateY(-1px);
    border-color: rgba(255,255,255,0.13);
    background: linear-gradient(180deg, rgba(31,36,43,0.98), rgba(19,23,29,1));
}

/* Primary button = New Chat */
div.stButton > button[kind="primary"] {
    background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%) !important;
    color: white !important;
    border: 1px solid rgba(96,165,250,0.55) !important;
    box-shadow: 0 14px 36px rgba(37,99,235,0.28) !important;
}

div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(180deg, #4b8df8 0%, #2f6ff0 100%) !important;
    border-color: rgba(147,197,253,0.8) !important;
}

/* Hero */
.hero-wrap {
    max-width: 760px;
    margin: 0 auto 2rem auto;
    text-align: center;
}

.hero-title {
    font-size: 3rem;
    line-height: 1.04;
    font-weight: 800;
    letter-spacing: -0.055em;
    color: #ffffff;
    margin-bottom: 0.9rem;
}

.hero-subtitle {
    color: var(--muted);
    font-size: 1.02rem;
    line-height: 1.85;
}

/* Example row */
.example-row {
    max-width: 980px;
    margin: 0 auto 1rem auto;
}

/* Force equal looking example buttons */
.example-btn div.stButton > button {
    min-height: 72px !important;
    border-radius: 20px !important;
    padding: 0.9rem 1rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    line-height: 1.45 !important;
}

/* Chat cards */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin-bottom: 1rem;
}

[data-testid="stChatMessageContent"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    width: 100%;
}

.msg-user,
.msg-assistant {
    display: none;
}

/* User message */
[data-testid="stChatMessage"]:has(.msg-user) {
    display: flex;
    justify-content: flex-end;
}

[data-testid="stChatMessage"]:has(.msg-user) [data-testid="stChatMessageContent"] {
    max-width: 74%;
    margin-left: auto;
    background: linear-gradient(180deg, rgba(42,47,56,0.98), rgba(31,36,44,0.98)) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 22px !important;
    padding: 16px 18px !important;
    box-shadow: 0 14px 34px rgba(0,0,0,0.18);
}

/* Assistant message */
[data-testid="stChatMessage"]:has(.msg-assistant) [data-testid="stChatMessageContent"] {
    background: linear-gradient(180deg, rgba(16,20,26,0.95), rgba(12,15,20,0.98)) !important;
    border: 1px solid var(--border) !important;
    border-radius: 24px !important;
    padding: 18px 20px !important;
    box-shadow: var(--shadow);
}

.assistant-label {
    font-size: 0.82rem;
    font-weight: 700;
    color: #dbe3ee;
    margin-bottom: 0.55rem;
}

/* Markdown inside chat */
[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] li {
    color: #edf2f8 !important;
    font-size: 0.97rem;
    line-height: 1.85 !important;
}

[data-testid="stChatMessageContent"] h1,
[data-testid="stChatMessageContent"] h2,
[data-testid="stChatMessageContent"] h3,
[data-testid="stChatMessageContent"] h4 {
    color: #ffffff !important;
    letter-spacing: -0.02em;
    margin-top: 0.4rem;
    margin-bottom: 0.55rem;
}

[data-testid="stChatMessageContent"] ul,
[data-testid="stChatMessageContent"] ol {
    padding-left: 1.2rem;
}

[data-testid="stChatMessageContent"] hr {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 1rem 0;
}

[data-testid="stChatMessageContent"] pre {
    background: #0c1015 !important;
    border: 1px solid var(--border-soft) !important;
    border-radius: 16px !important;
    padding: 14px !important;
}

[data-testid="stChatMessageContent"] code {
    color: #eef3f8 !important;
}

/* Sources */
.sources-wrap {
    margin-top: 1rem;
}

.sources-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--muted-2);
    margin-bottom: 0.55rem;
}

.source-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
}

.source-pill {
    display: inline-flex;
    align-items: center;
    padding: 9px 12px;
    border-radius: 999px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    color: #dfe7f1;
    font-size: 0.82rem;
    font-weight: 600;
}

/* Input */
[data-testid="stChatInput"] {
    position: fixed;
    left: 50%;
    bottom: 34px;
    transform: translateX(-50%);
    width: min(960px, calc(100vw - 1rem));
    background: rgba(10, 13, 17, 0.8);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 24px;
    padding: 0.45rem 0.6rem;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    box-shadow: 0 22px 60px rgba(0,0,0,0.34);
}

[data-testid="stChatInput"] > div {
    border: none !important;
    background: transparent !important;
}

[data-testid="stChatInput"] textarea {
    color: #f5f7fb !important;
    font-size: 0.98rem !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #93a0ad !important;
}

/* Footer */
.credit-footer {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 8px;
    text-align: center;
    color: #697482;
    font-size: 0.76rem;
    font-weight: 600;
    z-index: 998;
    pointer-events: none;
}

/* Mobile */
@media (max-width: 900px) {
    .brand-chip {
        display: none;
    }

    .hero-title {
        font-size: 2.2rem;
    }

    .block-container {
        padding-top: 5.8rem;
        padding-bottom: 10rem;
    }

    [data-testid="stChatMessage"]:has(.msg-user) [data-testid="stChatMessageContent"] {
        max-width: 90%;
    }

    [data-testid="stChatInput"] {
        width: calc(100vw - 0.6rem);
    }
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Top bar
# -----------------------------
st.markdown("""
<div class="topbar">
    <div class="topbar-inner">
        <div class="brand">
            <div class="brand-icon">⚖️</div>
            <div class="brand-text">
                <div class="brand-title">Legal Lens</div>
                <div class="brand-subtitle">Grounded legal assistant for the IT Act, 2000</div>
            </div>
        </div>
        <div class="brand-chip">Semantic RAG + Local LLM</div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Top-right New Chat
# -----------------------------
st.markdown('<div class="top-actions"></div>', unsafe_allow_html=True)
top_left, top_right = st.columns([9, 2])

with top_right:
    if st.button("New Chat", key="new_chat_btn", type="primary"):
        clear_chat()
        st.rerun()

# -----------------------------
# Empty state
# -----------------------------
example_prompt = None

if len(st.session_state.messages) == 0:
    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-title">Trusted Legal Answers from Context.</div>
        <div class="hero-subtitle">
            Ask questions about the Information Technology Act, 2000.
            Legal Lens retrieves relevant sections first, then answers in clear, structured markdown.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="example-row"></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown('<div class="example-btn">', unsafe_allow_html=True)
        if st.button("Explain section 66", key="example_1"):
            example_prompt = "Explain section 66"
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="example-btn">', unsafe_allow_html=True)
        if st.button("Which section apply to electronic records?", key="example_2"):
            example_prompt = "Which section apply to electronic records?"
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="example-btn">', unsafe_allow_html=True)
        if st.button("What is the punishment for identity theft?", key="example_3"):
            example_prompt = "What is the punishment for identity theft?"
        st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Render old messages
# -----------------------------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown('<span class="msg-user"></span>', unsafe_allow_html=True)
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="⚖️"):
            st.markdown('<span class="msg-assistant"></span>', unsafe_allow_html=True)
            st.markdown('<div class="assistant-label">Legal Lens</div>', unsafe_allow_html=True)
            st.markdown(msg["answer"])
            render_sources(msg.get("sections", []))

# -----------------------------
# Input
# -----------------------------
user_input = st.chat_input("Message Legal Lens...")
active_prompt = example_prompt or user_input

if active_prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": active_prompt
    })

    with st.chat_message("user"):
        st.markdown('<span class="msg-user"></span>', unsafe_allow_html=True)
        st.markdown(active_prompt)

    with st.chat_message("assistant", avatar="⚖️"):
        st.markdown('<span class="msg-assistant"></span>', unsafe_allow_html=True)
        st.markdown('<div class="assistant-label">Legal Lens</div>', unsafe_allow_html=True)

        with st.spinner("Legal Lens is thinking..."):
            raw_result = model_generate(active_prompt)
            answer, sections = normalize_result(raw_result)

        st.markdown(answer)
        render_sources(sections)

    st.session_state.messages.append({
        "role": "assistant",
        "answer": answer,
        "sections": sections
    })

# -----------------------------
# Footer credit
# -----------------------------
st.markdown(
    '<div class="credit-footer">Created by Akshit Raj</div>',
    unsafe_allow_html=True
)

