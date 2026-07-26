import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Bio-Monitor Alert System",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 750;
        margin-bottom: 0.15rem;
    }
    .subtitle {
        color: #a7adb8;
        font-size: 0.95rem;
        margin-bottom: 1.4rem;
    }
    .patient-card {
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
        padding: 18px 18px 14px 18px;
        background: rgba(255,255,255,0.035);
        min-height: 205px;
    }
    .patient-name {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .status-normal {
        color: #44d07b;
        font-weight: 700;
        font-size: 0.9rem;
        margin-bottom: 0.85rem;
    }
    .status-alert {
        color: #ff5c5c;
        font-weight: 800;
        font-size: 0.9rem;
        margin-bottom: 0.85rem;
    }
    .metric-label {
        color: #a7adb8;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.04rem;
    }
    .metric-value {
        font-size: 1.35rem;
        font-weight: 750;
        margin-bottom: 0.7rem;
    }
    .alert-banner {
        border-radius: 14px;
        padding: 16px 18px;
        background: rgba(255, 76, 76, 0.14);
        border: 1px solid rgba(255, 76, 76, 0.45);
        color: #ffd4d4;
        font-weight: 650;
        margin: 10px 0 18px 0;
    }
    .normal-banner {
        border-radius: 14px;
        padding: 16px 18px;
        background: rgba(68, 208, 123, 0.12);
        border: 1px solid rgba(68, 208, 123, 0.35);
        color: #d8ffe6;
        font-weight: 650;
        margin: 10px 0 18px 0;
    }
    .small-note {
        color: #9ca3af;
        font-size: 0.82rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


THRESHOLDS = {
    "low_heart_rate": 50,
    "high_heart_rate": 120,
    "low_oxygen": 92,
    "high_systolic_bp": 150,
    "high_diastolic_bp": 95,
}

PATIENT_BASELINES = {
    "Patient 1": {"heart": 78, "oxygen": 98, "systolic": 118, "diastolic": 76},
    "Patient 2": {"heart": 88, "oxygen": 96, "systolic": 132, "diastolic": 84},
    "Patient 3": {"heart": 64, "oxygen": 98, "systolic": 112, "diastolic": 72},
}


def clamp(value, low, high):
    return max(low, min(high, value))


def create_starting_data():
    rows = []
    start_time = datetime.now() - timedelta(minutes=20)

    for patient_name, baseline in PATIENT_BASELINES.items():
        for minute in range(21):
            rows.append(
                {
                    "Patient": patient_name,
                    "Time": start_time + timedelta(minutes=minute),
                    "Heart Rate (bpm)": round(baseline["heart"] + np.random.normal(0, 2), 1),
                    "Oxygen Saturation (%)": round(baseline["oxygen"] + np.random.normal(0, 0.6), 1),
                    "Systolic BP (mmHg)": round(baseline["systolic"] + np.random.normal(0, 3), 1),
                    "Diastolic BP (mmHg)": round(baseline["diastolic"] + np.random.normal(0, 2), 1),
                }
            )

    return pd.DataFrame(rows)


def start_random_event():
    patient = np.random.choice(list(PATIENT_BASELINES.keys()))
    event = np.random.choice(["Hypoxia", "Tachycardia", "Bradycardia", "Hypertension"])
    st.session_state.active_event = {
        "patient": patient,
        "event": event,
        "ticks_remaining": np.random.randint(3, 6),
    }


def simulate_next_reading():
    old_data = st.session_state.vital_data
    latest_by_patient = old_data.sort_values("Time").groupby("Patient").tail(1)

    if st.session_state.tick % 4 == 0 and st.session_state.active_event is None:
        start_random_event()

    new_rows = []
    now = datetime.now()

    for _, row in latest_by_patient.iterrows():
        patient = row["Patient"]

        heart = row["Heart Rate (bpm)"] + np.random.normal(0, 3)
        oxygen = row["Oxygen Saturation (%)"] + np.random.normal(0, 0.7)
        systolic = row["Systolic BP (mmHg)"] + np.random.normal(0, 4)
        diastolic = row["Diastolic BP (mmHg)"] + np.random.normal(0, 2)

        active = st.session_state.active_event
        if active is not None and active["patient"] == patient:
            event = active["event"]

            if event == "Hypoxia":
                oxygen -= np.random.uniform(4, 8)
            elif event == "Tachycardia":
                heart += np.random.uniform(22, 38)
            elif event == "Bradycardia":
                heart -= np.random.uniform(18, 30)
            elif event == "Hypertension":
                systolic += np.random.uniform(18, 30)
                diastolic += np.random.uniform(8, 14)

        heart = clamp(heart, 38, 150)
        oxygen = clamp(oxygen, 84, 100)
        systolic = clamp(systolic, 90, 180)
        diastolic = clamp(diastolic, 55, 115)

        new_rows.append(
            {
                "Patient": patient,
                "Time": now,
                "Heart Rate (bpm)": round(heart, 1),
                "Oxygen Saturation (%)": round(oxygen, 1),
                "Systolic BP (mmHg)": round(systolic, 1),
                "Diastolic BP (mmHg)": round(diastolic, 1),
            }
        )

    if st.session_state.active_event is not None:
        st.session_state.active_event["ticks_remaining"] -= 1
        if st.session_state.active_event["ticks_remaining"] <= 0:
            st.session_state.active_event = None

    updated = pd.concat([old_data, pd.DataFrame(new_rows)], ignore_index=True)
    updated = updated.groupby("Patient").tail(40).reset_index(drop=True)

    st.session_state.vital_data = updated
    st.session_state.tick += 1


def evaluate_patient_status(row):
    reasons = []

    if row["Heart Rate (bpm)"] < THRESHOLDS["low_heart_rate"]:
        reasons.append("heart rate below 50 bpm")
    if row["Heart Rate (bpm)"] > THRESHOLDS["high_heart_rate"]:
        reasons.append("heart rate above 120 bpm")
    if row["Oxygen Saturation (%)"] < THRESHOLDS["low_oxygen"]:
        reasons.append("oxygen saturation below 92%")
    if row["Systolic BP (mmHg)"] > THRESHOLDS["high_systolic_bp"] or row["Diastolic BP (mmHg)"] > THRESHOLDS["high_diastolic_bp"]:
        reasons.append("blood pressure above 150/95 mmHg")

    if reasons:
        return "Priority 1 Alert", reasons

    return "Stable", []


def line_chart(patient_data, y_column, title, y_title, threshold=None):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=patient_data["Time"],
            y=patient_data[y_column],
            mode="lines+markers",
            name=y_title,
            line=dict(width=3),
            marker=dict(size=5),
        )
    )

    if threshold is not None:
        fig.add_hline(
            y=threshold,
            line_dash="dash",
            annotation_text=f"Threshold: {threshold}",
            annotation_position="top left",
        )

    fig.update_layout(
        title=title,
        height=260,
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis_title="Time",
        yaxis_title=y_title,
        legend=dict(orientation="h"),
    )

    return fig


if "vital_data" not in st.session_state:
    np.random.seed(42)
    st.session_state.vital_data = create_starting_data()
    st.session_state.tick = 1
    st.session_state.active_event = None


with st.sidebar:
    st.header("Simulation Controls")
    auto_refresh = st.toggle("Run live simulation", value=True)
    refresh_seconds = st.slider("Refresh speed", min_value=1, max_value=5, value=2)
    st.caption("The app generates new readings every few seconds to simulate remote patient monitoring.")

    if st.button("Reset Simulation"):
        st.session_state.vital_data = create_starting_data()
        st.session_state.tick = 1
        st.session_state.active_event = None
        st.rerun()


st.markdown('<div class="main-title">Bio-Monitor Alert System</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Real-time simulated hospital dashboard for monitoring heart rate, oxygen saturation, and blood pressure.</div>',
    unsafe_allow_html=True,
)

if auto_refresh:
    simulate_next_reading()

data = st.session_state.vital_data.copy()
latest = data.sort_values("Time").groupby("Patient").tail(1).sort_values("Patient")

alert_rows = []
for _, row in latest.iterrows():
    status, reasons = evaluate_patient_status(row)
    if status == "Priority 1 Alert":
        alert_rows.append(f"{row['Patient']}: " + ", ".join(reasons))

if alert_rows:
    st.markdown(
        '<div class="alert-banner">Priority 1 Alert Active — '
        + " | ".join(alert_rows)
        + "</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="normal-banner">All monitored patients are currently within the project threshold ranges.</div>',
        unsafe_allow_html=True,
    )

cols = st.columns(3)

for col, (_, row) in zip(cols, latest.iterrows()):
    status, reasons = evaluate_patient_status(row)
    status_class = "status-alert" if status == "Priority 1 Alert" else "status-normal"
    status_text = "Priority 1 Alert: " + ", ".join(reasons) if reasons else "Stable"

    with col:
        st.markdown(
            f"""
            <div class="patient-card">
                <div class="patient-name">{row['Patient']}</div>
                <div class="{status_class}">{status_text}</div>

                <div class="metric-label">Heart Rate</div>
                <div class="metric-value">{row['Heart Rate (bpm)']:.0f} bpm</div>

                <div class="metric-label">Oxygen Saturation</div>
                <div class="metric-value">{row['Oxygen Saturation (%)']:.0f}%</div>

                <div class="metric-label">Blood Pressure</div>
                <div class="metric-value">{row['Systolic BP (mmHg)']:.0f}/{row['Diastolic BP (mmHg)']:.0f} mmHg</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

for patient in sorted(data["Patient"].unique()):
    patient_data = data[data["Patient"] == patient].sort_values("Time")

    st.subheader(patient)

    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.plotly_chart(
            line_chart(
                patient_data,
                "Heart Rate (bpm)",
                "Heart Rate Over Time",
                "Heart Rate (bpm)",
                threshold=120,
            ),
            use_container_width=True,
        )

    with chart_cols[1]:
        st.plotly_chart(
            line_chart(
                patient_data,
                "Oxygen Saturation (%)",
                "Oxygen Saturation Over Time",
                "Oxygen Saturation (%)",
                threshold=92,
            ),
            use_container_width=True,
        )

st.divider()

st.subheader("Latest Readings")
display_table = latest[
    [
        "Patient",
        "Time",
        "Heart Rate (bpm)",
        "Oxygen Saturation (%)",
        "Systolic BP (mmHg)",
        "Diastolic BP (mmHg)",
    ]
].copy()
display_table["Time"] = display_table["Time"].dt.strftime("%H:%M:%S")
st.dataframe(display_table, use_container_width=True, hide_index=True)

with st.expander("System Architecture and Data Flow"):
    st.markdown(
        """
        **Data source:** simulated patient vital-sign readings.

        **Data processing:** pandas stores and updates patient readings in a table.

        **Alert logic:** each new reading is compared against clinical threshold values.

        **Dashboard output:** Streamlit displays live patient cards, trend charts, and Priority 1 warning banners.
        """
    )

st.markdown(
    '<div class="small-note">This dashboard is an educational prototype and is not intended for real clinical use.</div>',
    unsafe_allow_html=True,
)

if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()