import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
from components import render_bounds_chart, render_gauge

# Constants
API_BASE = "http://localhost:8000"
BATCH_DIR = os.path.join(os.getcwd(), "data", "batches")

st.set_page_config(page_title="GCO Engine - Phase 1", layout="wide")

# --- INITIALIZATION & PREFETCH ---
if 'current_mode' not in st.session_state:
    try:
        resp = requests.get(f"{API_BASE}/mode/current")
        if resp.status_code == 200:
            st.session_state['current_mode'] = resp.json()
    except Exception:
        st.session_state['current_mode'] = None

if 'mode_policy' not in st.session_state:
    try:
        resp = requests.get(f"{API_BASE}/mode/policy")
        if resp.status_code == 200:
            st.session_state['mode_policy'] = resp.json()
    except Exception:
        st.session_state['mode_policy'] = None

def refresh_mode():
    try:
        resp = requests.get(f"{API_BASE}/mode/current")
        if resp.status_code == 200:
            st.session_state['current_mode'] = resp.json()
    except Exception as e:
        st.error(f"Failed to refresh mode: {e}")

st.title("Golden Corridor Optimization Engine")
st.caption("Phase 1 – Mode Configuration & Hardening")

# --- SIDEBAR: Optimization Mode ---
st.sidebar.header("Optimization Mode")

if st.session_state['mode_policy']:
    policy = st.session_state['mode_policy']
    allowed_modes = policy['allowed_modes']
    mode_options = {m['label']: m['id'] for m in allowed_modes}
    
    current_mode_id = st.session_state['current_mode']['mode'] if st.session_state['current_mode'] else "sustainability_first"
    current_label = next((m['label'] for m in allowed_modes if m['id'] == current_mode_id), "Sustainability-First")
    
    selected_label = st.sidebar.radio(
        "Choose Mode", 
        options=list(mode_options.keys()),
        index=list(mode_options.keys()).index(current_label) if current_label in mode_options else 0
    )
    
    if st.sidebar.button("Apply Mode"):
        selected_id = mode_options[selected_label]
        try:
            resp = requests.post(f"{API_BASE}/mode/set", json={"mode": selected_id})
            if resp.status_code == 200:
                data = resp.json()
                st.session_state['current_mode'] = data
                if data['changed']:
                    st.sidebar.success(f"Applied: {selected_label}")
                else:
                    st.sidebar.info("No change (already active)")
            else:
                st.sidebar.error(f"Error: {resp.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.sidebar.error(f"Connection error: {e}")

    # Current Mode Card in Sidebar
    if st.session_state['current_mode']:
        curr = st.session_state['current_mode']
        st.sidebar.markdown("---")
        st.sidebar.subheader("Current Mode Status")
        st.sidebar.info(f"**Mode:** {curr['mode']}")
        st.sidebar.json(curr['weights'])
        st.sidebar.caption(f"Last changed: {curr.get('changed_at', 'N/A')}")
else:
    st.sidebar.warning("Could not fetch mode policy from API.")

# --- MAIN AREA ---

# Mode Details Expander
with st.expander("Mode Details & Policy Info", expanded=False):
    if st.session_state['mode_policy']:
        policy = st.session_state['mode_policy']
        st.write(policy['notes'])
        cols = st.columns(len(policy['allowed_modes']))
        for i, m in enumerate(policy['allowed_modes']):
            with cols[i]:
                st.markdown(f"### {m['label']}")
                st.write(m['description'])
                st.json(m['weights'])
    
    if st.button("Refresh Current Mode"):
        refresh_mode()
        st.rerun()

st.divider()

# --- EXISTING PHASE 0 FLOWS ---

st.header("1. Batch Exploration & Recommendations")
col1, col2 = st.columns([1, 3])

batch_files = []
if os.path.exists(BATCH_DIR):
    batch_files = sorted([f.replace(".csv", "") for f in os.listdir(BATCH_DIR) if f.endswith(".csv")])

if not batch_files:
    st.warning("No batch data found. Please run 'make data' first.")
    # But don't stop entirely, maybe they can still see the mode config
else:
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
        try:
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
        except Exception as e:
            st.error(f"Could not fetch corridor data: {e}")

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
    k_batch = st.selectbox("Batch ID", batch_files, key="k_batch") if batch_files else st.text_input("Batch ID")
    k_energy = st.number_input("Energy Consumed (kWh)", min_value=0.0, value=45.0)
    k_yield = st.number_input("Yield (%)", min_value=0.0, max_value=100.0, value=92.5)
    k_quality = st.checkbox("Quality Deviation Flag")
    
    if st.form_submit_button("Submit KPIs"):
        try:
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
        except Exception as e:
            st.error(f"Connection error: {e}")

# --- SECTION: Corridor Proposals & Governance ---
st.divider()
st.header("3. Corridor Governance & Proposals")

prop_col, hist_col = st.columns(2)

with prop_col:
    st.subheader("Pending Proposals")
    try:
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
    except Exception as e:
        st.error(f"Could not fetch proposals: {e}")

with hist_col:
    st.subheader("Version History")
    try:
        corridor_resp = requests.get(f"{API_BASE}/corridor/version")
        if corridor_resp.status_code == 200:
            corridor_data = corridor_resp.json()
            st.write(f"**Current Version:** {corridor_data['active_version']}")
            st.table(corridor_data['history'])
    except Exception:
        st.write("Could not fetch version history.")
