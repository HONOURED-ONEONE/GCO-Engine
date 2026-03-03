import streamlit as st
import pandas as pd

def render_bounds_chart(df, param, bounds, rec_val=None, rec_ts=None):
    st.subheader(f"{param.capitalize()} vs Corridor Bounds")
    
    # Prepare data for plotting
    plot_df = df.copy()
    plot_df['lower'] = bounds['lower']
    plot_df['upper'] = bounds['upper']
    
    # Simple line chart using streamlit native
    st.line_chart(plot_df.set_index('ts')[[param, 'lower', 'upper']])
    
    if rec_val is not None:
        st.info(f"Recommended {param}: {rec_val}")

def render_gauge(label, value, lower, upper):
    st.metric(label=label, value=value, delta=f"Range: [{lower}, {upper}]", delta_color="normal")
