import os
import pickle
import pandas as pd
from datetime import datetime

REFRESH_FILE = "refresh_trigger.txt"
STATE_FILE = "streamlit_session.pkl"

def load_admin_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            return {"error": f"Error loading portal state: {e}"}
    return {"error": "Portal state file not found."}

def get_class_list():
    classes_dir = "classes"
    if not os.path.exists(classes_dir):
        return []
    return [f.replace(".csv", "") for f in os.listdir(classes_dir) if f.endswith(".csv")]

def should_refresh(last_refresh: str):
    if os.path.exists(REFRESH_FILE):
        with open(REFRESH_FILE, "r") as f:
            current_value = f.read().strip()
        return current_value if current_value != last_refresh else None
    return None

def read_class_csv(file_path):
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=["Roll Number", "Name"])
    try:
        return pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=["Roll Number", "Name"])


def mark_attendance(df, roll, name, current_date):
    # Ensure Roll Number is string for consistent matching
    roll = str(roll)
    df["Roll Number"] = df["Roll Number"].astype(str)

    student_row_index = df[df["Roll Number"] == roll].index

    # 1. Already marked?
    if not student_row_index.empty:
        if df.loc[student_row_index[0], current_date] == 'P':
            return df, "already_marked"
        else:
            # Update attendance for existing student
            df.loc[student_row_index[0], current_date] = 'P'
            return df, "updated"

    # 2. New student — add row
    new_data = {"Roll Number": roll, "Name": name}
    for col in df.columns:
        if col not in ["Roll Number", "Name"]:
            new_data[col] = ""
    new_data[current_date] = 'P'
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    return df, "added"

