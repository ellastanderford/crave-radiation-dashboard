import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt

# page config
st.set_page_config(layout="wide", page_title="CRAVE Telemetry Analytics")
st.title("☀️ CRAVE Project: Surface Radiation & Meteorological Dashboard")
st.markdown("Interactive QA/QC web analytics alongside automated publication-grade report generation.")

# data ingestion engine
@st.cache_data
def load_actual_bsrn_data(file_path):
    days = []
    longwave_global_data = []
    shortwave_global_data = []
    shortwave_direct_data = []
    shortwave_diffuse_data = []
    
    with open(file_path, "r") as input_file:
        for line in input_file:
            if '#' not in line:
                parts = line.split()
                longwave_global_data.append(float(parts[17]))
                shortwave_global_data.append(float(parts[14]))
                shortwave_direct_data.append(float(parts[15]))
                shortwave_diffuse_data.append(float(parts[16]))
                
                month = parts[1]
                year = parts[0]
                day = int(parts[2])
                time = float(parts[6])
                days.append(day + (time / 24.0))
                
    # converting arrays to numpy
    time_axis = np.array(days)
    sw_global_arr = np.array(shortwave_global_data)
    sw_direct_arr = np.array(shortwave_direct_data)
    sw_diffuse_arr = np.array(shortwave_diffuse_data)
    lw_global_arr = np.array(longwave_global_data)
    
    # storing in dataframe for streamlit manipulation
    df = pd.DataFrame({
        'Day_of_Month': time_axis,
        'SW_Global': sw_global_arr,
        'SW_Direct': sw_direct_arr,
        'SW_Diffuse': sw_diffuse_arr,
        'LW_Global': lw_global_arr
    })
    
    return df, month, year

# sidebar controls and month selector
st.sidebar.header("📅 Data Selection")

selected_month_name = st.sidebar.selectbox(
    "Select Analysis Month (2025):",
    options=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    index=6
)

# map the text name to default file name
month_mapping = {
    "January": "01", "February": "02", "March": "03", "April": "04",
    "May": "05", "June": "06", "July": "07", "August": "08",
    "September": "09", "October": "10", "November": "11", "December": "12"
}
target_month_num = month_mapping[selected_month_name]
target_filename = f"BSRN-PLUS-gim_2025-{target_month_num}.txt"

# dynamic file ingestion
try:
    raw_df, month, year = load_actual_bsrn_data(target_filename)
    st.sidebar.success(f"Loaded active file: {target_filename}")
except FileNotFoundError:
    st.sidebar.warning(f"{target_filename} not found. Running simulated fallback profile.")
    
    # automatically change # of days depending on month
    num_days = 30 if target_month_num in ["04", "06", "09", "11"] else (28 if target_month_num == "02" else 31)
    time_axis = np.linspace(1, num_days, 288)
    
    # shift solar intensity depending on month
    solar_intensity_modifier = 0.6 if target_month_num in ["11", "12", "01", "02"] else 1.0
    
    raw_df = pd.DataFrame({
        'Day_of_Month': time_axis,
        'SW_Global': (400 + 350 * np.sin(time_axis) + np.random.normal(0, 10, 288)) * solar_intensity_modifier,
        'SW_Direct': (300 + 250 * np.sin(time_axis) + np.random.normal(0, 10, 288)) * solar_intensity_modifier,
        'SW_Diffuse': (100 + 100 * np.sin(time_axis) + np.random.normal(0, 5, 288)) * solar_intensity_modifier,
        'LW_Global': 300 + (50 * solar_intensity_modifier) + np.random.normal(0, 5, 288)
    })
    month, year = target_month_num, "2025"

# quality assurance + quality control pipeline
clean_df = raw_df.copy()
error_values = [-999.0, -999.90]

detected_anomalies = 0
for col in ['SW_Global', 'SW_Direct', 'SW_Diffuse', 'LW_Global']:
    detected_anomalies += clean_df[col].isin(error_values).sum()
    clean_df[col] = clean_df[col].mask(clean_df[col].isin(error_values), np.nan)

# display controls
st.sidebar.markdown("---")
st.sidebar.header("⚙️ QA/QC Control Panel")
show_raw_data = st.sidebar.checkbox("Show Raw Web Streams (With Faults)", value=False)
active_df = raw_df if show_raw_data else clean_df

st.sidebar.markdown("---")
st.sidebar.header("📄 Scientific Report Engine")

if st.sidebar.button("Build Scientific Plot"):
    # generate plot 
    fig, ax = plt.subplots(figsize=(12, 8), dpi=110, facecolor='white')
    
    ax.plot(clean_df['Day_of_Month'], clean_df['SW_Global'], label='Shortwave Global', color='blue', linewidth=0.8)
    ax.plot(clean_df['Day_of_Month'], clean_df['SW_Direct'], label='Shortwave Direct', color='cyan', linewidth=0.8)
    ax.plot(clean_df['Day_of_Month'], clean_df['SW_Diffuse'], label='Shortwave Diffuse', color='green', linewidth=0.8)
    ax.plot(clean_df['Day_of_Month'], clean_df['LW_Global'], label='Longwave Global', color='red', linewidth=0.8)
    
    ax.set_title(f"GIM-BSRN Downwelling Radiometric Data ({month.zfill(2)}/{year})", fontsize=14, fontweight='bold')
    ax.set_xlabel(f"Day of Month ({month.zfill(2)}/{year})", fontsize=12)
    ax.set_ylabel("W/m^2", fontsize=12)
    ax.set_xlim(1, clean_df['Day_of_Month'].max() + 1)
    ax.set_ylim(0, 1300)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', fontsize=10)
    
    # generate table
    table_data = [
        ["Radiation Type", "Minimum", "Maximum", "Mean"],
        ["Longwave Global", f"{clean_df['LW_Global'].min():.1f}", f"{clean_df['LW_Global'].max():.1f}", f"{clean_df['LW_Global'].mean():.1f}"],
        ["Shortwave Global", f"{clean_df['SW_Global'].min():.1f}", f"{clean_df['SW_Global'].max():.1f}", f"{clean_df['SW_Global'].mean():.1f}"],
        ["Shortwave Direct", f"{clean_df['SW_Direct'].min():.1f}", f"{clean_df['SW_Direct'].max():.1f}", f"{clean_df['SW_Direct'].mean():.1f}"],
        ["Shortwave Diffuse", f"{clean_df['SW_Diffuse'].min():.1f}", f"{clean_df['SW_Diffuse'].max():.1f}", f"{clean_df['SW_Diffuse'].mean():.1f}"]
    ]
    
    cell_colors = [
        ['#f5f5f5'] * 4,
        ['#ff9999'] * 4,
        ['#add8e6'] * 4,
        ['#e0ffff'] * 4,
        ['#90ee90'] * 4
    ]
    
    stat_table = ax.table(cellText=table_data, cellColours=cell_colors, loc='bottom', cellLoc='center', bbox=[0.1, -0.4, 0.8, 0.25])
    stat_table.auto_set_font_size(False)
    stat_table.set_fontsize(10)
    plt.subplots_adjust(bottom=0.35)
    
    with st.expander("🔬 View Static Publication Export", expanded=True):
        st.pyplot(fig)

# interactive web view
st.subheader("📊 In-Browser Interactive Telemetry Explorer")
m_col1, m_col2, m_col3 = st.columns(3)

with m_col1:
    st.metric("Peak Shortwave Global", f"{clean_df['SW_Global'].max():.1f} W/m²")
with m_col2:
    st.metric("Mean Longwave Global", f"{clean_df['LW_Global'].mean():.1f} W/m²")
with m_col3:
    st.metric("Masked Sensor Flags (-999.0)", f"{detected_anomalies} anomalies")

selected_streams = st.multiselect(
    "Toggle Live Streams to Plot:",
    options=['SW_Global', 'SW_Direct', 'SW_Diffuse', 'LW_Global'],
    default=['SW_Global', 'LW_Global', 'SW_Direct', 'SW_Diffuse']
)

if selected_streams:
    fig_rad = px.line(
        active_df, 
        x='Day_of_Month', 
        y=selected_streams, 
        title="Dynamic Irradiance Trends",
        labels={"value": "Irradiance (W/m²)", "Day_of_Month": "Day of Month"},
        template="plotly_dark"
    )
    st.plotly_chart(fig_rad, use_container_width=True)