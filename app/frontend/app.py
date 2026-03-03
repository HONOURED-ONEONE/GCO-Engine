import streamlit as st
import requests
import pandas as pd
import os
import time
from datetime import datetime
from components import render_bounds_chart, render_gauge

# Constants
API_BASE = "http://localhost:8000"
BATCH_DIR = os.path.join(os.getcwd(), "data", "batches")

st.set_page_config(page_title="GCO Engine - Phase 2", layout="wide")

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
st.caption("Phase 2 – Real-Time Optimization Loop & Pseudo-NMPC")

# --- SIDEBAR: Optimization Mode & Health ---
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
                    st.rerun()
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

st.sidebar.markdown("---")
st.sidebar.subheader("Engine Health")
if st.sidebar.button("Refresh Health"):
    try:
        h_resp = requests.get(f"{API_BASE}/optimize/health")
        if h_resp.status_code == 200:
            st.sidebar.json(h_resp.json())
    except:
        st.sidebar.error("Health API offline")

# --- MAIN AREA ---

tabs = st.tabs(["Live Recommendation", "Preview Loop", "Governance & KPI"])

batch_files = []
if os.path.exists(BATCH_DIR):
    batch_files = sorted([f.replace(".csv", "") for f in os.listdir(BATCH_DIR) if f.endswith(".csv")])

# 1. LIVE RECOMMENDATION TAB
with tabs[0]:
    if not batch_files:
        st.warning("No batch data found. Please run 'make data' first.")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            selected_batch = st.selectbox("Select Batch", batch_files, key="live_batch")
            df = pd.read_csv(os.path.join(BATCH_DIR, f"{selected_batch}.csv"))
            ts_options = df['ts'].tolist()
            selected_ts = st.select_slider("Select Timestamp", options=ts_options, key="live_ts")
            current_row = df[df['ts'] == selected_ts].iloc[0]
            
            st.subheader("Optimizer Tuning (Hints)")
            h_iters = st.slider("Max Iterations", 1, 20, 8)
            h_temp = st.slider("Temp Step (delta)", 0.1, 2.0, 1.0)
            h_flow = st.slider("Flow Step (delta)", 0.05, 0.5, 0.25)
            
            if st.button("Recommend Setpoints", type="primary"):
                rec_resp = requests.post(f"{API_BASE}/optimize/recommend", json={
                    "batch_id": selected_batch,
                    "ts": selected_ts,
                    "hints": {
                        "max_iters": h_iters,
                        "delta_temp": h_temp,
                        "delta_flow": h_flow
                    }
                })
                if rec_resp.status_code == 200:
                    st.session_state['recommendation'] = rec_resp.json()
                    st.success("Recommendation Received")
                else:
                    st.error("Failed to get recommendation")

        with col2:
            if 'recommendation' in st.session_state:
                rec = st.session_state['recommendation']
                st.subheader("Target Setpoints")
                c1, c2, c3 = st.columns(3)
                c1.metric("Temperature (°C)", rec['setpoints']['temperature'], delta=round(rec['nudge_applied']['temperature'], 2))
                c2.metric("Flow (L/min)", rec['setpoints']['flow'], delta=round(rec['nudge_applied']['flow'], 2))
                c3.metric("Compute Time", f"{rec['compute_ms']} ms")
                
                st.info(f"**Rationale:** {rec['rationale']}")
                
                st.subheader("Objective Breakdown")
                breakdown = rec['objective_breakdown']
                st.bar_chart(pd.Series({k: v for k, v in breakdown.items() if k != 'total'}))
                
                st.subheader("Constraint Verification")
                st.write(f"Within Bounds: {rec['within_bounds']}")
                st.json(rec['constraints'])
            else:
                st.info("Select a timestamp and click 'Recommend Setpoints' to see results.")

# 2. PREVIEW LOOP TAB
with tabs[1]:
    st.header("Pseudo-NMPC Preview")
    if not batch_files:
        st.warning("No batch data found.")
    else:
        p_col1, p_col2 = st.columns([1, 3])
        with p_col1:
            p_batch = st.selectbox("Select Batch", batch_files, key="prev_batch")
            p_horizon = st.slider("Horizon Steps", 10, 50, 20)
            p_step = st.slider("Step Interval (sec)", 2, 10, 5)
            
            if st.button("Run Preview Loop", type="primary"):
                with st.spinner("Simulating future steps..."):
                    p_resp = requests.get(f"{API_BASE}/optimize/preview", params={
                        "batch_id": p_batch,
                        "window": p_horizon,
                        "step_sec": p_step
                    })
                    if p_resp.status_code == 200:
                        st.session_state['preview'] = p_resp.json()
                    else:
                        st.error("Preview simulation failed")
        
        with p_col2:
            if 'preview' in st.session_state:
                prev = st.session_state['preview']
                st.caption(f"Note: {prev['note']} | Compute: {prev['compute_ms']}ms")
                
                pts = prev['points']
                pdf = pd.DataFrame([
                    {
                        "ts": p['ts'],
                        "T_actual": p['state']['temperature'],
                        "T_rec": p['setpoints']['temperature'],
                        "T_lower": p['bounds']['temperature'][0],
                        "T_upper": p['bounds']['temperature'][1],
                        "F_actual": p['state']['flow'],
                        "F_rec": p['setpoints']['flow'],
                        "F_lower": p['bounds']['flow'][0],
                        "F_upper": p['bounds']['flow'][1],
                        "Objective": p['objective_total']
                    } for p in pts
                ])
                pdf['ts'] = pd.to_datetime(pdf['ts'])
                pdf = pdf.set_index('ts')
                
                st.subheader("Temperature Preview")
                st.line_chart(pdf[['T_actual', 'T_rec', 'T_lower', 'T_upper']])
                
                st.subheader("Flow Preview")
                st.line_chart(pdf[['F_actual', 'F_rec', 'F_lower', 'F_upper']])
                
                st.subheader("Predicted Objective (Lower is Better)")
                st.area_chart(pdf['Objective'])
            else:
                st.info("Run a preview loop to see simulated results.")

# 3. GOVERNANCE & KPI TAB
with tabs[2]:
    st.header("KPI Ingestion & Corridor Governance")
    
    # KPI Ingestion
    with st.expander("End-of-Batch KPI Ingestion", expanded=False):
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

    st.divider()
    
    # Corridor Governance
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
                                # Clear cache by calling API or waiting
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
