import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

#function to load custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

#load the css file
local_css("style.css")

# Updated Page Header
st.title("Scientific Analysis Report Engine")
st.markdown("Exportable Reports")

# NEW: Make sure session state is ready
if 'selected_month_name' not in st.session_state:
    st.session_state['selected_month_name'] = 'January'

# NEW: Month Selector on the secondary page sidebar as well
st.sidebar.header("Month Selection")
selected_month_name = st.sidebar.selectbox(
    "Select Analysis Month (2025):",
    options=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    key='selected_month_name'
)

# Duplicated mapping/loading logic for seamless standalone file reading on this page
month_mapping = {
    "January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06",
    "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"
}
target_month_num = month_mapping[selected_month_name]
target_filename = f"gim_data/BSRN-PLUS-gim_2025-{target_month_num}.txt"

@st.cache_data
def load_actual_bsrn_data(file_path):
    days, longwave_global_data, shortwave_global_data, shortwave_direct_data, shortwave_diffuse_data = [], [], [], [], []
    latitude, longitude = 0, 0
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
    df = pd.DataFrame({
        'Day_of_Month': np.array(days), 'SW_Global': np.array(shortwave_global_data),
        'SW_Direct': np.array(shortwave_direct_data), 'SW_Diffuse': np.array(shortwave_diffuse_data),
        'LW_Global': np.array(longwave_global_data)
    })
    return df, month, year, latitude, longitude

try:
    raw_df, month, year, latitude, longitude = load_actual_bsrn_data(target_filename)
    st.sidebar.success(f"Loaded active file: {target_filename}")
    
    clean_df = raw_df.copy()
    for col in ['SW_Global', 'SW_Direct', 'SW_Diffuse', 'LW_Global']:
        clean_df[col] = clean_df[col].mask(clean_df[col].isin([-999.0, -999.9]), np.nan)
except FileNotFoundError:
    st.sidebar.error(f"Data Loading Error: The file {target_filename} could not be found")
    st.stop()

num_days = 31
if target_month_num == '04' or target_month_num == '06' or target_month_num == '09' or target_month_num == '11':
    num_days = 30
elif target_month_num == '02':
    num_days = 28

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
        
        # --- NEW EXPORT ENGINE ---
        import io
        
        # Create an in-memory buffer to hold image bytes
        buf = io.BytesIO()
        
        # Save the figure to the buffer as a high-res PNG
        fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
        
        # Create a download button for the user
        st.download_button(
            label="💾 Download Scientific Report (PNG)",
            data=buf.getvalue(),
            # Using a hyphen here instead of a slash so your OS saves it correctly!
            file_name=f"BSRN-PLUS-GIM-{month.zfill(2)}-{year}.png",
            mime="image/png"
        )