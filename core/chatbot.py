import streamlit as st
import os
import pandas as pd
from utils.chatbot_utils import get_agent_for_df, AppState

def show_chatbot_panel():
    st.header("🤖 Chat with Attendance Data")

    # --- Step 1: Dropdown for Class Files from 'classes/' folder ---
    class_dir = "classes"
    os.makedirs(class_dir, exist_ok=True)
    class_files = [f for f in os.listdir(class_dir) if f.endswith(".csv")]
    if not class_files:
        st.warning("No class CSVs found in 'classes/' folder.")
        return

    selected_file = st.selectbox("Choose a classroom CSV", class_files, key="chatbot_class_select")

    if selected_file:
        file_path = os.path.join(class_dir, selected_file)
        df = pd.read_csv(file_path)
        st.dataframe(df, use_container_width=True)

        # --- Step 2: Setup Chatbot Agent for Selected File ---
        if (
            "chat_agent" not in st.session_state
            or st.session_state.get("active_file") != selected_file
        ):
            st.session_state.chat_agent = get_agent_for_df(df)
            st.session_state.active_file = selected_file
            st.session_state.chat_history = []

        # --- Step 3: Chat Interface ---
        question = st.text_input("Ask a question about this class")

        if question:
            question = question.strip()
            with st.spinner("Thinking..."):
                result = st.session_state.chat_agent.invoke(AppState(question=question))
                # Avoid duplicate if user presses Enter multiple times quickly
                if (
                    not st.session_state.chat_history
                    or st.session_state.chat_history[-1] != ("You", question)
                ):
                    st.session_state.chat_history.append(("You", question))
                    st.session_state.chat_history.append(("Bot", result["answer"]))

        # --- Step 4: Chat Display ---
        for role, message in st.session_state.chat_history:
            if role == "You":
                st.markdown(f"**🧑 You:** {message}")
            else:
                st.markdown(f"**🤖 Bot:** {message}")
