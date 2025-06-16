import os
import pickle
import pandas as pd
from datetime import datetime

STATE_FILE = "streamlit_session.pkl"
REFRESH_FILE = "refresh_trigger.txt"
CLASSES_DIR = "classes"

# Ensure the classes directory exists
os.makedirs(CLASSES_DIR, exist_ok=True)

def save_admin_state(st):
    admin_state = {
        "attendance_status": st.session_state.attendance_status,
        "attendance_codes": st.session_state.attendance_codes,
        "attendance_limits": st.session_state.attendance_limits
    }
    with open(STATE_FILE, "wb") as f:
        pickle.dump(admin_state, f)

def load_admin_state(st):
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "rb") as f:
                admin_state = pickle.load(f)
            return admin_state
        except Exception as e:
            st.error(f"Error loading admin state: {e}")
            return {
                "attendance_status": {},
                "attendance_codes": {},
                "attendance_limits": {}
            }
    else:
        return {
            "attendance_status": {},
            "attendance_codes": {},
            "attendance_limits": {}
        }

def get_class_list():
    return [f.replace(".csv", "") for f in os.listdir(CLASSES_DIR) if f.endswith(".csv")]

def create_classroom(class_name):
    file_path = os.path.join(CLASSES_DIR, f"{class_name}.csv")
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=["Roll Number", "Name"])
        df.to_csv(file_path, index=False)

def delete_classroom(class_name, st):
    file_path = os.path.join(CLASSES_DIR, f"{class_name}.csv")
    if os.path.exists(file_path):
        os.remove(file_path)
        for key in ["attendance_status", "attendance_codes", "attendance_limits"]:
            if class_name in st.session_state.get(key, {}):
                del st.session_state[key][class_name]
        save_admin_state(st)

def trigger_student_refresh():
    with open(REFRESH_FILE, "w") as f:
        f.write(datetime.now().isoformat())
