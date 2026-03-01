import streamlit as st
from utils.data_utils import get_all_data

st.set_page_config(
    page_title="US International Flight Analysis", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("US International Air Travel Dashboard (1990-2025)")

st.markdown("""
### Welcome to the US-International Flight Trends Dashboard/Project
""")

if 'data_loaded' not in st.session_state:
    with st.spinner("Loading flight and economic data... this may take a moment."):
        pax_country, pax_airport, airport_map, manual_data = get_all_data()
        
        st.session_state['pax_country'] = pax_country
        st.session_state['pax_airport'] = pax_airport
        st.session_state['airport_map'] = airport_map
        st.session_state['manual_data'] = manual_data
        st.session_state['data_loaded'] = True

st.success("Data loaded successfully! Select 'Story' or 'Explore' from the sidebar to begin.")