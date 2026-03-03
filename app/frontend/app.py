import streamlit as st
import requests
import pandas as pd
import os
from components import render_bounds_chart, render_gauge

# Constants
API_BASE = "http://localhost:8000"
BATCH_DIR = os.path.join(os.getcwd(), "data", "batches")

st.set_page_config(page_title="GCO Engine - Phase 0", layout="wide")

st.title("Golden Corridor Optimization Engine")
st.caption("Phase 0 - Minimal Working Skeleton")

# --- SIDEBAR: Mode Selection ---
st.sidebar.header("Optimization Mode")
mode = st.sidebar.radio("Select Mode", ["sustainability_first", "production_first"])

if st.sidebar.button("Update Mode"):
    resp = requests.post(f"{API_BASE}/mode/set", json={"mode": mode})
    if resp.status_code == 200:
        data = resp.json()
        st.sidebar.success(f"Mode set to {data['mode']}")
        st.sidebar.json(data['weights'])

# --- MAIN: Batch Selection & Visualization ---
st.header("1. Batch Exploration & Recommendations")
col1, col2 = st.columns([1, 3])

batch_files = []
if os.path.exists(BATCH_DIR):
    batch_files = [f.replace(".csv", "") for f in os.listdir(BATCH_DIR) if f.endswith(".csv")]

if not batch_files:
    st.warning("No batch data found. Please run 'make data' first.")
    st.stop()

with col1:
    selected_batch = st.selectbox("Select Batch", batch_files)
    df = pd.read_csv(os.path.join(BATCH_DIR, f"{selected_batch}.csv"))
    
    ts_options = df['ts'].tolist()
    selected_ts = st.select_slider("Select Timestamp", options=ts_options)
    
    current_row = df[df['ts'] == selected_ts].iloc[0]
    
    if st.button("Get Recommendation"):
        rec_resp = requests.post(f"{API_BASE}/optimize/recommend", json={
            "batch_id": selected_batch,
            "ts": selected_ts
        })
        if rec_resp.status_code == 200:
            rec_data = rec_resp.json()
            st.session_state['recommendation'] = rec_data
            st.success("Recommendation Received")
        else:
            st.error("Failed to get recommendation")

with col2:
    # Get active corridor
    corridor_resp = requests.get(f"{API_BASE}/corridor/version")
    if corridor_resp.status_code == 200:
        corridor_data = corridor_resp.json()
        bounds = corridor_data['bounds']
        
        c1, c2 = st.columns(2)
        with c1:
            render_gauge("Temperature", current_row['temperature'], bounds['temperature']['lower'], bounds['temperature']['upper'])
        with c2:
            render_gauge("Flow", current_row['flow'], bounds['flow']['lower'], bounds['flow']['upper'])
            
        render_bounds_chart(df, "temperature", bounds['temperature'])
        render_bounds_chart(df, "flow", bounds['flow'])

if 'recommendation' in st.session_state:
    st.subheader("Last Recommendation")
    rec = st.session_state['recommendation']
    c1, c2, c3 = st.columns(3)
    c1.metric("Recommended Temp", rec['setpoints']['temperature'])
    c2.metric("Recommended Flow", rec['setpoints']['flow'])
    c3.write(f"**Rationale:** {rec['rationale']}")
    st.write(f"**Weights Applied:** {rec['objective_weights']}")

# --- SECTION: KPI Ingestion ---
st.divider()
st.header("2. End-of-Batch KPI Ingestion")
with st.form("kpi_form"):
    k_batch = st.selectbox("Batch ID", batch_files, key="k_batch")
    k_energy = st.number_input("Energy Consumed (kWh)", min_value=0.0, value=45.0)
    k_yield = st.number_input("Yield (%)", min_value=0.0, max_value=100.0, value=92.5)
    k_quality = st.checkbox("Quality Deviation Flag")
    
    if st.form_submit_button("Submit KPIs"):
        kpi_resp = requests.post(f"{API_BASE}/kpi/ingest", json={
            "batch_id": k_batch,
            "energy_kwh": k_energy,
            "yield_pct": k_yield,
            "quality_deviation": k_quality
        })
        if kpi_resp.status_code == 200:
            st.success(kpi_resp.json()['message'])
            if kpi_resp.json()['anomaly_flag']:
                st.warning("Anomaly detected in batch KPIs!")
        else:
            st.error("KPI ingestion failed")

# --- SECTION: Corridor Proposals & Governance ---
st.divider()
st.header("3. Corridor Governance & Proposals")

prop_col, hist_col = st.columns(2)

with prop_col:
    st.subheader("Pending Proposals")
    pending_resp = requests.get(f"{API_BASE}/corridor/proposals/pending")
    if pending_resp.status_code == 200:
        proposals = pending_resp.json()
        if not proposals:
            st.write("No pending proposals.")
        for p in proposals:
            with st.expander(f"Proposal {p['id']} - {p['created_at']}"):
                st.write(f"**Evidence:** {p['evidence']}")
                st.json(p['delta'])
                decision = st.radio(f"Decision for {p['id']}", ["approve", "reject"], key=f"radio_{p['id']}")
                notes = st.text_input("Notes", key=f"notes_{p['id']}")
                if st.button(f"Submit Decision for {p['id']}"):
                    app_resp = requests.post(f"{API_BASE}/corridor/approve", json={
                        "proposal_id": p['id'],
                        "decision": decision,
                        "notes": notes
                    })
                    if app_resp.status_code == 200:
                        st.success(f"Proposal {decision}d")
                        st.rerun()

with hist_col:
    st.subheader("Version History")
    if corridor_resp.status_code == 200:
        st.write(f"**Current Version:** {corridor_data['active_version']}")
        st.table(corridor_data['history'])
