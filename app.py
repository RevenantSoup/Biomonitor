import pandas as pd
import streamlit as st

st.set_page_config(page_title="Bio-Monitor Dashboard", page_icon="🩺", layout="wide")

st.title("🩺 Bio-Monitor Dashboard")
st.caption("Week 3: patient selection, vital-sign charts, and Priority 1 warnings")

# Load and clean the patient data
df = pd.read_csv("bio_monitor_week1_sample_vitals.csv")
df_clean = df.dropna().sort_values(["patient_id", "time_minute"])

# Let the user select a patient
patient_ids = sorted(df_clean["patient_id"].unique())
selected_patient = st.selectbox("Select a patient", patient_ids)

patient_data = df_clean[df_clean["patient_id"] == selected_patient].copy()
latest = patient_data.iloc[-1]

heart_rate = float(latest["heart_rate_bpm"])
oxygen = float(latest["oxygen_saturation_percent"])
systolic = float(latest["systolic_bp_mmhg"])
diastolic = float(latest["diastolic_bp_mmhg"])

# Priority 1 rules from the project
priority_1_reasons = []

if heart_rate < 50:
    priority_1_reasons.append("Heart rate is below 50 bpm")
elif heart_rate > 120:
    priority_1_reasons.append("Heart rate is above 120 bpm")

if oxygen < 92:
    priority_1_reasons.append("Oxygen saturation is below 92%")

if systolic > 150 or diastolic > 95:
    priority_1_reasons.append("Blood pressure is above 150/95 mmHg")

# Display the current status
if priority_1_reasons:
    st.error("🚨 PRIORITY 1 ALERT: " + " | ".join(priority_1_reasons))
else:
    st.success("✅ Current readings are within the project thresholds")

# Display the latest readings
col1, col2, col3, col4 = st.columns(4)
col1.metric("Heart Rate", f"{heart_rate:.0f} bpm")
col2.metric("Oxygen Saturation", f"{oxygen:.0f}%")
col3.metric("Systolic BP", f"{systolic:.0f} mmHg")
col4.metric("Diastolic BP", f"{diastolic:.0f} mmHg")

# Interactive line charts
st.subheader("Heart Rate Over Time")
st.line_chart(
    patient_data.set_index("time_minute")[["heart_rate_bpm"]],
    x_label="Time (minutes)",
    y_label="Heart rate (bpm)",
)

st.subheader("Oxygen Saturation Over Time")
st.line_chart(
    patient_data.set_index("time_minute")[["oxygen_saturation_percent"]],
    x_label="Time (minutes)",
    y_label="Oxygen saturation (%)",
)

st.subheader("Patient Timeline")
st.dataframe(patient_data, use_container_width=True, hide_index=True)
