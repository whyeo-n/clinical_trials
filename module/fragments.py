import pandas as pd
import plotly.express as px
import streamlit as st

from math import ceil
from time import sleep
from module.utils import *
from module.constants import STUDY_COLUMN_NAME, STUDY_DETAILS_COLUMN_NAME

@st.fragment
def medication_clinical_trial_search():
    st.header('의약품 임상시험 :blue[승인 정보 조회]')
    columns = st.columns(2)
    form = columns[0].form(key='medication_clinical_trial_info_search')
    form_columns = form.columns(2)
    form_columns[0].text_input('Protocol Title Keyword', key='title')
    form_columns[1].text_input('IND Approval Date (Available Input: :blue[YYYY] | :blue[YYYY]:orange[MM] | :blue[YYYY]:orange[MM]:green[DD])', placeholder='YYYYMMDD', max_chars=8, key='date')

    if form.form_submit_button('Search'):
        df = generate_medication_clinical_trial_dataframe(form)

        # session state에 저장
        st.session_state['medication_clinical_trial_dataframe'] = df

        # Exapmle Dataframe
        columns[0].dataframe(df.reset_index(drop=True))

        # Download Button
        columns[0].download_button(
            label="Download",
            key='clinical_trial_info_download_button',
            data=convert_df(df),
            file_name=f'clinical_trial_info.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        # top10_trial_count_per_sponsor_fig
        top10_trial_count_per_sponsor_fig = generate_top10_sponsor_plot(df)
        columns[1].plotly_chart(top10_trial_count_per_sponsor_fig)

        # top10_trial_count_per_site_fig
        top10_trial_count_per_site_fig = generate_top10_site_plot(df)
        columns[1].plotly_chart(top10_trial_count_per_site_fig)

        # 상세항목 검색
        medication_clinical_trial_details_search()



@st.fragment
def medication_clinical_trial_details_search():
    st.header('의약품 임상시험 승인 :blue[상세 정보 조회] (2019~)')
    st.write('조회된 모든 Protocol에 대한 정보를 확인하려면 버튼을 클릭하세요. 특정한 Protocol에 대한 정보를 확인하려면 Clinical Trial ID를 직접 입력하세요.')
    
    columns = st.columns(2)
    form = columns[0].form(key='medication_clinical_trial_details_info_search')
    form_columns = form.columns(2)

    if form.form_submit_button(label='Search Details'):
        df = generate_medication_clinical_trial_details_dataframe(form)

        form.dataframe(df.reset_index(drop=True))

        st.download_button(
            label='Download',
            key="clinical_trial_details_info_excel_download_button",
            data=convert_df(df),
            file_name=f'clinical_trial_details_info.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        # top10_trial_count_per_site_fig
        top10_trial_count_per_site_fig = generate_top10_developer_plot(df)
        columns[1].plotly_chart(top10_trial_count_per_site_fig)