import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# --- APP SETUP ---
st.set_page_config(page_title="RPAS Travel Log", page_icon="🚗")
st.title("🚗 RPAS Projects Travel Log")

# --- PASTE YOUR NEW GOOGLE SHEET LINK HERE ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1YFFbNzBC4XSHeIiDHjePtodpObBttpIV6QcC07g61hA/edit?gid=0#gid=0"

# --- CONNECT TO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    log_df = conn.read(spreadsheet=SHEET_URL, worksheet="Logbook", usecols=list(range(7)), ttl="0s").dropna(how="all")
except Exception as e:
    st.error(f"Could not connect to the 'Logbook' tab. Error: {e}")
    st.stop()

# Set to South African Standard Time (SAST)
now_sast = datetime.now() + timedelta(hours=2)
today_date_str = now_sast.strftime("%d-%b-%Y")
current_time_str = now_sast.strftime("%H:%M")

# --- DATA ENTRY FORM ---
st.subheader("Log a Trip")

with st.form("travel_form", clear_on_submit=True):
    employee = st.selectbox("Employee", ["Adrian", "Jannie"])
    site = st.text_input("Site Visited")
    
    col1, col2 = st.columns(2)
    with col1:
        start_odo = st.number_input("Start Odometer reading", min_value=0.0, step=1.0)
    with col2:
        end_odo = st.number_input("End Odometer reading", min_value=0.0, step=1.0)
        
    submit = st.form_submit_button("✅ Log Travel", type="primary", use_container_width=True)
    
    if submit:
        if end_odo < start_odo:
            st.error("⚠️ End Odometer cannot be less than Start Odometer! Please check your numbers.")
        elif not site:
            st.error("⚠️ Please enter the Site Visited.")
        else:
            kms_traveled = end_odo - start_odo
            
            new_trip = pd.DataFrame([{
                "Date": today_date_str,
                "Time": current_time_str,
                "Employee": employee,
                "Start Odo": start_odo,
                "End Odo": end_odo,
                "KMs Traveled": kms_traveled,
                "Site": site
            }])
            
            updated_df = pd.concat([log_df, new_trip], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, worksheet="Logbook", data=updated_df)
            
            st.cache_data.clear()
            st.cache_resource.clear()
            
            st.success(f"Successfully logged {kms_traveled} km to {site} for {employee}!")
            st.rerun()

st.divider()

# --- DAILY DASHBOARD ---
st.subheader(f"📊 Today's Summary ({today_date_str})")

if not log_df.empty:
    log_df['Date'] = log_df['Date'].astype(str)
    log_df['KMs Traveled'] = pd.to_numeric(log_df['KMs Traveled'], errors='coerce').fillna(0)
    
    today_trips = log_df[log_df['Date'] == today_date_str]
    
    if not today_trips.empty:
        adrian_trips = today_trips[today_trips['Employee'] == "Adrian"]
        jannie_trips = today_trips[today_trips['Employee'] == "Jannie"]
        
        adrian_kms = adrian_trips['KMs Traveled'].sum()
        jannie_kms = jannie_trips['KMs Traveled'].sum()
        
        adrian_sites = ", ".join(adrian_trips['Site'].dropna().unique()) if not adrian_trips.empty else "None"
        jannie_sites = ", ".join(jannie_trips['Site'].dropna().unique()) if not jannie_trips.empty else "None"
        
        dash_col1, dash_col2 = st.columns(2)
        
        with dash_col1:
            st.markdown("### Adrian")
            st.metric(label="Total KMs Today", value=f"{adrian_kms} km")
            st.write(f"**Sites Visited:** {adrian_sites}")
            
        with dash_col2:
            st.markdown("### Jannie")
            st.metric(label="Total KMs Today", value=f"{jannie_kms} km")
            st.write(f"**Sites Visited:** {jannie_sites}")
            
        st.write("---")
        st.write("**Today's Trip Log**")
        display_df = today_trips[["Time", "Employee", "Start Odo", "End Odo", "KMs Traveled", "Site"]].sort_values(by="Time", ascending=False)
        st.dataframe(display_df, hide_index=True, use_container_width=True)
    else:
        st.info("No trips logged yet today.")
else:
    st.info("No data in the logbook yet.")
