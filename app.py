import streamlit as st
import requests

st.set_page_config(page_title="Enterprise RAG Assistant", layout="wide")

st.title("Secure Enterprise RAG Portal")
st.write("Demonstrating real-time semantic caching, multi-tenant isolation, and background ingestion.")

st.sidebar.header("Identity & Access Management")
user_department = st.sidebar.selectbox(
    "Select Session Role Scope:",
    ["general", "engineering", "hr"]
)

st.sidebar.info(f"Current Data Isolation Partition: **{user_department.upper()}**")

tab1, tab2 = st.tabs(["AI Employee Portal", "Document Admin Panel"])

with tab1:
    st.subheader("Ask the Knowledge Base")
    user_query = st.text_input("Enter your question here:", placeholder="e.g., What is the corporate holiday policy?")
    
    if st.button("Submit Query", type="primary"):
        if user_query.strip():
            with st.spinner("Routing request down the microservice pipeline..."):
                try:
                    response = requests.post(
                        "http://localhost:8000/v1/query",
                        json={"prompt": user_query},
                        headers={"X-Department": user_department},
                    )
                except requests.exceptions.ConnectionError:
                    st.error("Backend is not reachable. Is uvicorn running on port 8000?")
                    st.stop()

                if response.status_code == 200:
                    payload = response.json()
                    st.chat_message("assistant").write(payload["data"]["answer"])

                    st.subheader("System Telemetry Metrics")
                    telemetry = payload["telemetry"]
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Request Resolution Status", telemetry['served_by'])
                    with col2:
                        st.metric("Total API Latency", f"{telemetry['total_processing_time_ms']:.2f} ms")
                else:
                    st.error(f"Backend error {response.status_code}: {response.json().get('detail', 'Unknown error')}")

with tab2:
    st.subheader("Upload Corporate Manuals (Background Processing)")
    doc_name = st.text_input("Document File Name:", placeholder="e.g., security_policy.txt")
    target_dept = st.selectbox("Assign Security Metadata Tag:", ["general", "engineering", "hr"])
    
    if st.button("Trigger Ingestion Process"):
        if doc_name.strip():
            try:
                response = requests.post(
                    f"http://localhost:8000/v1/documents?file_name={doc_name}&department={target_dept}"
                )
            except requests.exceptions.ConnectionError:
                st.error("Backend is not reachable. Is uvicorn running on port 8000?")
                st.stop()

            if response.status_code == 202:
                st.success("Background worker task launched successfully!")
                st.json(response.json())
            else:
                st.error(f"Backend error {response.status_code}: {response.json().get('detail', 'Unknown error')}")