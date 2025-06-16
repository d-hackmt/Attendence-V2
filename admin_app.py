import streamlit as st
from core.admin import show_admin_panel
from core.chatbot import show_chatbot_panel
from analytics.analytics import show_analytics_panel
import os

st.set_page_config(page_title="Admin Dashboard", layout="centered")

# --- Ensure necessary files and folders exist ---
if not os.path.exists("refresh_trigger.txt"):
    with open("refresh_trigger.txt", "w") as f:
        f.write("init")

if not os.path.exists("classes"):
    os.makedirs("classes")

# --- Initialize session state ---
for key in ["attendance_status", "attendance_codes", "attendance_limits", "admin_logged_in"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "admin_logged_in" else {}

# --- Show login or dashboard tabs ---
if not st.session_state.admin_logged_in:
    show_admin_panel()  # Includes login UI
else:
    tab1, tab2, tab3 = st.tabs(["🗂️ Admin Panel", "🤖 Chatbot Panel", "📊 Analytics"])
    with tab1:
        show_admin_panel()
    with tab2:
        show_chatbot_panel()
    with tab3:
        show_analytics_panel()
