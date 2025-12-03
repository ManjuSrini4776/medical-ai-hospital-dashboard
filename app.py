import os
import json
import datetime
import streamlit as st

# ==== CONFIG ====
BASE = "/content/drive/MyDrive/Medical_AI_Hospital_Project"  # adjust if running locally

patients_path = os.path.join(BASE, "patients.json")
doctors_path = os.path.join(BASE, "doctors.json")
dashboard_path = os.path.join(BASE, "doctor_dashboard.json")
appointments_path = os.path.join(BASE, "appointments.json")
notifications_path = os.path.join(BASE, "notifications.json")


# ==== UTILS ====
def load_json(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# ==== FALLBACK DOCTOR LOGIC ====
def get_approving_doctor(patient_id):
    patients = load_json(patients_path, {})
    doctors = load_json(doctors_path, {})

    assigned_doc = patients[patient_id]["doctor_id"]
    assigned_dept = doctors[assigned_doc]["department"]

    # 1) If assigned doctor is available → use
    if doctors[assigned_doc].get("available", True):
        return assigned_doc

    # 2) Fallback in same department
    for did, doc in doctors.items():
        if (
            doc["department"] == assigned_dept
            and doc.get("available", True)
            and did != assigned_doc
        ):
            return did

    # 3) No one available
    return None


# ==== APPROVAL ENGINE ====
def approve_case(patient_id):
    dashboard = load_json(dashboard_path, {})
    appointments = load_json(appointments_path, {})
    notifications = load_json(notifications_path, {})

    if patient_id not in dashboard:
        st.error(f"Patient {patient_id} not found in dashboard.")
        return

    case = dashboard[patient_id]
    severity = case["final_severity"]

    approver = get_approving_doctor(patient_id)
    if approver is None:
        st.error("No doctor available in this department to approve.")
        return

    case["approved_by"] = approver
    case["status"] = "Approved"

    # Patient message
    if severity == "Normal":
        message = (
            f"Dear {case['patient_name']}, your test results are normal. "
            f"You may continue your current routine. No special treatment required."
        )
    elif severity == "Mild":
        message = (
            f"Dear {case['patient_name']}, your reports show mild abnormality. "
            f"Please follow doctor advice and schedule a follow-up check."
        )
    else:  # Severe
        message = (
            f"⚠ Dear {case['patient_name']}, your reports need urgent medical attention. "
            f"An immediate appointment has been scheduled."
        )
        today = str(datetime.date.today())
        appt = {
            "patient_id": patient_id,
            "doctor_id": approver,
            "date": today,
            "time": "10:00 AM",
            "status": "Scheduled",
        }
        appointments[patient_id] = appt
        save_json(appointments_path, appointments)

    notifications[patient_id] = {
        "message": message,
        "severity": severity,
        "approved_by": approver,
        "time": str(datetime.datetime.now()),
    }

    # Save updates
    save_json(notifications_path, notifications)
    dashboard[patient_id] = case
    save_json(dashboard_path, dashboard)

    st.success(f"Patient {patient_id} approved by {approver}")
    st.info(f"Notification sent: {message}")
    if severity == "Severe":
        st.warning("Appointment created automatically for this severe case.")


# ==== STREAMLIT UI ====
def main():
    st.set_page_config(page_title="Doctor Dashboard", layout="wide")
    st.title("🩺 AI-Powered Doctor Dashboard")

    patients = load_json(patients_path, {})
    doctors = load_json(doctors_path, {})
    dashboard = load_json(dashboard_path, {})

    if not dashboard:
        st.warning("No dashboard data found. Run AI processing first.")
        return

    # ---- SIDEBAR FILTERS ----
    st.sidebar.header("Filters")

    # Doctor filter
    doctor_options = ["All"] + [f"{did} - {doc['name']}" for did, doc in doctors.items()]
    doc_selected = st.sidebar.selectbox("Filter by Doctor", doctor_options)

    # Status filter
    status_options = ["All", "Pending Review", "Approved"]
    status_selected = st.sidebar.selectbox("Filter by Status", status_options)

    # Severity filter
    severity_options = ["All", "Normal", "Mild", "Severe"]
    severity_selected = st.sidebar.selectbox("Filter by Severity", severity_options)

    # ---- BUILD TABLE DATA ----
    rows = []
    for pid, entry in dashboard.items():
        row = {
            "Patient ID": pid,
            "Name": entry["patient_name"],
            "Doctor ID": entry["doctor_id"],
            "Final Severity": entry["final_severity"],
            "Status": entry["status"],
            "Symptoms": entry["symptoms"],
        }
        rows.append(row)

    # Filter in memory
    import pandas as pd

    df = pd.DataFrame(rows)

    if doc_selected != "All":
        selected_id = doc_selected.split(" - ")[0]
        df = df[df["Doctor ID"] == selected_id]

    if status_selected != "All":
        df = df[df["Status"] == status_selected]

    if severity_selected != "All":
        df = df[df["Final Severity"] == severity_selected]

    st.subheader("🧾 Patient List")
    st.dataframe(df, use_container_width=True)

    if df.empty:
        st.info("No patients match the selected filters.")
        return

    # ---- SELECT PATIENT ----
    st.subheader("🔍 Review a Patient")

    patient_ids = df["Patient ID"].tolist()
    selected_pid = st.selectbox("Select Patient ID", patient_ids)

    entry = dashboard[selected_pid]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 👤 Patient Info")
        st.write(f"**ID:** {selected_pid}")
        st.write(f"**Name:** {entry['patient_name']}")
        st.write(f"**Symptoms:** {entry['symptoms']}")
        st.write(f"**Assigned Doctor:** {entry['doctor_id']}")
        st.write(f"**Final Severity:** {entry['final_severity']}")
        st.write(f"**Status:** {entry['status']}")

    with col2:
        st.markdown("### 🧪 Tests & AI Results")
        for test_name, result in entry["ai_results"].items():
            st.markdown(f"**Test:** `{test_name}`")
            st.json(result)

    # RAG explanation
    st.markdown("### 📚 RAG Clinical Explanation")
    with st.expander("Show AI + guideline-based explanation"):
        st.text(entry.get("rag_explanation", "No RAG explanation available."))

    # ---- APPROVAL BUTTON ----
    st.markdown("---")
    st.markdown("### ✅ Doctor Approval")

    if entry["status"] == "Approved":
        st.success(f"This case is already approved by {entry.get('approved_by', 'N/A')}.")
    else:
        if st.button("Approve this case"):
            approve_case(selected_pid)
            st.experimental_rerun()


if __name__ == "__main__":
    main()
