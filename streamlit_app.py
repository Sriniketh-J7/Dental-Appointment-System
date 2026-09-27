"""
Streamlit chat UI for the Dental Appointment Management System.
Thin wrapper — all agent logic lives in dental_agent/, untouched.
"""

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage, AIMessage
from dental_agent.agent import dental_graph

st.set_page_config(page_title="Dental Appointment Assistant", page_icon="🦷")

st.title("🦷 Dental Appointment Assistant")
st.caption("Multi-agent system powered by LangGraph + Grok-4 (xAI)")

with st.expander("Example things you can ask"):
    st.markdown(
        """
- Show available slots for an orthodontist
- Book patient 1000082 with Emily Johnson on 5/10/2026 9:00
- What appointments does patient 1000048 have?
- Cancel appointment for patient 1000082 at 5/10/2026 9:00
- Reschedule patient 1000082 from 5/10/2026 9:00 to 5/12/2026 10:00
"""
    )

if "history" not in st.session_state:
    st.session_state.history = []

# Render past turns
for msg in st.session_state.history:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.write(msg.content)

user_input = st.chat_input("Type a message...")

if user_input:
    st.session_state.history.append(HumanMessage(content=user_input))
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        response_text = ""
        final_messages = None

        try:
            for event_type, data in dental_graph.stream(
                {"messages": st.session_state.history},
                stream_mode=["messages", "values"],
                config={"recursion_limit": 20},
            ):
                if event_type == "messages":
                    chunk, meta = data
                    if (
                        isinstance(chunk, AIMessage)
                        and chunk.content
                        and not getattr(chunk, "tool_calls", None)
                    ):
                        response_text += chunk.content
                        placeholder.write(response_text)
                elif event_type == "values":
                    final_messages = data.get("messages", [])
        except Exception as exc:
            placeholder.error(f"Error: {exc}")
            st.session_state.history.pop()
            st.stop()

        if final_messages:
            st.session_state.history = final_messages
