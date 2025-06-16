import streamlit as st
from datetime import datetime
import pandas as pd
import os

from utils.admin_utils import (
    save_admin_state, load_admin_state, get_class_list,
    create_classroom, delete_classroom, trigger_student_refresh
)

ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

def show_admin_panel():
    st.title("Admin Panel")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        st.subheader("Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                state = load_admin_state(st)
                st.session_state.attendance_status = state.get("attendance_status", {})
                st.session_state.attendance_codes = state.get("attendance_codes", {})
                st.session_state.attendance_limits = state.get("attendance_limits", {})
                st.success("Login successful!")
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")
        return

    if st.sidebar.button("Logout Admin"):
        st.session_state.admin_logged_in = False
        st.rerun()

    if "attendance_status" not in st.session_state:
        st.session_state.attendance_status = {}
    if "attendance_codes" not in st.session_state:
        st.session_state.attendance_codes = {}
    if "attendance_limits" not in st.session_state:
        st.session_state.attendance_limits = {}

    st.subheader("Manage Classrooms")
    col1, col2 = st.columns([2, 1])
    with col1:
        new_class = st.text_input("Add New Classroom")
    with col2:
        if st.button("Add Classroom"):
            if not new_class.strip():
                st.warning("Classroom name cannot be empty.")
            elif new_class.strip() in get_class_list():
                st.warning(f"Classroom '{new_class}' already exists.")
            else:
                create_classroom(new_class.strip())
                st.success(f"Classroom '{new_class}' created.")
                st.rerun()

    class_list = get_class_list()
    if not class_list:
        st.warning("No classrooms found.")
        return

    selected_class = st.selectbox("Select Classroom", class_list)

    if st.button("Delete Selected Classroom"):
        delete_classroom(selected_class, st)
        st.warning(f"Classroom '{selected_class}' deleted.")
        st.rerun()

    st.subheader(f"Attendance Control for '{selected_class}'")
    current_status = st.session_state.attendance_status.get(selected_class, False)
    st.info(f"Current Attendance Status: {'OPEN' if current_status else 'CLOSED'}")

    col_open, col_close = st.columns(2)
    with col_open:
        if st.button("Open Attendance"):
            st.session_state.attendance_status[selected_class] = True
            save_admin_state(st)
            trigger_student_refresh()
            st.success("Portal OPENED.")
            st.rerun()
    with col_close:
        if st.button("Close Attendance"):
            st.session_state.attendance_status[selected_class] = False
            save_admin_state(st)
            trigger_student_refresh()
            st.info("Portal CLOSED.")
            st.rerun()


    # Display current code and limit
    current_code = st.session_state.attendance_codes.get(selected_class, "")
    current_limit = st.session_state.attendance_limits.get(selected_class, 1) # Default to 1 if not set

    st.markdown(f"**Current Code:** `{current_code}`")
    st.markdown(f"**Current Limit:** `{current_limit}`")


    code = st.text_input("Set Attendance Code", value=st.session_state.attendance_codes.get(selected_class, ""))
    limit = st.number_input("Set Token Limit", value=st.session_state.attendance_limits.get(selected_class, 1), min_value=1)

    if st.button("Update Code & Limit"):
        st.session_state.attendance_codes[selected_class] = code
        st.session_state.attendance_limits[selected_class] = int(limit)
        save_admin_state(st)
        st.success("Updated.")
        st.rerun()

    st.subheader(f"Attendance for {selected_class}")
    path = os.path.join("classes", f"{selected_class}.csv")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            st.dataframe(df)
            st.download_button("Download Attendance CSV", df.to_csv(index=False), file_name=f"{selected_class}_attendance.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.warning("No attendance file found.")

