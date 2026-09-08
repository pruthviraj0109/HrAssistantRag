"""
Simple Streamlit UI for the HR Policy Assistant.
Talks to the FastAPI backend running at API_BASE_URL.

Run with:
    streamlit run ui/app.py
(Make sure the FastAPI server is also running: uvicorn api.main:app --reload)
"""

import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="HR Policy Assistant", page_icon="📄")
st.title("📄 HR Policy Assistant")

# --- Session state for chat display (separate from the backend's own memory) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar: document upload ---
with st.sidebar:
    st.header("Upload HR Policy Document")
    uploaded_file = st.file_uploader("Choose a PDF, DOCX, or TXT file", type=["pdf", "docx", "txt"])

    if uploaded_file is not None:
        if st.button("Upload & Ingest"):
            with st.spinner("Uploading and processing document..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                try:
                    response = requests.post(f"{API_BASE_URL}/upload", files=files)
                    if response.status_code == 200:
                        st.success(f"'{uploaded_file.name}' uploaded and indexed successfully.")
                    else:
                        st.error(f"Upload failed: {response.json().get('detail')}")
                except requests.exceptions.ConnectionError:
                    st.error("Could not reach the API. Is the FastAPI server running?")

    st.divider()
    if st.button("Reset Conversation"):
        try:
            requests.post(f"{API_BASE_URL}/reset")
            st.session_state.messages = []
            st.success("Conversation reset.")
        except requests.exceptions.ConnectionError:
            st.error("Could not reach the API. Is the FastAPI server running?")

# --- Chat display ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- Chat input ---
question = st.chat_input("Ask a question about HR policy...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(f"{API_BASE_URL}/chat", json={"question": question})
                if response.status_code == 200:
                    answer = response.json()["answer"]
                else:
                    answer = f"Error: {response.json().get('detail')}"
            except requests.exceptions.ConnectionError:
                answer = "Could not reach the API. Is the FastAPI server running?"

            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})