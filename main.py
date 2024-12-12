import streamlit as st
from module.fragments import medication_clinical_trial_search

try:
    st.set_page_config(layout='wide')
    st.title('Clinical Trial Information :blue[Finder]')
    st.write('식품의약품 안전처의 의약품 임상시험 승인 정보를 검색하려면 :blue[임상시험 제목 및/또는 승인년월일]을 입력하고 버튼을 클릭하세요')

    medication_clinical_trial_search()

except Exception as e:
    st.toast(f':red[Error Occured]: {e}')