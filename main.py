from datetime import datetime
import pytz

import pandas as pd
import streamlit as st
from st_files_connection import FilesConnection

from module.fragments import home, medication_tirals, device_tirals

timezone = pytz.timezone('Asia/Seoul')
today = datetime.now(tz=timezone).isoformat()
st.set_page_config(
    page_title='Trial Finder',
    page_icon=':microscope:',
    layout='wide'
    )

# Session State Initialization
if 'today' not in st.session_state:
    st.session_state['today'] = today
if 'files_connection' not in st.session_state:
    st.session_state['files_connection'] = st.connection('gcs', type=FilesConnection)
if 'fetch_data_result_dict' not in st.session_state:
    st.session_state['fetch_data_result_dict'] = dict
if 'medication_api' not in st.session_state:
    st.session_state['medication_api'] = 'INITIAL'
if 'medication_details_api' not in st.session_state:
    st.session_state['medication_details_api'] = 'INITIAL'
if 'medication_df' not in st.session_state:
    st.session_state['medication_df'] = pd.DataFrame
if 'medication_filtered_df' not in st.session_state:
    st.session_state['medication_filtered_df'] = pd.DataFrame
if 'medication_details_df' not in st.session_state:
    st.session_state['medication_details_df'] = pd.DataFrame
if 'api_call_logs_df' not in st.session_state:
    st.session_state['api_call_logs_df'] = pd.DataFrame
if 'device_api' not in st.session_state:
    st.session_state['device_api'] = 'INITIAL'

# Sidebar
pages = { 
    'Home': home,
    'Medication Trials': medication_tirals, 
    'Device Trials': device_tirals,
    }

with st.sidebar.title('Navigation') as sidebar:
    page = st.sidebar.radio('Go to', options=list(pages.keys()), index=0)

# Pages
with st.spinner('Loading...'):
    pages[page]()