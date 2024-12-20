from datetime import datetime

import pandas as pd
import streamlit as st
from st_files_connection import FilesConnection

from module.fragments import medication_tirals
from module.constants import GCS_BUCKET_NAME, MEDICATION_STUDY_COLUMN_NAME

today = datetime.now().isoformat()
st.set_page_config(layout='wide')


# Session State Initialization
if 'medication_api' not in st.session_state:
    st.session_state['medication_api'] = False
if 'medication_detail_api' not in st.session_state:
    st.session_state['medication_detail'] = False
if 'device_api' not in st.session_state:
    st.session_state['device_api'] = False

medication_tirals(today)