#!/usr/bin/python3

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt

#function to load custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

#load the css file
local_css("style.css")

#setting up the page
st.set_page_config(layout='wide', page_title='Granite Island BSRN-PLUS Radiation Data')
st.title("Monthly Radiation Plots - GIM")
st.markdown("Interactive Web Plots | Automated Report Generation")

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

#adding sidebar controls and a month selector
st.sidebar.header("Month Selection")
selected_month_name = st.sidebar.selectbox(
    "Select Analysis Month (2025):",
    options=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    index = 0
)
#map the text name to the default file name
month_mapping = {
    "January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06",
    "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"
}
target_month_num = month_mapping[selected_month_name]
target_filename = f"BSRN-PLUS-gim_2025-{target_month_num}.txt"
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
    num_days = 31
    if target_month_num == '04' or target_month_num == '06' or target_month_num == '09' or target_month_num == '11':
        num_days = 30
    elif target_month_num == '02':
        num_days = 28

    #cleaning the data and tracking the anomalies (-999.9 or -999.0) which are missing data values
    clean_df = raw_df.copy()
    error_values = [-999.0, -999.9]
    detected_anomalies = 0
    for col in ['SW_Global', 'SW_Direct', 'SW_Diffuse', 'LW_Global']:
        detected_anomalies += clean_df[col].isin(error_values).sum()
        clean_df[col] = clean_df[col].mask(clean_df[col].isin(error_values), np.nan)
    
    #sidebar and display controls
    st.sidebar.markdown("-----")
    st.sidebar.header("Report Engine")
    if st.sidebar.button("Build Scientific Plot"):
        #generates the plot if the button is clicked
        fig, ax = plt.subplots(figsize=(12, 8), dpi=110, facecolor='white')
        ax.plot(clean_df['Day_of_Month'], clean_df['SW_Global'], label='Shortwave Global', color='blue', linewidth=0.8)
        ax.plot(clean_df['Day_of_Month'], clean_df['SW_Direct'], label='Shortwave Direct', color='cyan', linewidth=0.8)
        ax.plot(clean_df['Day_of_Month'], clean_df['SW_Diffuse'], label='Shortwave Diffuse', color='green', linewidth=0.8)
        ax.plot(clean_df['Day_of_Month'], clean_df['LW_Global'], label='Longwave Global', color='red', linewidth=0.8)
        plt.title(f"GIM-BSRN Downwelling Radiometric Data ({month.zfill(2)}/{year})\nLatitude = {latitude} Longitude={longitude}", fontsize=20, fontweight='bold')
        ax.set_xlabel(f"Day of Month ({month.zfill(2)}/{year})", fontsize=12)
        ax.set_ylabel("W/m^2", fontsize=12)
        ax.set_xlim(1, clean_df['Day_of_Month'].max() + 1)
        ax.set_ylim(0, 1300)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(loc='upper right', fontsize=10)
        #generates minimum, maximum, mean, standard deviation, and standard error for data
        if not clean_df['LW_Global'].isna().all():
            LW_global_min = round(clean_df['LW_Global'].min(), 2)
            LW_global_max = round(clean_df['LW_Global'].max(), 2)
            LW_global_mean = round(clean_df['LW_Global'].mean(), 2)
            LW_global_std = round(clean_df['LW_Global'].std(), 2)
            LW_global_err = round(clean_df['LW_Global'].std() / np.sqrt(len(clean_df['LW_Global'])), 2)
        else:
            LW_global_min = LW_global_max = LW_global_mean = LW_global_std = LW_global_err = "N/A"
        if not clean_df['SW_Global'].isna().all():
            SW_global_min = round(clean_df['SW_Global'].min(), 2)
            SW_global_max = round(clean_df['SW_Global'].max(), 2)
            SW_global_mean = round(clean_df['SW_Global'].mean(), 2)
            SW_global_std = round(clean_df['SW_Global'].std(), 2)
            SW_global_err = round(clean_df['SW_Global'].std() / np.sqrt(len(clean_df['SW_Global'])), 2)
        else:
            SW_global_min = SW_global_max = SW_global_mean = SW_global_std = SW_global_err = "N/A"
        if not clean_df['SW_Direct'].isna().all():
            SW_direct_min = round(clean_df['SW_Direct'].min(), 2)
            SW_direct_max = round(clean_df['SW_Direct'].max(), 2)
            SW_direct_mean = round(clean_df['SW_Direct'].mean(), 2)
            SW_direct_std = round(clean_df['SW_Direct'].std(), 2)
            SW_direct_err = round(clean_df['SW_Direct'].std() / np.sqrt(len(clean_df['SW_Direct'])), 2)
        else:
            SW_direct_min = SW_direct_max = SW_direct_mean = SW_direct_std = SW_direct_err = "N/A"
        if not clean_df['SW_Diffuse'].isna().all():
            SW_diffuse_min = round(clean_df['SW_Diffuse'].min(), 2)
            SW_diffuse_max = round(clean_df['SW_Diffuse'].max(), 2)
            SW_diffuse_mean = round(clean_df['SW_Diffuse'].mean(), 2)
            SW_diffuse_std = round(clean_df['SW_Diffuse'].std(), 2)
            SW_diffuse_err = round(clean_df['SW_Diffuse'].std() / np.sqrt(len(clean_df['SW_Diffuse'])), 2)
        else:
            SW_diffuse_min = SW_diffuse_max = SW_diffuse_mean = SW_diffuse_std = SW_diffuse_err = "N/A"

        table_data = [
            ["Radiation Type", "Minimum", "Maximum", "Mean", "Standard Deviation", "Standard Error"],
            ["Longwave Global", str(LW_global_min), str(LW_global_max), str(LW_global_mean), str(LW_global_std), str(LW_global_err)],
            ["Shortwave Global", str(SW_global_min), str(SW_global_max), str(SW_global_mean), str(SW_global_std), str(SW_global_err)],
            ["Shortwave Direct", str(SW_direct_min), str(SW_direct_max), str(SW_direct_mean), str(SW_direct_std), str(SW_direct_err)],
            ["Shortwave Diffuse", str(SW_diffuse_min), str(SW_diffuse_max), str(SW_diffuse_mean), str(SW_diffuse_std), str(SW_diffuse_err)]
        ]
        cell_colors = [
            ['whitesmoke', 'whitesmoke', 'whitesmoke', 'whitesmoke', 'whitesmoke', 'whitesmoke'],
            ['salmon', 'salmon', 'salmon', 'salmon', 'salmon', 'salmon'],
            ['lightblue', 'lightblue', 'lightblue', 'lightblue', 'lightblue', 'lightblue'],
            ['lightcyan', 'lightcyan', 'lightcyan', 'lightcyan', 'lightcyan', 'lightcyan'],
            ['lightgreen', 'lightgreen', 'lightgreen', 'lightgreen', 'lightgreen', 'lightgreen']
        ]
        stat_table = ax.table(cellText=table_data, cellColours=cell_colors, loc='bottom', cellLoc='center', bbox=[0.1, -0.45, 0.8, 0.3])
        stat_table.auto_set_font_size(False)
        stat_table.set_fontsize(8)
        cell_dict = stat_table.get_celld()
        for row in range(len(table_data)):
            for col in range(len(table_data[0])):
                cell_dict[(row, col)].set_height(0.05)
        with st.expander("View Static Export Form", expanded=True):
            st.pyplot(fig)

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