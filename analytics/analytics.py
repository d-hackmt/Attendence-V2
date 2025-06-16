# analytics.py

import streamlit as st
import os
import pandas as pd
import re
import matplotlib.pyplot as plt

def show_analytics_panel():
    st.header("📊 Attendance Analytics")

    class_dir = "classes"
    os.makedirs(class_dir, exist_ok=True)
    class_files = [f for f in os.listdir(class_dir) if f.endswith(".csv")]
    if not class_files:
        st.warning("No class CSVs found in 'classes/' folder.")
        return

    selected_file = st.selectbox("Select class for analytics", class_files, key="analytics_class_select")

    if selected_file:
        file_path = os.path.join(class_dir, selected_file)
        df = pd.read_csv(file_path)

        df.columns = df.columns.str.strip()
        if "Roll Number" not in df.columns or "Name" not in df.columns:
            st.error("CSV format error: 'Roll Number' and 'Name' columns are required.")
            return

        st.dataframe(df, use_container_width=True)

        date_cols = sorted([col for col in df.columns if re.match(r"\d{4}-\d{2}-\d{2}", col)])
        if not date_cols:
            st.warning("No attendance dates found in the CSV.")
            return

        total_lectures = len(date_cols)
        df["Present_Count"] = df[date_cols].apply(lambda row: sum(val == "P" for val in row), axis=1)
        df["Attendance %"] = (df["Present_Count"] / total_lectures * 100).round(2)

        st.subheader("📈 Total Attendance (Top 30 Students)")
        top_chart_data = df[["Name", "Present_Count"]].nlargest(30, "Present_Count").set_index("Name")
        st.bar_chart(top_chart_data)

        st.subheader("🏆 Top 3 Students (by Attendance %)")
        st.table(df.sort_values("Attendance %", ascending=False).head(3)[["Name", "Present_Count", "Attendance %"]])

        st.subheader("⚠️ Bottom 3 Students (by Attendance %)")
        st.table(df.sort_values("Attendance %").head(3)[["Name", "Present_Count", "Attendance %"]])

        st.subheader("🎯 Filter Students by Attendance Range (%)")
        min_val, max_val = float(df["Attendance %"].min()), float(df["Attendance %"].max())
        selected_range = st.slider("Select attendance percentage range", min_value=0.0, max_value=100.0,
                                   value=(min_val, max_val), step=1.0)

        filtered_df = df[(df["Attendance %"] >= selected_range[0]) & (df["Attendance %"] <= selected_range[1])]
        st.markdown(f"Showing **{len(filtered_df)}** students with attendance between **{selected_range[0]}%** and **{selected_range[1]}%**.")
        st.dataframe(filtered_df[["Name", "Roll Number", "Present_Count", "Attendance %"]].reset_index(drop=True), use_container_width=True)

        # 🟠 Pie Chart: Present vs Absent
        st.subheader("🥧 Overall Attendance Summary")

        # Flatten all date columns and count 'P' and empty entries
        flattened = df[date_cols].values.flatten()
        present_count = sum(val == "P" for val in flattened)
        absent_count = sum(val != "P" and val != "" for val in flattened) + sum(val == "" for val in flattened)

        labels = ["Present", "Absent"]
        sizes = [present_count, absent_count]
        colors = ["#4CAF50", "#F44336"]

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)
