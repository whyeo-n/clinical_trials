import requests
from io import BytesIO

import streamlit as st
import pandas as pd
import plotly.express as px

from math import ceil
from time import sleep
from module.constants import STUDY_COLUMN_NAME, STUDY_DETAILS_COLUMN_NAME

@st.cache_data
def convert_df(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    output.seek(0)

    return output

@st.cache_data
def get_request(url, params):

    return requests.get(url, params=params)


@st.cache_data
def generate_top10_sponsor_plot(df):
    df = df.groupby('Sponsor', as_index=False).count()[['Sponsor', 'Protocol Title']].nlargest(10, 'Protocol Title').sort_values('Protocol Title', ascending=True)
    colors =  ["lightgray" if count != max(df['Protocol Title']) else "#ffaa00" for count in df['Protocol Title']]
    fig = px.bar(
        df,
        title='Top 10 Sponsors',
        x='Protocol Title',
        y='Sponsor',
        orientation='h',
    )

    fig.update_xaxes(dtick=5)
    fig.update_traces(marker=dict(color=colors))
    fig.update_layout(xaxis_title='', yaxis_title='')

    return fig

@st.cache_data
def generate_top10_site_plot(df):
    df = df['Site Name'].str.split(" :", expand=True).melt().dropna().value_counts('value').to_frame().reset_index().nlargest(10, 'count').sort_values('count', ascending=True)
    colors =  ["lightgray" if count != max(df['count']) else "#ffaa00" for count in df['count']]
    fig = px.bar(
        df,
        title='Top 10 Site',
        x='count',
        y='value',
        orientation='h',
    )

    fig.update_xaxes(dtick=5)
    fig.update_traces(marker=dict(color=colors))
    fig.update_layout(xaxis_title='', yaxis_title='')

    return fig

@st.cache_data
def generate_top10_developer_plot(df):
    df = df['Original Developer of the IP'].value_counts().to_frame().reset_index().nlargest(10, 'count').sort_values('count', ascending=True)
    colors =  ["lightgray" if count != max(df['count']) else "#ffaa00" for count in df['count']]
    fig = px.bar(
        df,
        title='Top 10 Developer',
        x='count',
        y='Original Developer of the IP',
        orientation='h',
    )

    fig.update_xaxes(dtick=5)
    fig.update_traces(marker=dict(color=colors))
    fig.update_layout(xaxis_title='', yaxis_title='')

    return fig

def generate_medication_clinical_trial_dataframe(form):
    progress_bar = form.progress(0, text='Idle...')

    URL = 'http://apis.data.go.kr/1471000/MdcinClincTestInfoService02/getMdcinClincTestInfoList02'
    PARAMS = {
        'serviceKey': st.secrets['DECODED_API_KEY'],
        'clinic_exam_title': st.session_state.get('title', ''),
        'pageNo': 1,
        'numOfRows': 100,
        'type': 'json',
        'approval_time': st.session_state.get('date', ''),
        }
    
    response = get_request(URL, params=PARAMS)

    if response.status_code != 200:
        st.toast(f'Error occured, status_code: {response.status_code}, response: {response.text}')

    else:
        try:
            initial_result = response.json()['body']['items']
            total_count = response.json()['body']['totalCount']
            max_page = int(ceil(total_count / PARAMS['numOfRows']))
            
            # 100 건 이내인 경우
            if max_page == 1:
                i = 1
                while i < 100:
                    sleep(0.01)
                    progress_bar.progress(i, text='Processing')
                    i += 1
                progress_bar.progress(100, text='Done')

            # 100 건 초과 시
            else:
                i = 2
                while i < max_page:
                    progress_bar.progress(i / max_page, text='Processing')
                    PARAMS['pageNo'] = i

                    response = get_request(URL, params=PARAMS)
                    if response.status_code != 200:
                        st.toast(f'Error occured, status_code: {response.status_code}, response: {response.text}')
                    else:
                        initial_result.extend(response.json()['body']['items'])

                    i += 1
                progress_bar.progress(100, text='Done')

            df = pd.DataFrame(initial_result)
            df.columns = STUDY_COLUMN_NAME
            
            return df
    
        except KeyError as e:
                if str(e) == "'items'":
                    st.toast('검색 결과가 존재하지 않습니다.')
                else:
                    st.toast(f'KeyError: {e}')

def generate_medication_clinical_trial_details_dataframe(form):
    URL = 'http://apis.data.go.kr/1471000/ClncExamPlanDtlService2/getClncExamPlanDtlInq2'
    PARAMS = {
        'serviceKey': st.secrets['DECODED_API_KEY'],
        'pageNo': 1,
        'numOfRows': 100,
        'type': 'json',
        'CLNC_TEST_SN': ''
        }

    # progress_bar
    progress_bar = form.progress(0, text='Idle...')

    df = st.session_state.get('medication_clinical_trial_dataframe', pd.DataFrame())

    temp_list = []

    i = 1
    while i < len(df['Clinical Trial ID']):
        PARAMS['CLNC_TEST_SN'] = df['Clinical Trial ID'][i]
        response = get_request(URL, params=PARAMS)
        progress_bar.progress(i / len(df['Clinical Trial ID']), text='Processing')

        if response.status_code != 200:
            st.toast(f'Error occured, status_code: {response.status_code}, response: {response.text}')

        else:
            # 상세 정보가 존재하지 않는 경우에 대한 예외처리
            try:
                temp_list.append(pd.DataFrame(response.json()['body']['items']))

            except KeyError as e:
                if str(e) == "'items'":
                    st.toast(f'ID {PARAMS['CLNC_TEST_SN']} Study의 상세 정보가 존재하지 않습니다.')
                else:
                    st.toast(f'{PARAMS['CLNC_TEST_SN']} KeyError: {e}')
                continue
    
        i += 1

    progress_bar.progress(100, text='Done')

    df = pd.concat(temp_list)
    df.columns = STUDY_DETAILS_COLUMN_NAME

    return df