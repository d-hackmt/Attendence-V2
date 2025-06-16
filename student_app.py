# student_app.py

import streamlit as st
from core.student import show_student_panel
import os

st.set_page_config(page_title="Student Attendance", layout="centered")

# Ensure refresh trigger file exists
if not os.path.exists("refresh_trigger.txt"):
    with open("refresh_trigger.txt", "w") as f:
        f.write("init")

# Defensive session state init
for key in ["attendance_status", "attendance_codes", "attendance_limits"]:
    if key not in st.session_state:
        st.session_state[key] = {}

show_student_panel()
