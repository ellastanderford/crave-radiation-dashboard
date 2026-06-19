import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import io
import os

# function to load custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# load the css file
local_css("style.css")

st.title("NASA CERES Satellite Validation Engine")
st.markdown("Compare localized ground-station data against 1° x 1° grid satellite observations.")

# Safety boundary: Make sure data was initialized on the home page first
if 'clean_df' not in st.session_state:
    st.warning("⚠️ No dataset has been loaded yet. Please select a month on the main Home Page first.")
    st.stop()

clean_df = st.session_state['clean_df']
target_month_num = st.session_state['target_month_num']
month = st.session_state['month']
year = st.session_state['year']
latitude = st.session_state['latitude']
longitude = st.session_state['longitude']

# --- AUTOMATED SATELLITE DATA INGESTION ---
# The script automatically hunts your local folder for the file matching the chosen month
expected_ceres_filename = f"ceres_data/CERES_2025-{target_month_num}.csv"

ceres_df = None
if os.path.exists(expected_ceres_filename):
    try:
        ceres_df = pd.read_csv(expected_ceres_filename)
        st.sidebar.success(f"✅ Auto-loaded Satellite Data: CERES_2025-{target_month_num}.csv")
    except Exception as e:
        st.sidebar.error(f"Error reading archived CERES file: {e}")
else:
    st.sidebar.warning(f"ℹ️ No archived CERES data file found for this month at: {expected_ceres_filename}")

num_days = 31
if target_month_num in ['04', '06', '09', '11']:
    num_days = 30
elif target_month_num == '02':
    num_days = 28

st.sidebar.markdown("-----")
st.sidebar.header("Validation Controls")

# Let the user choose exactly what parameter stream they want to compare
validation_stream = st.sidebar.radio(
    "Select Radiation Parameter to Compare:",
    options=["SW_Global", "LW_Global", "SW_Direct", "SW_Diffuse"]
)

compare_toggle = st.sidebar.checkbox("Overlay Satellite Comparison Data", value=True if ceres_df is not None else False)

if st.sidebar.button("Run Validation Plot"):
    
    # Process BSRN high-resolution data down to Daily Averages for an accurate comparison
    clean_df['Integer_Day'] = clean_df['Day_of_Month'].astype(int)
    daily_bsrn = clean_df.groupby('Integer_Day').mean().reset_index()

    fig, ax = plt.subplots(figsize=(12, 7), dpi=110, facecolor='white')
    
    # Configuration dictionary mapping the user choice to specific colors and CSV column headers
    stream_config = {
        "SW_Global": {"bsrn_col": "SW_Global", "ceres_col": "CERES_SW", "label": "Shortwave Global", "bsrn_color": "blue", "ceres_color": "dodgerblue"},
        "LW_Global": {"bsrn_col": "LW_Global", "ceres_col": "CERES_LW", "label": "Longwave Global", "bsrn_color": "red", "ceres_color": "coral"},
        "SW_Direct": {"bsrn_col": "SW_Direct", "ceres_col": "CERES_DIR", "label": "Shortwave Direct", "bsrn_color": "cyan", "ceres_color": "deepskyblue"},
        "SW_Diffuse": {"bsrn_col": "SW_Diffuse", "ceres_col": "CERES_DIF", "label": "Shortwave Diffuse", "bsrn_color": "green", "ceres_color": "limegreen"}
    }
    
    cfg = stream_config[validation_stream]
    
    # 1. Plot Selected Ground-Based BSRN Daily Averages (Solid Line)
    ax.plot(
        daily_bsrn['Integer_Day'], 
        daily_bsrn[cfg["bsrn_col"]], 
        label=f'BSRN Ground {cfg["label"]} (Daily Avg)', 
        color=cfg["bsrn_color"], 
        linewidth=1.8, 
        marker='o', 
        markersize=5
    )
    
    # 2. Plot Selected Satellite-Based CERES Data if archive exists and toggle is active (Dashed Line)
    if compare_toggle and ceres_df is not None:
        if 'Day' in ceres_df.columns:
            if cfg["ceres_col"] in ceres_df.columns:
                ax.plot(
                    ceres_df['Day'], 
                    ceres_df[cfg["ceres_col"]], 
                    label=f'NASA CERES Satellite {cfg["label"]}', 
                    color=cfg["ceres_color"], 
                    linestyle='--', 
                    linewidth=2.2, 
                    marker='s', 
                    markersize=5
                )
            else:
                st.warning(f"ℹ️ Note: Target column '{cfg['ceres_col']}' not found in the uploaded archive for this specific metric comparison.")
        else:
            st.error("Error: The local archive file is missing a 'Day' column header.")

    # Dynamic layout text based on choices
    has_comparison = compare_toggle and ceres_df is not None and cfg["ceres_col"] in (ceres_df.columns if ceres_df is not None else [])
    title_text = f"GIM-BSRN vs NASA CERES {cfg['label']} Validation ({month.zfill(2)}/{year})\n" if has_comparison else f"GIM-BSRN {cfg['label']} Baseline ({month.zfill(2)}/{year})\n"
    plt.title(f"{title_text}Latitude = {latitude}° N  |  Longitude = {longitude}° W", fontsize=14, fontweight='bold')
    
    ax.set_xlabel(f"Day of Month ({month.zfill(2)}/{year})", fontsize=12)
    ax.set_ylabel("Downward Flux (W/m²)", fontsize=12)
    ax.set_xlim(1, num_days)
    ax.set_xticks(range(1, num_days + 1, 2))
    ax.set_ylim(0, 1300)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', fontsize=10, framealpha=0.95, facecolor='whitesmoke')
    
    # Render Plot Container
    with st.expander("View Comparison Plot", expanded=True):
        st.pyplot(fig)
        
        # Export setup
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
        st.download_button(
            label="💾 Download Validation Plot (PNG)",
            data=buf.getvalue(),
            file_name=f"BSRN-CERES-{validation_stream}-{month.zfill(2)}-{year}.png",
            mime="image/png"
        )