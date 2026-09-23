import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000"

DOMAINS = [
    "hr",
    "healthcare",
    "banking",
    "news_media",
    "customer_support",
    "government_schemes",
]

AGENT_LABELS = {
    "hr_policy": "📄 HR Policy Agent",
    "leave_management": "🗓️ Leave Management Agent",
    "onboarding": "📋 Onboarding & Training Agent",
    "employee_support": "💬 Employee Support Agent",
}

TOKEN_LIMIT = 8000
TOKEN_WARN_THRESHOLD = 6000

# A tool call slower than this is worth seeing — retrieval is usually the
# cause, and it is the part of latency the user never otherwise notices.
SLOW_TOOL_MS = 1000

st.set_page_config(
    page_title="Multi-Domain RAG Assistant",
    page_icon="🤖",
)

st.markdown(
    """
    <style>
    .stApp { background: #ffffff; color: #202123; }

    .main .block-container {
        max-width: 1000px;
        padding-top: 1rem;
        padding-bottom: 6rem;
    }

    header[data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer { visibility: hidden; }

    section[data-testid="stSidebar"] {
        background: #f7f7f8;
        border-right: 1px solid #e5e5e5;
    }
    section[data-testid="stSidebar"] > div { background: #f7f7f8; }
    section[data-testid="stSidebar"] * { color: #202123; }

    h1 {
        color: #202123 !important;
        font-size: 1.55rem !important;
        font-weight: 600 !important;
    }
    h2, h3 { color: #202123 !important; }

    button[data-baseweb="tab"] { color: #6e6e80; font-size: 0.95rem; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #202123; }

    div[data-testid="stChatMessage"] {
        background: transparent;
        border: none;
        border-bottom: 1px solid transparent;
        padding-top: 0.75rem;
        padding-bottom: 0.75rem;
    }
    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        color: #202123;
        line-height: 1.65;
    }
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: #f7f7f8;
        border-radius: 14px;
        padding: 0.4rem 0.8rem;
        margin-left: auto;
        max-width: 78%;
    }
    div[data-testid="stChatMessage"]:has(
        [data-testid="chatAvatarIcon-assistant"]
    ) { max-width: 100%; }

    div[data-testid="stChatInput"] {
        background: #f7f7f8;
        border: 1px solid #d9d9e3;
        border-radius: 18px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
        position: fixed;
        bottom: 1.5rem;
        left: 50%;
        transform: translateX(-50%);
        width: min(1000px, 92%);
        z-index: 999;
    }
    div[data-testid="stChatInput"] textarea {
        color: #202123 !important;
        background: transparent !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #8b8b8b !important;
    }

    .stButton > button {
        background: #ffffff;
        color: #202123;
        border: 1px solid #414141;
        border-radius: 9px;
    }
    .stButton > button:hover {
        background: #ececf1;
        border-color: #c5c5d2;
        color: #202123;
    }

    div[data-baseweb="select"] > div, input, textarea {
        background-color: #ffffff !important;
        color: #202123 !important;
        border-color: #d9d9e3 !important;
    }

    div[data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 10px;
    }

    div[data-testid="stMetric"] {
        background: #f7f7f8;
        border: 1px solid #e5e5e5;
        border-radius: 9px;
        padding: 0.5rem;
    }
    div[data-testid="stMetricLabel"] { color: #6e6e80 !important; }
    div[data-testid="stMetricValue"] { color: #202123 !important; }

    .agent-badge, .model-badge {
        display: inline-block;
        background: #f7f7f8;
        border: 1px solid #d9d9e3;
        color: #565869;
        border-radius: 999px;
        padding: 0.28rem 0.7rem;
        font-size: 0.76rem;
    }
    .model-dot { color: #10a37f; }

    .chat-welcome { text-align: center; padding: 7rem 1rem 4rem 1rem; }
    .chat-welcome-title {
        font-size: 1.8rem; font-weight: 600; color: #202123;
    }
    .chat-welcome-subtitle { color: #6e6e80; margin-top: 0.4rem; }

    .stMarkdown, .stCaption, label, p { color: #202123; }
    .stCaption { color: #6e6e80 !important; }

    div[data-testid="stFileUploader"] {
        background: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 10px;
        padding: 0.35rem;
    }

    .tool-time {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.45rem 0.7rem;
        margin: 0.25rem 0;
        background: #f7f7f8;
        border: 1px solid #e5e5e5;
        border-left: 3px solid #10a37f;
        border-radius: 8px;
        font-size: 0.85rem;
        color: #565869;
    }
    .tool-time.slow { border-left-color: #d97706; }
    .tool-time .ms { font-variant-numeric: tabular-nums; color: #202123; }

    .metric-error {
        padding: 0.45rem 0.7rem;
        margin: 0.25rem 0;
        background: #fdf2f2;
        border: 1px solid #f3c9c9;
        border-left: 3px solid #c00000;
        border-radius: 8px;
        font-size: 0.85rem;
        color: #7a1c1c;
    }

    @media (max-width: 700px) {
        .main .block-container {
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }
        div[data-testid="stChatMessage"]:has(
            [data-testid="chatAvatarIcon-user"]
        ) { max-width: 92%; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🤖 Multi-Domain RAG Assistant")

# --------------------------------------------------------------- state
for key, default in [
    ("token", None),
    ("username", None),
    ("messages", []),
    ("hr_assistant_messages", []),
    ("session_tokens", 0),
    ("session_turns", 0),
    ("session_latency_ms", 0),
    ("session_tool_calls", 0),
    ("session_tool_execution_ms", 0),
    ("session_errors", 0),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ======================================================================
# Metrics
# ======================================================================
def render_metrics(metrics):
    if not metrics:
        return

    total = metrics.get("total_tokens", 0)
    latency = metrics.get("latency_ms", 0)
    tools = metrics.get("tools_used") or []
    tool_calls = metrics.get("tool_calls", 0)
    llm_calls = metrics.get("llm_calls", 0)
    tool_ms = metrics.get("tool_execution_time_ms", 0) or 0
    executions = metrics.get("tool_executions") or []
    errors = metrics.get("errors") or []
    model = metrics.get("model") or "unknown"

    warn = "⚠️ " if total >= TOKEN_WARN_THRESHOLD else ""
    summary = f"{warn}{total:,} tokens · {latency / 1000:.2f}s · 🤖 {model}"
    if tool_calls:
        summary += f" · 🔧 {tool_calls} tool call(s)"
    if errors:
        summary += f" · ❌ {len(errors)} error(s)"
    st.caption(summary)

    with st.expander("Run details", expanded=False):

        c1, c2, c3 = st.columns(3)
        c1.metric("Input tokens", f"{metrics.get('input_tokens', 0):,}")
        c2.metric("Output tokens", f"{metrics.get('output_tokens', 0):,}")
        c3.metric("Total tokens", f"{total:,}")

        c4, c5, c6 = st.columns(3)
        c4.metric("Latency", f"{latency / 1000:.2f}s")
        c5.metric("LLM calls", llm_calls)
        c6.metric("Tool calls", tool_calls)

        # ---------------------------------------------------- tool time
        if tool_calls:
            st.divider()
            st.markdown("**🔧 Tool execution**")

            # how much of the wall-clock time was spent in tools rather
            # than waiting on the model — the useful split
            share = (tool_ms / latency * 100) if latency else 0

            t1, t2, t3 = st.columns(3)
            t1.metric("Total tool time", f"{tool_ms:,} ms")
            t2.metric("Share of latency", f"{share:.0f}%")
            t3.metric(
                "Model time",
                f"{max(latency - tool_ms, 0) / 1000:.2f}s",
            )

            if executions:
                for ex in executions:
                    name = ex.get("tool", "unknown_tool")
                    ms = ex.get("execution_time_ms", 0)

                    # a negative or absurd value means the timing maths is
                    # wrong upstream, not that the tool was instant
                    if ms < 0:
                        st.markdown(
                            f'<div class="metric-error">⚠️ '
                            f"<strong>{name}</strong> reported {ms:,} ms — "
                            "check the on_tool_end timing calculation."
                            "</div>",
                            unsafe_allow_html=True,
                        )
                        continue

                    slow = " slow" if ms >= SLOW_TOOL_MS else ""
                    st.markdown(
                        f'<div class="tool-time{slow}">'
                        f"<span>🔧 <strong>{name}</strong></span>"
                        f'<span class="ms">{ms:,} ms</span>'
                        "</div>",
                        unsafe_allow_html=True,
                    )

            if tools:
                st.caption(
                    "Tools used: " + ", ".join(f"`{t}`" for t in tools)
                )

        # ------------------------------------------------------- errors
        if errors:
            st.divider()
            st.markdown("**❌ Failed calls**")
            for err in errors:
                where = err.get("source") or err.get("tool") or "llm"
                message = err.get("error") or err.get("message") or "unknown"
                st.markdown(
                    f'<div class="metric-error">'
                    f"<strong>{where}</strong> — {message}"
                    "</div>",
                    unsafe_allow_html=True,
                )

        # -------------------------------------------------- token budget
        st.divider()
        st.caption(f"Model: `{model}`")

        if total:
            st.progress(
                min(total / TOKEN_LIMIT, 1.0),
                text=(
                    f"{total:,} of the {TOKEN_LIMIT:,} tokens-per-minute limit"
                ),
            )

        if total >= TOKEN_WARN_THRESHOLD:
            st.warning(
                f"This request used {total:,} tokens against a "
                f"{TOKEN_LIMIT:,} per-minute limit. Ask a shorter follow-up, "
                "or reset the conversation, to avoid a rate-limit error."
            )


def record_metrics(metrics):
    if not metrics:
        return
    st.session_state.session_tokens += metrics.get("total_tokens", 0)
    st.session_state.session_latency_ms += metrics.get("latency_ms", 0)
    st.session_state.session_tool_calls += metrics.get("tool_calls", 0)
    st.session_state.session_tool_execution_ms += (
        metrics.get("tool_execution_time_ms", 0) or 0
    )
    st.session_state.session_errors += len(metrics.get("errors") or [])
    st.session_state.session_turns += 1


def replay_history(messages):
    for msg in messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and msg.get("agent"):
                st.markdown(
                    f'<span class="agent-badge">'
                    f'{AGENT_LABELS.get(msg["agent"], msg["agent"])}</span>',
                    unsafe_allow_html=True,
                )
            st.write(msg["content"])
            if msg["role"] == "assistant":
                render_metrics(msg.get("metrics"))


# ======================================================================
# Auth
# ======================================================================
def show_auth_screen():
    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        username = st.text_input("Username", key="login_username")
        password = st.text_input(
            "Password", type="password", key="login_password"
        )

        if st.button("Login", key="login_btn"):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/login",
                    data={"username": username, "password": password},
                )
                if response.status_code == 200:
                    st.session_state.token = response.json()["access_token"]
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error(
                        response.json().get("detail", "Login failed.")
                    )
            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not reach the API. Is the FastAPI server running?"
                )

    with tab_register:
        new_username = st.text_input("Choose a username", key="reg_username")
        new_password = st.text_input(
            "Choose a password",
            type="password",
            key="reg_password",
            help="At least 8 characters, with an uppercase letter and a number.",
        )

        if st.button("Register", key="register_btn"):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/register",
                    json={"username": new_username, "password": new_password},
                )
                if response.status_code == 201:
                    st.success(
                        "Registered successfully — now log in from the Login "
                        "tab. A default leave balance has been set up for you."
                    )
                else:
                    st.error(
                        response.json().get("detail", "Registration failed.")
                    )
            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not reach the API. Is the FastAPI server running?"
                )


if not st.session_state.token:
    show_auth_screen()
    st.stop()

auth_headers = {"Authorization": f"Bearer {st.session_state.token}"}


# ======================================================================
# Sidebar
# ======================================================================
with st.sidebar:
    st.caption(f"Logged in as **{st.session_state.username}**")

    if st.session_state.session_turns:
        turns = st.session_state.session_turns

        st.divider()
        st.caption("This session")

        a, b = st.columns(2)
        a.metric("Turns", turns)
        b.metric("Tokens", f"{st.session_state.session_tokens:,}")

        avg_tokens = st.session_state.session_tokens / turns
        avg_latency = st.session_state.session_latency_ms / turns / 1000
        st.caption(
            f"~{avg_tokens:,.0f} tokens · {avg_latency:.2f}s per turn on average"
        )

        if st.session_state.session_tool_calls:
            st.divider()
            st.caption("Tool usage")
            t1, t2 = st.columns(2)
            t1.metric("Tool calls", st.session_state.session_tool_calls)
            t2.metric(
                "Tool time",
                f"{st.session_state.session_tool_execution_ms:,} ms",
            )

        if st.session_state.session_errors:
            st.divider()
            st.metric("Failed calls", st.session_state.session_errors)

    if st.button("Logout"):
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.messages = []
        st.session_state.hr_assistant_messages = []
        st.session_state.session_tokens = 0
        st.session_state.session_turns = 0
        st.session_state.session_latency_ms = 0
        st.session_state.session_tool_calls = 0
        st.session_state.session_tool_execution_ms = 0
        st.session_state.session_errors = 0
        st.rerun()


tab_domain_rag, tab_hr_assistant = st.tabs(
    ["📚 Domain RAG Assistant", "🧑‍💼 HR Assistant (Multi-Agent)"]
)


# ======================================================================
# TAB 1 — Domain RAG
# ======================================================================
with tab_domain_rag:
    with st.sidebar:
        st.divider()
        domain = st.selectbox("Choose RAG domain", DOMAINS, key="domain_select")

        st.header("Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a PDF, DOCX, or TXT file",
            type=["pdf", "docx", "txt"],
            key="domain_upload",
        )

        if uploaded_file is not None:
            if st.button("Upload & Ingest", key="domain_upload_btn"):
                with st.spinner("Uploading and processing document..."):
                    files = {
                        "file": (uploaded_file.name, uploaded_file.getvalue())
                    }
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/upload",
                            params={"domain": domain},
                            files=files,
                            headers=auth_headers,
                        )
                        if response.status_code == 200:
                            result = response.json().get("result") or {}
                            chunks = (
                                result.get("chunks_indexed")
                                or response.json().get("chunks_indexed")
                                or "?"
                            )
                            st.success(
                                f"'{uploaded_file.name}' indexed "
                                f"({chunks} chunks)."
                            )
                        else:
                            st.error(
                                f"Upload failed: {response.json().get('detail')}"
                            )
                    except requests.exceptions.ConnectionError:
                        st.error(
                            "Could not reach the API. "
                            "Is the FastAPI server running?"
                        )

        st.divider()
        if st.button("Reset Conversation", key="domain_reset_btn"):
            try:
                requests.post(
                    f"{API_BASE_URL}/reset",
                    params={"domain": domain},
                    headers=auth_headers,
                )
                st.session_state.messages = []
                st.success("Conversation reset.")
            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not reach the API. Is the FastAPI server running?"
                )

    st.caption(f"Domain: **{domain}**")

    if not st.session_state.messages:
        st.markdown(
            f"""
            <div class="chat-welcome">
                <div class="chat-welcome-title">Where should we begin?</div>
                <div class="chat-welcome-subtitle">
                    Ask anything about your {domain} documents
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    replay_history(st.session_state.messages)

    question = st.chat_input(
        f"Ask a question about {domain}...", key="domain_chat_input"
    )

    if question:
        st.session_state.messages.append(
            {"role": "user", "content": question}
        )
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                metrics = None
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/chat",
                        json={"domain": domain, "question": question},
                        headers=auth_headers,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        answer = data["answer"]
                        metrics = data.get("metrics")
                    elif response.status_code == 401:
                        answer = (
                            "Your session expired — please log out and "
                            "log in again."
                        )
                    else:
                        answer = f"Error: {response.json().get('detail')}"
                except requests.exceptions.ConnectionError:
                    answer = (
                        "Could not reach the API. Is the FastAPI server running?"
                    )

                st.write(answer)
                render_metrics(metrics)
                record_metrics(metrics)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "metrics": metrics,
                    }
                )


# ======================================================================
# TAB 2 — Multi-agent HR assistant
# ======================================================================
with tab_hr_assistant:
    st.caption(
        "Ask about HR policy, your leave balance, your onboarding checklist, "
        "or general HR support — the assistant routes your question "
        "automatically."
    )

    if not st.session_state.hr_assistant_messages:
        st.markdown(
            """
            <div class="chat-welcome">
                <div class="chat-welcome-title">How can I help you?</div>
                <div class="chat-welcome-subtitle">
                    HR Policy · Leave · Onboarding · Employee Support
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    replay_history(st.session_state.hr_assistant_messages)

    hr_question = st.chat_input(
        "Ask the HR assistant...", key="hr_assistant_chat_input"
    )

    if hr_question:
        st.session_state.hr_assistant_messages.append(
            {"role": "user", "content": hr_question}
        )
        with st.chat_message("user"):
            st.write(hr_question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                metrics = None
                agent = None
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/chat/hr-assistant",
                        json={"message": hr_question},
                        headers=auth_headers,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        answer = data["answer"]
                        agent = data.get("agent")
                        metrics = data.get("metrics")
                    elif response.status_code == 401:
                        answer = (
                            "Your session expired — please log out and "
                            "log in again."
                        )
                    else:
                        answer = f"Error: {response.json().get('detail')}"
                except requests.exceptions.ConnectionError:
                    answer = (
                        "Could not reach the API. Is the FastAPI server running?"
                    )

                if agent:
                    st.markdown(
                        f'<span class="agent-badge">'
                        f"{AGENT_LABELS.get(agent, agent)}</span>",
                        unsafe_allow_html=True,
                    )

                st.write(answer)
                render_metrics(metrics)
                record_metrics(metrics)

                st.session_state.hr_assistant_messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "agent": agent,
                        "metrics": metrics,
                    }
                )