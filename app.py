# Import tools for timing the automatic dashboard refresh.
# Import date tools for creating timestamps for patient readings.
import time
from datetime import datetime, timedelta

# Import NumPy to generate small random changes in simulated vital signs.
# Import pandas to store and organize patient readings in a DataFrame.
# Import Plotly to create the interactive vital-sign charts.
# Import Streamlit to build and display the web dashboard.
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Configure the browser page before displaying any dashboard content.
st.set_page_config(
    page_title="Bio-Monitor Alert System",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Add custom CSS to control the appearance of titles, cards, statuses, metrics, and alert banners.
st.markdown(
    """
<style>
.main-title {
    font-size: 2.2rem;
    font-weight: 750;
    margin-bottom: 1.2rem;
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
</style>
""",
    unsafe_allow_html=True,
)

# Store the project thresholds used to decide when a patient needs a Priority 1 Alert.
THRESHOLDS = {
    "low_heart_rate": 50,
    "high_heart_rate": 120,
    "low_oxygen": 92,
    "high_systolic_bp": 150,
    "high_diastolic_bp": 95,
}

# Store normal starting values for each simulated patient.
PATIENT_BASELINES = {
    "Patient 1": {"heart": 78, "oxygen": 98, "systolic": 118, "diastolic": 76},
    "Patient 2": {"heart": 88, "oxygen": 96, "systolic": 132, "diastolic": 84},
    "Patient 3": {"heart": 64, "oxygen": 98, "systolic": 112, "diastolic": 72},
}


# Keep a simulated value inside a realistic minimum and maximum range.
def clamp(value, low, high):
    return max(low, min(high, value))


# Create the first 21 readings for every patient when the dashboard starts.
def create_starting_data():
    # Create an empty list that will hold every generated patient reading.
    rows = []
    # Start the sample timeline 20 minutes before the current time.
    start_time = datetime.now() - timedelta(minutes=20)

    # Generate a separate timeline using the baseline values for each patient.
    for patient, baseline in PATIENT_BASELINES.items():
        # Create one reading per minute for a total of 21 starting readings.
        for minute in range(21):
            # Add small random changes so the starting data looks realistic.
            rows.append(
                {
                    "Patient": patient,
                    "Time": start_time + timedelta(minutes=minute),
                    "Heart Rate (bpm)": round(baseline["heart"] + np.random.normal(0, 2), 1),
                    "Oxygen Saturation (%)": round(baseline["oxygen"] + np.random.normal(0, 0.6), 1),
                    "Systolic BP (mmHg)": round(baseline["systolic"] + np.random.normal(0, 3), 1),
                    "Diastolic BP (mmHg)": round(baseline["diastolic"] + np.random.normal(0, 2), 1),
                }
            )

    # Convert the completed list of readings into a pandas DataFrame.
    return pd.DataFrame(rows)


# Choose one random patient and one random medical event for the live demonstration.
def start_random_event():
    # Save the active event in Streamlit session state so it continues across refreshes.
    st.session_state.active_event = {
        "patient": np.random.choice(list(PATIENT_BASELINES)),
        "event": np.random.choice(["Hypoxia", "Tachycardia", "Bradycardia", "Hypertension"]),
        "ticks_remaining": np.random.randint(3, 6),
    }


# Generate the next live reading for every patient.
def simulate_next_reading():
    # Get the stored patient data from Streamlit session state.
    data = st.session_state.vital_data
    # Select the most recent reading for each patient.
    latest = data.sort_values("Time").groupby("Patient").tail(1)

    # Start a random abnormal event every four update cycles when no event is active.
    if st.session_state.tick % 4 == 0 and st.session_state.active_event is None:
        start_random_event()

    # Create a list for the next set of readings and record the current time.
    new_rows = []
    now = datetime.now()

    # Update each patient separately using their most recent measurements.
    for _, row in latest.iterrows():
        # Read the patient name and add small random changes to each vital sign.
        patient = row["Patient"]
        heart = row["Heart Rate (bpm)"] + np.random.normal(0, 3)
        oxygen = row["Oxygen Saturation (%)"] + np.random.normal(0, 0.7)
        systolic = row["Systolic BP (mmHg)"] + np.random.normal(0, 4)
        diastolic = row["Diastolic BP (mmHg)"] + np.random.normal(0, 2)

        # Check whether this patient currently has a simulated medical event.
        active = st.session_state.active_event
        if active and active["patient"] == patient:
            event = active["event"]
            # Change the matching vital sign enough to demonstrate each alert type.
            if event == "Hypoxia":
                oxygen -= np.random.uniform(4, 8)
            elif event == "Tachycardia":
                heart += np.random.uniform(22, 38)
            elif event == "Bradycardia":
                heart -= np.random.uniform(18, 30)
            else:
                systolic += np.random.uniform(18, 30)
                diastolic += np.random.uniform(8, 14)

        # Save the new reading after limiting every value to a broad realistic range.
        new_rows.append(
            {
                "Patient": patient,
                "Time": now,
                "Heart Rate (bpm)": round(clamp(heart, 38, 150), 1),
                "Oxygen Saturation (%)": round(clamp(oxygen, 84, 100), 1),
                "Systolic BP (mmHg)": round(clamp(systolic, 90, 180), 1),
                "Diastolic BP (mmHg)": round(clamp(diastolic, 55, 115), 1),
            }
        )

    # Reduce the remaining duration of the active event after each update.
    if st.session_state.active_event:
        st.session_state.active_event["ticks_remaining"] -= 1
        # End the event when its update cycles have finished.
        if st.session_state.active_event["ticks_remaining"] <= 0:
            st.session_state.active_event = None

    # Add the new readings to the existing DataFrame.
    updated = pd.concat([data, pd.DataFrame(new_rows)], ignore_index=True)
    # Keep only the latest 40 readings for each patient so the charts stay readable.
    st.session_state.vital_data = updated.groupby("Patient").tail(40).reset_index(drop=True)
    # Increase the update counter used to schedule random events.
    st.session_state.tick += 1


# Compare one patient reading against every Priority 1 threshold.
def evaluate_patient_status(row):
    # Store every reason that causes an alert.
    reasons = []

    # Check for severe bradycardia.
    if row["Heart Rate (bpm)"] < THRESHOLDS["low_heart_rate"]:
        reasons.append("heart rate below 50 bpm")
    # Check for severe tachycardia.
    if row["Heart Rate (bpm)"] > THRESHOLDS["high_heart_rate"]:
        reasons.append("heart rate above 120 bpm")
    # Check for low oxygen saturation.
    if row["Oxygen Saturation (%)"] < THRESHOLDS["low_oxygen"]:
        reasons.append("oxygen saturation below 92%")
    # Check whether either blood-pressure measurement crosses its threshold.
    if (
        row["Systolic BP (mmHg)"] > THRESHOLDS["high_systolic_bp"]
        or row["Diastolic BP (mmHg)"] > THRESHOLDS["high_diastolic_bp"]
    ):
        reasons.append("blood pressure above 150/95 mmHg")

    # Return Priority 1 with the reasons, or Stable when no threshold is crossed.
    return ("Priority 1 Alert", reasons) if reasons else ("Stable", [])


# Build a reusable Plotly chart for heart rate or oxygen saturation.
def line_chart(patient_data, y_column, title, y_title, threshold):
    # Create the main line and marker trace using the selected vital-sign column.
    fig = go.Figure(
        go.Scatter(
            x=patient_data["Time"],
            y=patient_data[y_column],
            mode="lines+markers",
            name=y_title,
            line=dict(width=3),
            marker=dict(size=5),
        )
    )

    # Add a dashed horizontal line showing the alert threshold.
    fig.add_hline(
        y=threshold,
        line_dash="dash",
        annotation_text=f"Threshold: {threshold}",
        annotation_position="top left",
    )

    # Set the chart title, size, labels, margins, and legend position.
    fig.update_layout(
        title=title,
        height=260,
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis_title="Time",
        yaxis_title=y_title,
        legend=dict(orientation="h"),
    )

    # Return the finished chart so Streamlit can display it.
    return fig


# Build a blood-pressure chart with systolic and diastolic readings together.
def blood_pressure_chart(patient_data):
    # Start with an empty Plotly figure.
    fig = go.Figure()

    # Add the systolic blood-pressure line.
    fig.add_trace(
        go.Scatter(
            x=patient_data["Time"],
            y=patient_data["Systolic BP (mmHg)"],
            mode="lines+markers",
            name="Systolic BP",
            line=dict(width=3),
            marker=dict(size=5),
        )
    )

    # Add the diastolic blood-pressure line.
    fig.add_trace(
        go.Scatter(
            x=patient_data["Time"],
            y=patient_data["Diastolic BP (mmHg)"],
            mode="lines+markers",
            name="Diastolic BP",
            line=dict(width=3),
            marker=dict(size=5),
        )
    )

    # Show the systolic alert threshold at 150 mmHg.
    fig.add_hline(
        y=150,
        line_dash="dash",
        annotation_text="Systolic threshold: 150",
        annotation_position="top left",
    )

    # Show the diastolic alert threshold at 95 mmHg.
    fig.add_hline(
        y=95,
        line_dash="dash",
        annotation_text="Diastolic threshold: 95",
        annotation_position="bottom left",
    )

    # Set the blood-pressure chart title, size, axes, margins, and legend.
    fig.update_layout(
        title="Blood Pressure Over Time",
        height=260,
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis_title="Time",
        yaxis_title="Blood Pressure (mmHg)",
        legend=dict(orientation="h"),
    )

    # Return the completed blood-pressure chart.
    return fig


# Create the dashboard data only once when a new Streamlit session begins.
if "vital_data" not in st.session_state:
    # Use a fixed random seed so the starting data is consistent.
    np.random.seed(42)
    # Store the starting data, update counter, and active event in session state.
    st.session_state.vital_data = create_starting_data()
    st.session_state.tick = 1
    st.session_state.active_event = None

# Build the sidebar controls for the live simulation.
with st.sidebar:
    # Add the simulation title, on/off switch, and refresh-speed slider.
    st.header("Simulation Controls")
    auto_refresh = st.toggle("Run live simulation", value=True)
    refresh_seconds = st.slider("Refresh speed", 1, 5, 2)

    # Reset all generated data and restart the app when the button is pressed.
    if st.button("Reset Simulation"):
        st.session_state.vital_data = create_starting_data()
        st.session_state.tick = 1
        st.session_state.active_event = None
        st.rerun()

# Display the main dashboard title.
st.markdown('<div class="main-title">Bio-Monitor Alert System</div>', unsafe_allow_html=True)

# Generate a new set of readings whenever live simulation is enabled.
if auto_refresh:
    simulate_next_reading()

# Copy the complete dataset and select the latest reading for each patient.
data = st.session_state.vital_data.copy()
latest = data.sort_values("Time").groupby("Patient").tail(1).sort_values("Patient")

# Check every latest reading and collect all active Priority 1 alert messages.
alerts = []
for _, row in latest.iterrows():
    status, reasons = evaluate_patient_status(row)
    if status == "Priority 1 Alert":
        alerts.append(f"{row['Patient']}: " + ", ".join(reasons))

# Display a red banner when alerts exist, or a green banner when all patients are stable.
if alerts:
    st.markdown(
        '<div class="alert-banner">Priority 1 Alert Active - '
        + " | ".join(alerts)
        + "</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="normal-banner">All monitored patients are currently within the project threshold ranges.</div>',
        unsafe_allow_html=True,
    )

# Create three equal columns for the patient summary cards.
columns = st.columns(3)

# Build one card for each patient's latest measurements and status.
for column, (_, row) in zip(columns, latest.iterrows()):
    # Evaluate the patient and choose the correct status style and text.
    status, reasons = evaluate_patient_status(row)
    status_class = "status-alert" if reasons else "status-normal"
    status_text = "Priority 1 Alert: " + ", ".join(reasons) if reasons else "Stable"

    # Create the HTML that displays the patient's heart rate, oxygen, and blood pressure.
    card_html = (
        f'<div class="patient-card">'
        f'<div class="patient-name">{row["Patient"]}</div>'
        f'<div class="{status_class}">{status_text}</div>'
        f'<div class="metric-label">Heart Rate</div>'
        f'<div class="metric-value">{row["Heart Rate (bpm)"]:.0f} bpm</div>'
        f'<div class="metric-label">Oxygen Saturation</div>'
        f'<div class="metric-value">{row["Oxygen Saturation (%)"]:.0f}%</div>'
        f'<div class="metric-label">Blood Pressure</div>'
        f'<div class="metric-value">{row["Systolic BP (mmHg)"]:.0f}/{row["Diastolic BP (mmHg)"]:.0f} mmHg</div>'
        f'</div>'
    )

    # Place the completed patient card inside its assigned dashboard column.
    with column:
        st.markdown(card_html, unsafe_allow_html=True)

# Separate the patient cards from the trend charts.
st.divider()

# Create three trend charts for every patient without requiring a patient selector.
for patient in sorted(data["Patient"].unique()):
    # Filter the DataFrame to include only the current patient's readings.
    patient_data = data[data["Patient"] == patient].sort_values("Time")
    st.subheader(patient)

    # Place heart rate, oxygen saturation, and blood pressure in three columns.
    chart_columns = st.columns(3)

    # Display the patient's heart-rate chart.
    with chart_columns[0]:
        st.plotly_chart(
            line_chart(
                patient_data,
                "Heart Rate (bpm)",
                "Heart Rate Over Time",
                "Heart Rate (bpm)",
                120,
            ),
            use_container_width=True,
        )

    # Display the patient's oxygen-saturation chart.
    with chart_columns[1]:
        st.plotly_chart(
            line_chart(
                patient_data,
                "Oxygen Saturation (%)",
                "Oxygen Saturation Over Time",
                "Oxygen Saturation (%)",
                92,
            ),
            use_container_width=True,
        )

    # Display the patient's combined systolic and diastolic blood-pressure chart.
    with chart_columns[2]:
        st.plotly_chart(
            blood_pressure_chart(patient_data),
            use_container_width=True,
        )

# Separate the charts from the latest-readings table.
st.divider()
# Add a heading for the most recent patient measurements.
st.subheader("Latest Readings")

# Select only the columns needed in the final table.
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

# Format the timestamps so they are easy to read.
display_table["Time"] = display_table["Time"].dt.strftime("%H:%M:%S")
# Display the latest readings as a full-width Streamlit table.
st.dataframe(display_table, use_container_width=True, hide_index=True)

# Wait for the chosen refresh interval and rerun the app to simulate live monitoring.
if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()
