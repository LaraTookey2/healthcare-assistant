import time
import pandas as pd
import streamlit as st

from src.agents.coordinator import CoordinatorAgent


# =============================================================================
# Page Setup
# =============================================================================

st.set_page_config(
    page_title="Agentic Healthcare Assistant",
    page_icon="🏥",
    layout="wide"
)


# =============================================================================
# Load Agent
# =============================================================================

@st.cache_resource
def load_agent():
    return CoordinatorAgent()


agent = load_agent()


# =============================================================================
# Session State
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "metrics" not in st.session_state:
    st.session_state.metrics = []

if "patient_id" not in st.session_state:
    st.session_state.patient_id = "P001"


# =============================================================================
# Header
# =============================================================================

st.title("🏥 Agentic Healthcare Assistant")
st.caption("Patient dashboard for appointments, records, medications, lab results, medical search, and evaluation metrics")


# =============================================================================
# Sidebar
# =============================================================================

with st.sidebar:
    st.header("👤 Patient")
    st.write("**Logged in as:** Sarah Johnson")
    st.write("**Patient ID:** P001")

    st.divider()

    st.header("⚡ Quick Actions")

    quick_prompt = None

    if st.button("📅 Show appointments"):
        quick_prompt = "Show me my appointments"

    if st.button("💊 Show medications"):
        quick_prompt = "What are my current medications?"

    if st.button("🧪 Show lab results"):
        quick_prompt = "Show me my lab results"

    if st.button("📋 Health summary"):
        quick_prompt = "Give me a summary of my health"

    if st.button("🕐 Check cardiologist availability"):
        quick_prompt = "Check availability for cardiologist"

    if st.button("🔎 Search diabetes information"):
        quick_prompt = "What is diabetes?"

    st.divider()

    if st.button("🧹 Clear chat and metrics"):
        st.session_state.messages = []
        st.session_state.metrics = []
        st.rerun()


# =============================================================================
# Tabs
# =============================================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Assistant Chat",
    "📅 Appointment Demo",
    "📊 Evaluation Metrics",
    "ℹ️ Help"
])


# =============================================================================
# Tab 1: Chat
# =============================================================================

with tab1:
    st.subheader("Chat with your healthcare assistant")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input(
        "Ask about appointments, medications, records, lab results, or medical topics..."
    )

    if quick_prompt:
        user_input = quick_prompt

    if user_input:
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                start_time = time.time()

                response = agent.process(
                    user_input,
                    st.session_state.patient_id
                )

                response_time = round(time.time() - start_time, 3)
                trace = getattr(agent, "last_trace", {})

                st.session_state.metrics.append({
                    "prompt": user_input,
                    "intent": trace.get("intent", "unknown"),
                    "agent": trace.get("agent", "unknown"),
                    "success": trace.get("success", False),
                    "response_time_sec": response_time,
                    "message": trace.get("message", "")
                })

                st.markdown(response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })


# =============================================================================
# Tab 2: Appointment Demo
# =============================================================================

with tab2:
    st.subheader("📅 Appointment booking examples")

    st.write("Try these prompts in the chat:")

    st.code("Show me my appointments")
    st.code("Check availability for cardiologist")
    st.code("Book me with a cardiologist tomorrow at 10:00 AM for chest pain follow-up")
    st.code("Confirm appointment A001")
    st.code("Cancel appointment A001")

    st.info(
        "Tip: First ask 'Show me my appointments' to see the correct appointment ID, "
        "then use that ID for confirmation or cancellation."
    )


# =============================================================================
# Tab 3: Evaluation / LLMOps Metrics
# =============================================================================

with tab3:
    st.subheader("📊 Evaluation / LLMOps Metrics")

    if st.session_state.metrics:
        df = pd.DataFrame(st.session_state.metrics)

        total_requests = len(df)
        successful_requests = int(df["success"].sum())
        failed_requests = total_requests - successful_requests
        success_rate = round((successful_requests / total_requests) * 100, 2)
        avg_response_time = round(df["response_time_sec"].mean(), 3)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Requests", total_requests)
        col2.metric("Success Rate", f"{success_rate}%")
        col3.metric("Avg Response Time", f"{avg_response_time}s")
        col4.metric("Failed Requests", failed_requests)

        st.divider()

        st.write("### Intent / Agent Trace Log")
        st.dataframe(df, use_container_width=True)

        st.write("### Requests by Agent")
        st.bar_chart(df["agent"].value_counts())

        st.write("### Requests by Intent")
        st.bar_chart(df["intent"].value_counts())

        st.write("### Success vs Failure")
        success_df = df["success"].value_counts().rename(index={
            True: "Success",
            False: "Failure"
        })
        st.bar_chart(success_df)

    else:
        st.info("No metrics yet. Use the chat to generate evaluation logs.")


# =============================================================================
# Tab 4: Help
# =============================================================================

with tab4:
    st.subheader("ℹ️ What this assistant can do")

    st.markdown("""
    ### Core Features

    - 📅 Book, view, confirm, and cancel appointments
    - 💊 Show current medications
    - 🧪 Show lab results and abnormal result alerts
    - 📋 Retrieve medical history
    - 🧠 Maintain patient context during the session
    - 🔎 Search trusted medical information from MedlinePlus
    - 📊 Track evaluation metrics such as intent, agent used, success/failure, and response time

    ### Example Prompts

    **Appointments**
    - Show me my appointments
    - Check availability for cardiologist
    - Book me with a cardiologist tomorrow at 10:00 AM
    - Cancel appointment A001

    **Medical Records**
    - What are my current medications?
    - Show me my lab results
    - What conditions do I have?
    - Give me a summary of my health

    **Medical Search**
    - What is diabetes?
    - Tell me about hypertension
    - What are symptoms of asthma?
    """)

    st.warning(
        "This prototype uses mock patient data and provides general health information only. "
        "It is not a substitute for professional medical advice."
    )