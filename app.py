import streamlit as st
import pandas as pd
import os
import glob

# ----------------------------
# Base directory (project root)
# ----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ----------------------------
# Find Excel file automatically
# inside reports/excel folder
# ----------------------------
excel_folder = os.path.join(BASE_DIR, "reports", "excel")

file_list = glob.glob(os.path.join(excel_folder, "*.xlsx"))

# Check if file exists
if len(file_list) == 0:
    st.error("No Excel file found in reports/excel folder")
    st.stop()

# Take latest file (recommended for automation projects)
file_path = file_list[0]

# ----------------------------
# Load Excel file
# ----------------------------
df = pd.read_excel(file_path)

# ----------------------------
# UI
# ----------------------------
st.title("Pharmacovigilance Dashboard (PV Automation)")

st.subheader("Loaded Report File")
st.write(file_path)

st.dataframe(df)

# ----------------------------
# KPIs (safe check)
# ----------------------------
st.subheader("Key Metrics")

st.write("Total Records:", len(df))

if "Seriousness" in df.columns:
    st.write("Serious Cases:", len(df[df["Seriousness"] == "Serious"]))
    st.write("Non-Serious Cases:", len(df[df["Seriousness"] == "Non-Serious"]))

    st.subheader("Seriousness Distribution")
    st.bar_chart(df["Seriousness"].value_counts())

# ----------------------------
# Country chart (if exists)
# ----------------------------
if "Country" in df.columns:
    st.subheader("Country-wise Cases")
    st.bar_chart(df["Country"].value_counts())