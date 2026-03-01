import streamlit as st
from utils.data_utils import load_data, get_daily_standings

st.set_page_config(
    page_title="Premier League Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Premier League Interactive Dashboard: 2023 - 2025")

st.markdown("""
### Welcome to the Premier League Analysis Tool
This dashboard explores team performance, attacking consistency, and home-field advantage across the last two seasons.

**How to navigate:**
* **Story**: View a guided narrative of team performance comparisons.
* **Explore**: Interact with raw metrics and specific match-day statistics.
""")

if 'data_loaded' not in st.session_state:
    with st.spinner("Loading season data..."):
        df_2324, df_2425 = load_data()
        
        st.session_state['standings_2324'] = get_daily_standings(df_2324)
        st.session_state['standings_2425'] = get_daily_standings(df_2425)
        st.session_state['data_loaded'] = True

st.success("Data is ready. Select a page from the sidebar to begin.")