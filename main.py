from datetime import datetime
import pytz

import pandas as pd
import streamlit as st
from st_files_connection import FilesConnection

from module.fragments import medication_tirals, medication_details
from module.constants import GCS_BUCKET_NAME, MEDICATION_STUDY_COLUMN_NAME

timezone = pytz.timezone('Asia/Seoul')
today = datetime.now(tz=timezone).isoformat()
st.set_page_config(
    page_title='Trial Finder',
    page_icon=':microscope:',
    layout='wide'
    )

# Session State Initialization
if 'medication_api' not in st.session_state:
    st.session_state['medication_api'] = 'INITIAL'
if 'medication_detail_api' not in st.session_state:
    st.session_state['medication_detail_api'] = 'INITIAL'
if 'medication_df' not in st.session_state:
    st.session_state['medication_df'] = pd.DataFrame
if 'device_api' not in st.session_state:
    st.session_state['device_api'] = 'INITIAL'

medication_tirals(today)
if st.session_state['medication_api'] == 'DONE':
    medication_details()