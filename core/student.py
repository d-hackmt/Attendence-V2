# student.py

import streamlit as st
import time
from datetime import datetime
import os
import pandas as pd

from utils.student_utils import (
    load_admin_state,
    get_class_list,
    should_refresh,
    read_class_csv,
    mark_attendance
)

def show_student_panel():
    st.title("📚 Student Attendance Portal")

    # Auto-refresh logic
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = ""
    refresh = should_refresh(st.session_state.last_refresh)
    if refresh:
        st.session_state.last_refresh = refresh
        st.rerun()
    time.sleep(1)

    class_list = get_class_list()
    if not class_list:
        st.warning("No classrooms available. Please contact admin.")
        return

    selected_class = st.selectbox("Select Your Class", class_list)

    st.subheader("📝 Mark Your Attendance")
    with st.form("attendance_form"):
        name = st.text_input("Full Name")
        roll = st.text_input("Roll Number")
        token = st.text_input("Attendance Token")

        submit = st.form_submit_button("Submit Attendance")

        if submit:
            if not name.strip() or not roll.strip() or not token.strip():
                st.warning("All fields are required.")
                return
            if not roll.isdigit():
                st.warning("Roll Number must be numeric.")
                return

            admin_state = load_admin_state()
            if "error" in admin_state:
                st.error(admin_state["error"])
                return

            status = admin_state.get("attendance_status", {})
            codes = admin_state.get("attendance_codes", {})
            limits = admin_state.get("attendance_limits", {})

            if not status.get(selected_class, False):
                st.error("❌ Attendance portal is currently CLOSED for this class.")
                return

            if token != codes.get(selected_class, ""):
                st.error("❌ Invalid token.")
                return

            file_path = os.path.join("classes", f"{selected_class}.csv")
            if not os.path.exists(file_path):
                st.error("❌ Classroom attendance file not found.")
                return

            current_date = datetime.now().strftime("%Y-%m-%d")
            df = read_class_csv(file_path)

            if "Roll Number" not in df.columns or "Name" not in df.columns:
                st.error("Attendance file format error.")
                return

            df["Roll Number"] = df["Roll Number"].astype(str)

            if current_date not in df.columns:
                df[current_date] = ""

            if limits.get(selected_class) is not None:
                present_count = (df[current_date] == 'P').sum()
                if present_count >= limits[selected_class]:
                    st.error("❌ Token limit reached. Attendance not recorded.")
                    return

            df, status = mark_attendance(df, roll, name, current_date)
            if status == "already_marked":
                st.warning("⚠️ You have already marked your attendance for today.")
                return
            else:
                st.success("✅ Attendance marked successfully!")

            try:
                df["Roll Number"] = df["Roll Number"].astype(int)
                df.sort_values(by="Roll Number", inplace=True)
                df["Roll Number"] = df["Roll Number"].astype(str)
            except ValueError:
                df.sort_values(by="Roll Number", inplace=True)

            df.to_csv(file_path, index=False)
            st.rerun()
