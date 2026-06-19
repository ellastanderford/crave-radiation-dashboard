#!/usr/bin/python3
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

#function to load custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

#load the css file
local_css("style.css")

#setting up the page
st.set_page_config(layout='wide', page_title='Granite Island BSRN-PLUS Radiation Data')
st.title("Monthly Radiation Plots - GIM")
st.markdown("Interactive Web Plots")

# NEW: Initialize the shared month state if it doesn't exist yet
if 'selected_month_name' not in st.session_state:
    st.session_state['selected_month_name'] = 'January'

#adding sidebar controls and a month selector
st.sidebar.header("Month Selection")
# Modified: Linked directly to session_state so both pages sync up perfectly
selected_month_name = st.sidebar.selectbox(
    "Select Analysis Month (2025):",
    options=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    key='selected_month_name'
)

#map the text name to the default file name
month_mapping = {
    "January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06",
    "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"
}
target_month_num = month_mapping[selected_month_name]
target_filename = f"gim_data/BSRN-PLUS-gim_2025-{target_month_num}.txt"

#data take-in-engine
@st.cache_data
def load_actual_bsrn_data(file_path):
    days = []
    longwave_global_data = []
    shortwave_global_data = []
    shortwave_direct_data = []
    shortwave_diffuse_data = []
    latitude = 0
    longitude = 0
    #reading the file and storing the data
    with open(file_path, "r") as input:
        for line in input:
            if '#' not in line:
                longwave_global_data.append(float(line.split()[17]))
                shortwave_global_data.append(float(line.split()[14]))
                shortwave_direct_data.append(float(line.split()[15]))
                shortwave_diffuse_data.append(float(line.split()[16]))
                month = line.split()[1]
                year = line.split()[0]
                day = int(line.split()[2])
                time = float(line.split()[6])
                days.append(day + (time / 24.0))
            if '# Latitude' in line:
                latitude = float(line.split()[2])
                longitude = float(line.split()[4])
    #converting these arrays to numpy so i can clean the data
    time_axis = np.array(days)
    sw_global_arr = np.array(shortwave_global_data)
    sw_direct_arr = np.array(shortwave_direct_data)
    sw_diffuse_arr = np.array(shortwave_diffuse_data)
    lw_global_arr = np.array(longwave_global_data)
    #storing the data in a streamlit dataframe
    df = pd.DataFrame({
        'Day_of_Month': time_axis,
        'SW_Global': sw_global_arr,
        'SW_Direct': sw_direct_arr,
        'SW_Diffuse': sw_diffuse_arr,
        'LW_Global': lw_global_arr
    })
    return df, month, year, latitude, longitude

#file ingestion... the try-except is to stop the website from crashing if it cannot find the data files
try:
    raw_df, month, year, latitude, longitude = load_actual_bsrn_data(target_filename)
    st.sidebar.success(f"Loaded active file: {target_filename}")
    data_loaded = True
except FileNotFoundError:
    st.sidebar.error(f"Data Loading Error: The file {target_filename} could not be found")
    st.sidebar.info("Please verify that the file exists or select a different month.")
    st.stop()

if data_loaded:
    # Save datasets into global state memory so the Analysis page can grab them smoothly
    st.session_state['raw_df'] = raw_df
    st.session_state['target_month_num'] = target_month_num
    st.session_state['month'] = month
    st.session_state['year'] = year
    st.session_state['latitude'] = latitude
    st.session_state['longitude'] = longitude

    #cleaning the data and tracking the anomalies (-999.0 or -999.9) which are missing data values
    clean_df = raw_df.copy()
    error_values = [-999.0, -999.9]
    detected_anomalies = 0
    for col in ['SW_Global', 'SW_Direct', 'SW_Diffuse', 'LW_Global']:
        detected_anomalies += clean_df[col].isin(error_values).sum()
        clean_df[col] = clean_df[col].mask(clean_df[col].isin(error_values), np.nan)
    
    st.session_state['clean_df'] = clean_df

    #interactive web view
    st.subheader("In-Browser Interactive Radiation Graph")
    selected_streams = st.multiselect(
        "Toggle Live Streams to Plot:",
        options=['SW_Global', 'LW_Global', 'SW_Direct', 'SW_Diffuse'], 
        default=['SW_Global', 'LW_Global', 'SW_Direct', 'SW_Diffuse']
    )
    if selected_streams:
        fig_rad = px.line(
            clean_df,
            x='Day_of_Month',
            y=selected_streams,
            title='Solar Radiation Trends',
            labels={'value': 'Radiation (W/m^2)', 'Day_of_Month': "Day of Month"},
            template="plotly_dark"
        )
        st.plotly_chart(fig_rad, use_container_width=True)
else:
    st.info("Please select a valid month containing a matching BSRN file in the sidebar to populate the analysis plot.")