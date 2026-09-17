"""
Streamlit UI for the Multi-Domain RAG Assistant.
Talks to the FastAPI backend running at API_BASE_URL.

Run with:
    streamlit run ui/app.py
(Make sure the FastAPI server is also running: uvicorn api.main:app --reload)
"""

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
    "employee_support": "💬 Employee Support Agent",
}

st.set_page_config(page_title="Multi-Domain RAG Assistant", page_icon="🤖")
st.title("🤖 Multi-Domain RAG Assistant")

# --- Session state ---
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "hr_assistant_messages" not in st.session_state:
    st.session_state.hr_assistant_messages = []


# --- Login / Register screen (shown until authenticated) ---
def show_auth_screen():
    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

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
                    st.error(response.json().get("detail", "Login failed."))
            except requests.exceptions.ConnectionError:
                st.error("Could not reach the API. Is the FastAPI server running?")

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
                        "Registered successfully — now log in from the Login tab. A default leave balance has been set up for you."
                    )
                else:
                    st.error(response.json().get("detail", "Registration failed."))
            except requests.exceptions.ConnectionError:
                st.error("Could not reach the API. Is the FastAPI server running?")


if not st.session_state.token:
    show_auth_screen()
    st.stop()

# --- Authenticated from here on ---
auth_headers = {"Authorization": f"Bearer {st.session_state.token}"}

with st.sidebar:
    st.caption(f"Logged in as **{st.session_state.username}**")
    if st.button("Logout"):
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.messages = []
        st.session_state.hr_assistant_messages = []
        st.rerun()

tab_domain_rag, tab_hr_assistant = st.tabs(
    ["📚 Domain RAG Assistant", "🧑‍💼 HR Assistant (Multi-Agent)"]
)

# =========================================================================
# TAB 1: Existing domain-based RAG assistant — UNCHANGED behavior
# =========================================================================
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
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/upload",
                            params={"domain": domain},
                            files=files,
                            headers=auth_headers,
                        )
                        if response.status_code == 200:
                            chunks = response.json().get("chunks_indexed", "?")
                            st.success(
                                f"'{uploaded_file.name}' indexed ({chunks} chunks)."
                            )
                        else:
                            st.error(f"Upload failed: {response.json().get('detail')}")
                    except requests.exceptions.ConnectionError:
                        st.error(
                            "Could not reach the API. Is the FastAPI server running?"
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
                st.error("Could not reach the API. Is the FastAPI server running?")

    st.caption(f"Domain: **{domain}**")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    question = st.chat_input(
        f"Ask a question about {domain}...", key="domain_chat_input"
    )

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/chat",
                        json={"domain": domain, "question": question},
                        headers=auth_headers,
                    )
                    if response.status_code == 200:
                        answer = response.json()["answer"]
                    elif response.status_code == 401:
                        answer = (
                            "Your session expired — please log out and log in again."
                        )
                    else:
                        answer = f"Error: {response.json().get('detail')}"
                except requests.exceptions.ConnectionError:
                    answer = "Could not reach the API. Is the FastAPI server running?"

                st.write(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

# =========================================================================
# TAB 2: NEW — Multi-agent HR assistant (Supervisor + Policy/Leave/Support)
# =========================================================================
with tab_hr_assistant:
    st.caption(
        "Ask about HR policy, your leave balance, or general HR support — the assistant routes your question automatically."
    )

    for msg in st.session_state.hr_assistant_messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and msg.get("agent"):
                st.caption(AGENT_LABELS.get(msg["agent"], msg["agent"]))
            st.write(msg["content"])

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
                    elif response.status_code == 401:
                        answer, agent = (
                            "Your session expired — please log out and log in again.",
                            None,
                        )
                    else:
                        answer, agent = f"Error: {response.json().get('detail')}", None
                except requests.exceptions.ConnectionError:
                    answer, agent = (
                        "Could not reach the API. Is the FastAPI server running?",
                        None,
                    )

                if agent:
                    st.caption(AGENT_LABELS.get(agent, agent))
                st.write(answer)
                st.session_state.hr_assistant_messages.append(
                    {"role": "assistant", "content": answer, "agent": agent}
                )
