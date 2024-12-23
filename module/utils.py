import json
import requests
from datetime import datetime

from gcsfs.core import GCSFile
from st_files_connection import FilesConnection

import streamlit as st
import pandas as pd
import plotly.express as px

from math import ceil
from module.constants import *

@st.cache_data
def get_request(url: str, params: dict) -> dict:
    '''Make a GET request and return the response body if successful.'''
    
    try:
        # Make the GET request
        response = requests.get(url, params=params)
        
        # Check if the response status is successful
        response.raise_for_status()
        
        # Return the response body from the JSON response
        return response.json().get('body', {})
    
    except requests.exceptions.HTTPError as http_err:
        st.error(f':red[API Call Failed] HTTP error occurred: {http_err}', icon='🚨')
    except requests.exceptions.RequestException as req_err:
        st.error(f':red[API Call Failed] Request error occurred: {req_err}', icon='🚨')
    except Exception as err:
        st.error(f':red[API Call Failed] An unexpected error occurred: {err}', icon='🚨')
    
    # Return None if an error occurred
    return None

def check_api_call_logs():
    try:
        # Attempt to read the api_call_logs.json file from GCS
        st.session_state['api_call_logs_df'] = st.session_state['files_connection'].read(f'{GCS_BUCKET_NAME}/api_call_logs.json', input_format='jsonl', dtype=str)
        # Key Error Check
        st.session_state['api_call_logs_df'][['date', 'time']]
        result, e = Function_Status.SUCCESS, None
        
        return result, e
    except FileNotFoundError as e:
        # If reading fails, create a new empty DataFrame
        st.session_state['api_call_logs_df'] = pd.DataFrame(columns=['date', 'time'], dtype=str)
        # Save the empty DataFrame to GCS
        result, e = update_data(dataframe=st.session_state['api_call_logs_df'], conn=st.session_state['files_connection'], file_path=f'{GCS_BUCKET_NAME}/api_call_logs.json')
        
        return result, e
    except KeyError as e:
        st.session_state['api_call_logs_df'] = pd.DataFrame(columns=['date', 'time'], dtype=str)
        # Save the empty DataFrame to GCS
        result, e = update_data(dataframe=st.session_state['api_call_logs_df'], conn=st.session_state['files_connection'], file_path=f'{GCS_BUCKET_NAME}/api_call_logs.json')

        return result, e

def fetch_data(conn:FilesConnection, api_call_logs_df:pd.DataFrame, today:datetime, status) -> None:
    '''Function to save DataFrame to Json in GCS.'''
    
    result_dict = {
            'total_result': Function_Status.SUCCESS,
            'medication': {
                'status': Function_Status.SUCCESS,
                'message': 'Medication Trial Data updated successfully.'
            },
            'device': {
                'status': Function_Status.SUCCESS,
                'message': 'Device Trial Data updated successfully.'
            },
            'api_call_logs': {
                'status': Function_Status.SUCCESS,
                'message': 'API Call Logs updated successfully.'
            }
        }

    # Update Medication Trial Data
    status.info('Updating Medication Trial Data...')
    fetched_medication_trial_df = fetch_medication_trial_data(status)
    medication_result, medication_e = update_data(dataframe=fetched_medication_trial_df, conn=conn, file_path=f'{GCS_BUCKET_NAME}/medication_trial_info.json')

    # Update Device Trial Data
    status.info('Updating Device Trial Data...')
    fetched_device_trial_df = fetch_device_trial_data(status)
    device_result, device_e = update_data(dataframe=fetched_device_trial_df, conn=conn, file_path=f'{GCS_BUCKET_NAME}/device_trial_info.json')

    # Update API Call Logs with the current date and time
    max_row = api_call_logs_df.shape[0]
    api_call_logs_df.loc[max_row, 'date'] = today.split('T')[0]
    api_call_logs_df.loc[max_row, 'time'] = today.split('T')[1]
    api_call_logs_result, api_call_logs_e = update_data(dataframe=api_call_logs_df, conn=conn, file_path=f'{GCS_BUCKET_NAME}/api_call_logs.json')

    if medication_result == Function_Status.FAIL:
        result_dict.total_result = Function_Status.FAIL
        result_dict.medication.status = Function_Status.FAIL
        result_dict.medication.message = f'Medication API Failed: {str(medication_e)}]'
    
    if device_result == Function_Status.FAIL:
        result_dict.total_result = Function_Status.FAIL
        result_dict.device.status = Function_Status.FAIL
        result_dict.device.message = f'Device API Failed: {str(device_e)}]'
    
    if api_call_logs_result == Function_Status.FAIL:
        result_dict.total_result = Function_Status.FAIL
        result_dict.api_call_logs.status = Function_Status.FAIL
        result_dict.api_call_logs.message = f'API Call Log Update Failed: {str(api_call_logs_e)}]'

    st.session_state['fetch_data_result_dict'] = result_dict

    return None

def fetch_medication_trial_data(status):
    '''Fetch and return all medication trial data from the API.'''
    url = f'{BASE_URL}/MdcinClincTestInfoService02/getMdcinClincTestInfoList02'

    # Set up the parameters for the request
    params = {
        'serviceKey': st.secrets['DECODED_API_KEY'],
        'type': 'json',
    }

    # Initialize the list to store all items
    total_items = []

    # Fetch the total count first (to determine the number of pages)
    params['pageNo'] = 1
    params['numOfRows'] = 1  # Fetch 1 item to get the total count
    response_body_dict = get_request(url, params)

    if response_body_dict is None:
        status.error(':red[Failed to fetch initial data. Please check your API.]', icon='🚨')
        return pd.DataFrame()  # Return an empty DataFrame if the request fails

    totalCount = response_body_dict.get('totalCount', 0)
    if totalCount == 0:
        status.error(':orange[No data available from the API.]', icon='⚠️')
        return pd.DataFrame()  # Return an empty DataFrame if no data is available

    num_of_pages = ceil(totalCount / 100)  # Calculate the number of pages

    progress_bar = status.progress(value=0, text='Fetching start')
    # Fetch data from all pages
    for page_no in range(1, num_of_pages + 1):
        progress_bar.progress(page_no / num_of_pages, text=f'Fetching data from page {page_no}...')
        params['pageNo'] = page_no
        params['numOfRows'] = 100  # Fetch 100 items per page

        response_body_dict = get_request(url, params)

        if response_body_dict is None:
            status.error(f':red[Failed to fetch data for page {page_no}. Check the API or network.]', icon='🚨')
            continue  # Skip to the next page if the request fails
        
        items = response_body_dict.get('items', [])

        if items:  # Only add if there are items
            total_items.extend(items)
        else:
            status.error(f':orange[No items found for page {page_no}.]', icon='⚠️')
    
    progress_bar.progress(1.0, text=f'Fetching complete.')

    # Return the collected items as a DataFrame
    output_dataframe = pd.DataFrame(total_items)
    output_dataframe.columns = MEDICATION_STUDY_COLUMN_NAME
    return output_dataframe

def decoding_json_bytes(json_file: GCSFile) -> list:
    '''Decode the JSON bytes and return the list of JSON objects.'''
    json_bytes = f'[{json_file.read().decode('utf-8').replace('}\n{', '},{')}]'
    
    return json.loads(json_bytes)

def fetch_device_trial_data(status):
    '''Fetch and return all medical device trial data from the API.'''
    
    url = f'{BASE_URL}/MdeqClncTestPlanAprvAplyDtlService01/getMdeqClncTestPlanAprvAplyDtlInq01'

    # Set up the parameters for the request
    params = {
        'serviceKey': st.secrets['DECODED_API_KEY'],
        'type': 'json',
    }

    # Initialize the list to store all items
    total_items = []

    # Fetch the total count first (to determine the number of pages)
    params['pageNo'] = 1
    params['numOfRows'] = 1  # Fetch 1 item to get the total count
    response_body_dict = get_request(url, params)

    if response_body_dict is None:
        status.error(':red[Failed to fetch initial data. Please check your API.]', icon='🚨')
        return pd.DataFrame()  # Return an empty DataFrame if the request fails

    totalCount = response_body_dict.get('totalCount', 0)
    if totalCount == 0:
        status.error(':orange[No data available from the API.]', icon='⚠️')
        return pd.DataFrame()  # Return an empty DataFrame if no data is available

    num_of_pages = ceil(totalCount / 100)  # Calculate the number of pages

    progress_bar = status.progress(value=0, text='Fetching start')
    # Fetch data from all pages
    for page_no in range(1, num_of_pages + 1):
        progress_bar.progress(page_no / num_of_pages, text=f'Fetching data from page {page_no}...')
        params['pageNo'] = page_no
        params['numOfRows'] = 100  # Fetch 100 items per page

        response_body_dict = get_request(url, params)

        if response_body_dict is None:
            status.error(f':red[Failed to fetch data for page {page_no}. Check the API or network.]', icon='🚨')
            continue  # Skip to the next page if the request fails
        
        items = response_body_dict.get('items', [])

        if items:  # Only add if there are items
            total_items.extend(items)
        else:
            status.error(f':orange[No items found for page {page_no}.]', icon='⚠️')
    progress_bar.progress(1.0, text='Fetching complete')

    # Return the collected items as a DataFrame
    output_dataframe = pd.DataFrame(total_items)
    output_dataframe.columns = MEDICAL_DEVICE_STUDY_COLUMN_NAME
    return output_dataframe

# @st.cache_data
def fetch_medication_details_data(dataframe: pd.DataFrame):
    '''Fetch and return details data from the API.'''
    
    url = f'{BASE_URL}/ClncExamPlanDtlService2/getClncExamPlanDtlInq2'
    
    # Set up the parameters for the request
    params = {
        'serviceKey': st.secrets['DECODED_API_KEY'],
        'pageNo': 1,
        'numOfRows': 100,
        'type': 'json',
        }

    # Initialize the list to store all items
    total_items = []

    # Fetch data for each ids
    for i in dataframe.index:
        params['CLNC_TEST_SN'] = dataframe.loc[i,'Clinical Trial ID']
        
        response_body_dict = get_request(url, params)
        
        if response_body_dict is None:
            st.toast(f':red[Failed to fetch data for {params['CLNC_TEST_SN']}. Check the API or network.]', icon='🚨')
            continue  # Skip to the next page if the request fails
        
        items = response_body_dict.get('items', [])
        
        if items:  # Only add if there are items
            total_items.extend(items)
        else:
            st.toast(f':orange[No items found for page {params['CLNC_TEST_SN']}.]', icon='⚠️')
    
    # Return the collected items as a DataFrame
    output_dataframe = pd.DataFrame(total_items).fillna('None')
    output_dataframe.columns = MEDICATION_STUDY_DETAILS_COLUMN_NAME
    return output_dataframe

def update_data(dataframe: pd.DataFrame, conn: FilesConnection, file_path: str) -> tuple[Function_Status, Exception]:
    '''Function to save DataFrame to Json in GCS.'''
    
    try:
        # Open the file in write binary mode (wb)
        with conn.open(file_path, mode='wb') as f:
            # Save DataFrame to JSON with specific orientation and line separation
            dataframe.to_json(f, orient='records', lines=True, force_ascii=False)
        
        return Function_Status.SUCCESS, None
    
    except Exception as e:

        return Function_Status.FAIL, e

@st.cache_data
def make_plot(dataframe: pd.DataFrame, x: str, y: str):
    colors = ['lightgray' if count != max(dataframe[x]) else '#ffaa00' for count in dataframe[x]]
    fig = px.bar(
        dataframe,
        title='Top 10 Sponsors',
        x=x,
        y=y,
        orientation='h',
    )

    fig.update_xaxes(dtick=ceil(dataframe[x].max()/10))
    fig.update_traces(marker=dict(color=colors))
    fig.update_layout(xaxis_title='', yaxis_title='')

    return fig


@st.cache_data
def top10_sponsors_plot(dataframe: pd.DataFrame):
    x='Count'
    y='Sponsor'
    dataframe = dataframe.groupby(y, as_index=False)['Protocol Title'].count()
    dataframe.columns = [y, x]
    dataframe = dataframe.nlargest(n=10, columns=x).sort_values(x)

    return make_plot(dataframe, x, y)

@st.cache_data
def top10_sites_plot(dataframe: pd.DataFrame):
    x='Count'
    y='Site'
    dataframe = dataframe[y].str.split(' :', expand=True).melt().dropna()
    dataframe.columns = [x, y]
    dataframe = dataframe.groupby(y, as_index=False).count()
    dataframe = dataframe.nlargest(n=10, columns=x).sort_values(x)

    return make_plot(dataframe, x, y)
    
    # df = df.groupby(y, as_index=False).count()[[y, 'Protocol Title']].nlargest(10, 'Protocol Title').sort_values('Protocol Title', ascending=True)
    # colors =  ['lightgray' if count != max(df['Protocol Title']) else '#ffaa00' for count in df['Protocol Title']]
    # fig = px.bar(
    #     df,
    #     title='Top 10 Sponsors',
    #     x=x,
    #     y=y,
    #     orientation='h',
    # )

    # fig.update_xaxes(dtick=ceil(df['Protocol Title'].max()/10))
    # fig.update_traces(marker=dict(color=colors))
    # fig.update_layout(xaxis_title='', yaxis_title='')

    # return fig

@st.cache_data
def generate_top10_site_plot(df, x: str, y: str):
    df = df['Site Name'].str.split(' :', expand=True).melt().dropna().value_counts('value').to_frame().reset_index().nlargest(10, 'count').sort_values('count', ascending=True)
    colors =  ['lightgray' if count != max(df['count']) else '#ffaa00' for count in df['count']]
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

# @st.cache_data
# def generate_top10_developer_plot(df, x:str, y: str):
#     df = df[y].value_counts().to_frame().reset_index().nlargest(10, 'count').sort_values('count', ascending=True)
#     colors =  ['lightgray' if count != max(df['count']) else '#ffaa00' for count in df['count']]
#     fig = px.bar(
#         df,
#         title='Top 10 Developer',
#         x=x,
#         y=y,
#         orientation='h',
#     )

#     fig.update_xaxes(dtick=ceil(df['count'].max()/10))
#     fig.update_traces(marker=dict(color=colors))
#     fig.update_layout(xaxis_title='', yaxis_title='')

#     return fig

# @st.cache_data
# def generate_top10_disease_plot(df):
#     df = df['Target Disease Category'].value_counts().to_frame().reset_index().nlargest(10, 'count').sort_values('count', ascending=True)
#     colors =  ['lightgray' if count != max(df['count']) else '#ffaa00' for count in df['count']]
#     fig = px.bar(
#         df,
#         title='Top 10 Developer',
#         x='count',
#         y='Target Disease Category',
#         orientation='h',
#     )

#     fig.update_xaxes(dtick=ceil(df['count'].max()/10))
#     fig.update_traces(marker=dict(color=colors))
#     fig.update_layout(xaxis_title='', yaxis_title='')

#     return fig

# def call_api_MdcinClincTestInfoService02(initial:bool=False, iter:int=1):
#     url = BASE_URL + '/MdcinClincTestInfoService02/getMdcinClincTestInfoList02'
#     params = {
#         'serviceKey': st.secrets['DECODED_API_KEY'],
#         'clinic_exam_title': st.session_state.get('title', ''),
#         'pageNo': 1,
#         'numOfRows': NUM_OF_ROWS,
#         'type': 'json',
#         'approval_time': st.session_state.get('date', ''),
#         }

#     if initial:
#         response_body_dict = get_request(url, params=params)

#     else:
#         params['pageNo'] = iter
#         response_body_dict = get_request(url, params=params)

#     return response_body_dict

# def call_api_ClncExamPlanDtlService2(clinical_study_id:str):
#     url = BASE_URL + '/ClncExamPlanDtlService2/getClncExamPlanDtlInq2'
#     params = {
#         'serviceKey': st.secrets['DECODED_API_KEY'],
#         'pageNo': 1,
#         'numOfRows': 100,
#         'type': 'json',
#         'CLNC_TEST_SN': clinical_study_id
#         }

#     response_body_dict = get_request(url, params=params)

#     return response_body_dict


# def call_api_MdeqClncTestPlanAprvAplyDtlService01(initial:bool=False, iter:int=1):
#     url = BASE_URL + '/MdeqClncTestPlanAprvAplyDtlService01/getMdeqClncTestPlanAprvAplyDtlInq01'
#     # url = BASE_URL + '/MdeqClncTestPlanAprvAplyListService/getMdeqClncTestPlanAprvAplyListInq'
#     if initial:
#         params = {
#             'serviceKey': st.secrets['DECODED_API_KEY'],
#             'pageNo': 1,
#             'numOfRows': 100,
#             'type': 'json',
#             }
        
#         return get_request(url, params=params)
        
#     else:
#         params = {
#             'serviceKey': st.secrets['DECODED_API_KEY'],
#             'pageNo': iter,
#             'numOfRows': 100,
#             'type': 'json',
#             }

#         return get_request(url, params=params)
    

