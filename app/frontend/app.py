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

st.set_page_config(page_title="GCO Engine - Phase 3", layout="wide")

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
st.caption("Phase 3 – KPI Ingestion, MARL Proposals & Human Approval")

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

tabs = st.tabs(["Optimization Loop", "Batch KPIs", "Proposals", "Versions & Diff", "Audit Log"])

batch_files = []
if os.path.exists(BATCH_DIR):
    batch_files = sorted([f.replace(".csv", "") for f in os.listdir(BATCH_DIR) if f.endswith(".csv")])

# 1. OPTIMIZATION LOOP TAB (Combined Live & Preview for brevity)
with tabs[0]:
    if not batch_files:
        st.warning("No batch data found. Please run 'make data' first.")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Single Step Recommendation")
            selected_batch = st.selectbox("Select Batch", batch_files, key="live_batch")
            df = pd.read_csv(os.path.join(BATCH_DIR, f"{selected_batch}.csv"))
            ts_options = df['ts'].tolist()
            selected_ts = st.select_slider("Select Timestamp", options=ts_options, key="live_ts")
            
            if st.button("Recommend Setpoints", type="primary"):
                rec_resp = requests.post(f"{API_BASE}/optimize/recommend", json={
                    "batch_id": selected_batch,
                    "ts": selected_ts
                })
                if rec_resp.status_code == 200:
                    st.session_state['recommendation'] = rec_resp.json()
                    st.success("Recommendation Received")
            
            st.divider()
            st.subheader("Pseudo-NMPC Preview")
            p_horizon = st.slider("Horizon Steps", 10, 50, 20)
            if st.button("Run Preview Loop"):
                with st.spinner("Simulating..."):
                    p_resp = requests.get(f"{API_BASE}/optimize/preview", params={"batch_id": selected_batch, "window": p_horizon})
                    if p_resp.status_code == 200:
                        st.session_state['preview'] = p_resp.json()

        with col2:
            if 'recommendation' in st.session_state:
                rec = st.session_state['recommendation']
                st.subheader("Target Setpoints")
                c1, c2, c3 = st.columns(3)
                c1.metric("Temperature (°C)", rec['setpoints']['temperature'], delta=round(rec['nudge_applied']['temperature'], 2))
                c2.metric("Flow (L/min)", rec['setpoints']['flow'], delta=round(rec['nudge_applied']['flow'], 2))
                c3.metric("Compute Time", f"{rec['compute_ms']} ms")
                st.info(f"**Rationale:** {rec['rationale']}")
            
            if 'preview' in st.session_state:
                prev = st.session_state['preview']
                pts = prev['points']
                pdf = pd.DataFrame([{"ts": p['ts'], "T_actual": p['state']['temperature'], "T_rec": p['setpoints']['temperature'], "T_lower": p['bounds']['temperature'][0], "T_upper": p['bounds']['temperature'][1]} for p in pts])
                pdf['ts'] = pd.to_datetime(pdf['ts'])
                st.line_chart(pdf.set_index('ts')[['T_actual', 'T_rec', 'T_lower', 'T_upper']])

# 2. BATCH KPIs TAB
with tabs[1]:
    st.header("End-of-Batch KPI Ingestion")
    k1, k2 = st.columns([1, 2])
    with k1:
        with st.form("kpi_form_p3"):
            k_batch = st.selectbox("Batch ID", batch_files, key="k_batch_p3") if batch_files else st.text_input("Batch ID")
            k_energy = st.number_input("Energy Consumed (kWh)", min_value=0.0, value=45.0)
            k_yield = st.number_input("Yield (%)", min_value=0.0, max_value=100.0, value=92.5)
            k_quality = st.checkbox("Quality Deviation Flag")
            if st.form_submit_button("Ingest KPI"):
                resp = requests.post(f"{API_BASE}/kpi/ingest", json={"batch_id": k_batch, "energy_kwh": k_energy, "yield_pct": k_yield, "quality_deviation": k_quality})
                if resp.status_code == 200:
                    data = resp.json()
                    st.success(f"KPI {data['message']}!")
                    if data['marl_proposal_created']:
                        st.info(f"MARL Proposal Generated: {data['proposal_id']}")
                    if data['anomaly_flag']:
                        st.warning("Anomaly Detected!")
                else: st.error("Ingestion failed")
    
    with k2:
        st.subheader("Recent KPI Items")
        r_resp = requests.get(f"{API_BASE}/kpi/recent", params={"limit": 10})
        if r_resp.status_code == 200:
            kpis = r_resp.json()['items']
            if kpis:
                kdf = pd.DataFrame(kpis)
                st.dataframe(kdf[['batch_id', 'energy_kwh', 'yield_pct', 'quality_deviation', 'anomaly_flag', 'ingested_at']])
            else: st.write("No KPIs yet.")

# 3. PROPOSALS TAB
with tabs[2]:
    st.header("Corridor Update Proposals (Mock MARL)")
    p_resp = requests.get(f"{API_BASE}/corridor/proposals", params={"status": "pending"})
    if p_resp.status_code == 200:
        proposals = p_resp.json()['items']
        if not proposals:
            st.info("No pending proposals found.")
        else:
            for p in proposals:
                with st.container(border=True):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.subheader(f"Proposal {p['id']}")
                        st.write(f"**Summary:** {p['evidence']['summary']}")
                        st.write(f"**Confidence:** {p['evidence']['confidence']:.2f}")
                        st.write(f"**KPI Window:** {', '.join(p['evidence']['kpi_window'])}")
                        st.markdown("**Metrics:**")
                        st.json(p['evidence']['metrics'])
                    with c2:
                        st.markdown("**Proposed Delta:**")
                        st.json(p['delta'])
                        decision = st.radio(f"Decision {p['id']}", ["approve", "reject"], horizontal=True)
                        notes = st.text_input("Approval Notes", key=f"note_{p['id']}")
                        if st.button(f"Submit Decision", key=f"btn_{p['id']}"):
                            app_resp = requests.post(f"{API_BASE}/corridor/approve", json={"proposal_id": p['id'], "decision": decision, "notes": notes})
                            if app_resp.status_code == 200:
                                st.success(f"Decision submitted: {decision}")
                                time.sleep(1)
                                st.rerun()

# 4. VERSIONS & DIFF TAB
with tabs[3]:
    st.header("Corridor Versioning & Governance")
    v_resp = requests.get(f"{API_BASE}/corridor/version")
    if v_resp.status_code == 200:
        v_data = v_resp.json()
        st.subheader(f"Current Active: {v_data['active_version']}")
        st.json(v_data['bounds'])
        
        st.divider()
        st.subheader("Version History")
        h_df = pd.DataFrame(v_data['history'])
        st.dataframe(h_df, use_container_width=True)
        
        st.divider()
        st.subheader("Diff Viewer")
        all_versions = [h['version'] for h in v_data['history']]
        if len(all_versions) >= 2:
            col_f, col_t = st.columns(2)
            from_v = col_f.selectbox("From Version", all_versions, index=max(0, len(all_versions)-2))
            to_v = col_t.selectbox("To Version", all_versions, index=len(all_versions)-1)
            if st.button("Compare Versions"):
                d_resp = requests.get(f"{API_BASE}/corridor/diff", params={"from_v": from_v, "to_v": to_v})
                if d_resp.status_code == 200:
                    diff = d_resp.json()
                    st.write(f"**Impact Hints:**")
                    st.json(diff['impact_hints'])
                    st.write("**Boundary Changes:**")
                    st.json(diff['changes'])
        else:
            st.info("At least two versions are required for comparison.")

# 5. AUDIT LOG TAB
with tabs[4]:
    st.header("System Audit Trail")
    a_resp = requests.get(f"{API_BASE}/corridor/audit", params={"limit": 50})
    if a_resp.status_code == 200:
        audits = a_resp.json()['items']
        adf = pd.DataFrame(audits)
        if not adf.empty:
            st.dataframe(adf[['at', 'type', 'data']], use_container_width=True)
        else: st.write("Audit log is empty.")
