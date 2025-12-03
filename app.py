import streamlit as st
import json
import os

# ---------------------------------------------------
# 📌 Base folder for JSON files (GitHub root directory)
# ---------------------------------------------------
BASE = "."

# File paths
PATH_DASHBOARD = f"{BASE}/doctor_dashboard.json"
PATH_DOCTORS = f"{BASE}/doctors.json"
PATH_PATIENTS = f"{BASE}/patients.json"
PATH_APPOINTMENTS = f"{BASE}/appointments.json"
PATH_AI_RESULTS = f"{BASE}/ai_results.json"
PATH_NOTIFICATIONS = f"{BASE}/notifications.json"
PATH_ORDERS = f"{BASE}/doctor_orders.json"


# ---------------------------------------------------
# 📌 Helper function to load JSON safely
# ---------------------------------------------------
def load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return {}


# ---------------------------------------------------
# 📌 Load all data
# ---------------------------------------------------
dashboard = load_json(PATH_DASHBOARD)
doctors = load_json(PATH_DOCTORS)
patients = load_json(PATH_PATIENTS)
appointments = load_json(PATH_APPOINTMENTS)
ai_results = load_json(PATH_AI_RESULTS)
notifications = load_json(PATH_NOTIFICATIONS)
doctor_orders = load_json(PATH_ORDERS)


# ---------------------------------------------------
# 🌟 Streamlit UI Begins
# ---------------------------------------------------
st.set_page_config(page_title="AI Doctor Dashboard", layout="wide")

st.title("🩺 AI-Powered Doctor Dashboard")

# ---------------------------------------------------
# If no dashboard data exists
# ---------------------------------------------------
if not dashboard:
    st.warning("No dashboard data found. Run AI processing first.")
    st.stop()


# ---------------------------------------------------
# 🔍 Sidebar navigation
# ---------------------------------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "AI Results", "Appointments", "Notifications"])


# ---------------------------------------------------
# 📌 PAGE 1: DOCTOR DASHBOARD
# ---------------------------------------------------
if page == "Dashboard":
    st.header("📋 Patient Review Dashboard")

    for pid, pdata in dashboard.items():
        patient = patients.get(pid, {})
        doctor_id = pdata.get("doctor_id", "")
        doctor = doctors.get(doctor_id, {})

        with st.expander(f"🔵 {pid} — {patient.get('name', 'Unknown')}"):
            st.write(f"**Symptoms:** {patient.get('symptoms', 'N/A')}")
            st.write(f"**Assigned Doctor:** {doctor.get('name', 'Unknown')} ({doctor.get('department')})")
            st.write(f"**Tests Ordered:** {pdata.get('tests_ordered')}")
            st.write(f"**Final Severity:** {pdata.get('final_severity')}")
            st.write(f"**AI Test Results:**")
            st.json(pdata.get("tests", {}))

            # Approval button
            if st.button(f"Approve Report for {pid}"):
                st.success(f"Doctor approved {pid}'s report (simulation only).")


# ---------------------------------------------------
# 📌 PAGE 2: AI RESULTS
# ---------------------------------------------------
elif page == "AI Results":
    st.header("🤖 AI Test Results")

    if not ai_results:
        st.info("No AI results found.")
    else:
        st.json(ai_results)


# ---------------------------------------------------
# 📌 PAGE 3: Appointments
# ---------------------------------------------------
elif page == "Appointments":
    st.header("📅 Scheduled Appointments")

    if not appointments:
        st.info("No appointments available.")
    else:
        for pid, appt in appointments.items():
            with st.expander(f"{pid} — {appt.get('department')}"):
                st.write(appt)


# ---------------------------------------------------
# 📌 PAGE 4: Notifications
# ---------------------------------------------------
elif page == "Notifications":
    st.header("🔔 Patient Notifications")

    if not notifications:
        st.info("No notifications sent.")
    else:
        for pid, note in notifications.items():
            st.write(f"**{pid}:** {note}")
