import streamlit as st
from st_files_connection import FilesConnection

from module.fragments import medication_clinical_trial_search, medical_device_clinical_trial_search

st.set_page_config(layout='wide')

conn = st.connection('gcs', type=FilesConnection)
# df = conn.read('streamlit-mfds-clinical-trials/myfile.csv', input_format='csv', ttl=600)

pages_dict = {
    'Medication': medication_clinical_trial_search,
    'Medical Device': medical_device_clinical_trial_search
}

try:
    selected_page = st.sidebar.selectbox('Select', options=pages_dict.keys())
    pages_dict[selected_page]()

except Exception as e:
    st.toast(f':red[Error Occured]: {e}')