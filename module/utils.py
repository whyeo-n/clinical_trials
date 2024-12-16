import requests
from io import BytesIO

import streamlit as st
import pandas as pd
import plotly.express as px

from math import ceil
from module.constants import *

@st.cache_data
def convert_df(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    output.seek(0)

    return output

def get_request(url, params):
    response = requests.get(url, params=params)

    if response.status_code != 200:
        st.toast(f':red[API Call Failed] {response.text}')
        
        return None

    else:
        response_body_dict = response.json()['body']

        return response_body_dict


@st.cache_data
def generate_top10_sponsor_plot(df, x:str, y:str):
    df = df.groupby(y, as_index=False).count()[[y, 'Protocol Title']].nlargest(10, 'Protocol Title').sort_values('Protocol Title', ascending=True)
    colors =  ["lightgray" if count != max(df['Protocol Title']) else "#ffaa00" for count in df['Protocol Title']]
    fig = px.bar(
        df,
        title='Top 10 Sponsors',
        x=x,
        y=y,
        orientation='h',
    )

    fig.update_xaxes(dtick=ceil(df['Protocol Title'].max()/10))
    fig.update_traces(marker=dict(color=colors))
    fig.update_layout(xaxis_title='', yaxis_title='')

    return fig

@st.cache_data
def generate_top10_site_plot(df, x:str, y:str):
    df = df['Site Name'].str.split(" :", expand=True).melt().dropna().value_counts('value').to_frame().reset_index().nlargest(10, 'count').sort_values('count', ascending=True)
    colors =  ["lightgray" if count != max(df['count']) else "#ffaa00" for count in df['count']]
    fig = px.bar(
        df,
        title='Top 10 Site',
        x=x,
        y=y,
        orientation='h',
    )

    fig.update_xaxes(dtick=ceil(df['count'].max()/10))
    fig.update_traces(marker=dict(color=colors))
    fig.update_layout(xaxis_title='', yaxis_title='')

    return fig

@st.cache_data
def generate_top10_developer_plot(df, x:str, y: str):
    df = df[y].value_counts().to_frame().reset_index().nlargest(10, 'count').sort_values('count', ascending=True)
    colors =  ["lightgray" if count != max(df['count']) else "#ffaa00" for count in df['count']]
    fig = px.bar(
        df,
        title='Top 10 Developer',
        x=x,
        y=y,
        orientation='h',
    )

    fig.update_xaxes(dtick=ceil(df['count'].max()/10))
    fig.update_traces(marker=dict(color=colors))
    fig.update_layout(xaxis_title='', yaxis_title='')

    return fig

@st.cache_data
def generate_top10_disease_plot(df):
    df = df['Target Disease Category'].value_counts().to_frame().reset_index().nlargest(10, 'count').sort_values('count', ascending=True)
    colors =  ["lightgray" if count != max(df['count']) else "#ffaa00" for count in df['count']]
    fig = px.bar(
        df,
        title='Top 10 Developer',
        x='count',
        y='Target Disease Category',
        orientation='h',
    )

    fig.update_xaxes(dtick=ceil(df['count'].max()/10))
    fig.update_traces(marker=dict(color=colors))
    fig.update_layout(xaxis_title='', yaxis_title='')

    return fig

def call_api_MdcinClincTestInfoService02(initial:bool=False, iter:int=1):
    url = BASE_URL + '/MdcinClincTestInfoService02/getMdcinClincTestInfoList02'
    params = {
        'serviceKey': st.secrets['DECODED_API_KEY'],
        'clinic_exam_title': st.session_state.get('title', ''),
        'pageNo': 1,
        'numOfRows': NUM_OF_ROWS,
        'type': 'json',
        'approval_time': st.session_state.get('date', ''),
        }

    if initial:
        response_body_dict = get_request(url, params=params)

    else:
        params['pageNo'] = iter
        response_body_dict = get_request(url, params=params)

    return response_body_dict

def call_api_ClncExamPlanDtlService2(clinical_study_id:str):
    url = BASE_URL + '/ClncExamPlanDtlService2/getClncExamPlanDtlInq2'
    params = {
        'serviceKey': st.secrets['DECODED_API_KEY'],
        'pageNo': 1,
        'numOfRows': 100,
        'type': 'json',
        'CLNC_TEST_SN': clinical_study_id
        }

    response_body_dict = get_request(url, params=params)

    return response_body_dict


def call_api_MdeqClncTestPlanAprvAplyDtlService01(initial:bool=False, iter:int=1):
    url = BASE_URL + '/MdeqClncTestPlanAprvAplyDtlService01/getMdeqClncTestPlanAprvAplyDtlInq01'
    # url = BASE_URL + '/MdeqClncTestPlanAprvAplyListService/getMdeqClncTestPlanAprvAplyListInq'
    if initial:
        params = {
            'serviceKey': st.secrets['DECODED_API_KEY'],
            'pageNo': 1,
            'numOfRows': 100,
            'type': 'json',
            }
        
        return get_request(url, params=params)
        
    else:
        params = {
            'serviceKey': st.secrets['DECODED_API_KEY'],
            'pageNo': iter,
            'numOfRows': 100,
            'type': 'json',
            }

        return get_request(url, params=params)