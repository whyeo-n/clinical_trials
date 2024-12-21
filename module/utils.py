import requests

from st_files_connection import FilesConnection

import streamlit as st
import pandas as pd
import plotly.express as px

from math import ceil
from module.constants import *

@st.cache_data
def get_request(url: str, params: dict) -> dict:
    """Make a GET request and return the response body if successful."""
    
    try:
        # Make the GET request
        response = requests.get(url, params=params)
        
        # Check if the response status is successful
        response.raise_for_status()
        
        # Return the response body from the JSON response
        return response.json().get('body', {})
    
    except requests.exceptions.HTTPError as http_err:
        st.error(f':red[API Call Failed] HTTP error occurred: {http_err}', icon="🚨")
    except requests.exceptions.RequestException as req_err:
        st.error(f':red[API Call Failed] Request error occurred: {req_err}', icon="🚨")
    except Exception as err:
        st.error(f':red[API Call Failed] An unexpected error occurred: {err}', icon="🚨")
    
    # Return None if an error occurred
    return None

# @st.cache_data
def fetch_medication_trial_data():
    """Fetch and return all medication trial data from the API."""
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
        st.error(':red[Failed to fetch initial data. Please check your API.]', icon="🚨")
        return pd.DataFrame()  # Return an empty DataFrame if the request fails

    totalCount = response_body_dict.get('totalCount', 0)
    if totalCount == 0:
        st.error(':orange[No data available from the API.]', icon="⚠️")
        return pd.DataFrame()  # Return an empty DataFrame if no data is available

    num_of_pages = ceil(totalCount / 100)  # Calculate the number of pages

    progress_bar = st.progress(value=0, text='Fetching start')
    # Fetch data from all pages
    for page_no in range(1, num_of_pages + 1):
        progress_bar.progress(page_no / num_of_pages, text=f'Fetching data from page {page_no}...')
        params['pageNo'] = page_no
        params['numOfRows'] = 100  # Fetch 100 items per page

        response_body_dict = get_request(url, params)

        if response_body_dict is None:
            st.error(f':red[Failed to fetch data for page {page_no}. Check the API or network.]', icon="🚨")
            continue  # Skip to the next page if the request fails
        
        items = response_body_dict.get('items', [])

        if items:  # Only add if there are items
            total_items.extend(items)
        else:
            st.error(f':orange[No items found for page {page_no}.]', icon="⚠️")
    
    progress_bar.progress(1.0, text=f'Fetching complete.')

    # Return the collected items as a DataFrame
    output_dataframe = pd.DataFrame(total_items)
    output_dataframe.columns = MEDICATION_STUDY_COLUMN_NAME
    return output_dataframe

def fetch_device_trial_data():
    """Fetch and return all medical device trial data from the API."""
    
    st.write('Setting URL and parameters...')
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
        st.error(':red[Failed to fetch initial data. Please check your API.]', icon="🚨")
        return pd.DataFrame()  # Return an empty DataFrame if the request fails

    totalCount = response_body_dict.get('totalCount', 0)
    if totalCount == 0:
        st.error(':orange[No data available from the API.]', icon="⚠️")
        return pd.DataFrame()  # Return an empty DataFrame if no data is available

    num_of_pages = ceil(totalCount / 100)  # Calculate the number of pages

    progress_bar = st.progress(value=0, text='Fetching start')
    # Fetch data from all pages
    for page_no in range(1, num_of_pages + 1):
        progress_bar.progress(page_no / num_of_pages, text=f'Fetching data from page {page_no}...')
        params['pageNo'] = page_no
        params['numOfRows'] = 100  # Fetch 100 items per page

        response_body_dict = get_request(url, params)

        if response_body_dict is None:
            st.error(f':red[Failed to fetch data for page {page_no}. Check the API or network.]', icon="🚨")
            continue  # Skip to the next page if the request fails
        
        items = response_body_dict.get('items', [])

        if items:  # Only add if there are items
            total_items.extend(items)
        else:
            st.error(f':orange[No items found for page {page_no}.]', icon="⚠️")
    progress_bar.progress(1.0, text='Fetching complete')

    # Return the collected items as a DataFrame
    output_dataframe = pd.DataFrame(total_items)
    output_dataframe.columns = MEDICAL_DEVICE_STUDY_COLUMN_NAME
    return output_dataframe

# @st.cache_data
def fetch_medication_details_data(dataframe: pd.DataFrame):
    """Fetch and return details data from the API."""
    
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
            st.toast(f':red[Failed to fetch data for {params['CLNC_TEST_SN']}. Check the API or network.]', icon="🚨")
            continue  # Skip to the next page if the request fails
        
        items = response_body_dict.get('items', [])
        
        if items:  # Only add if there are items
            total_items.extend(items)
        else:
            st.toast(f':orange[No items found for page {params['CLNC_TEST_SN']}.]', icon="⚠️")
    
    # Return the collected items as a DataFrame
    output_dataframe = pd.DataFrame(total_items).fillna('None')
    output_dataframe.columns = MEDICATION_STUDY_DETAILS_COLUMN_NAME
    return output_dataframe

def update_data(dataframe: pd.DataFrame, conn: FilesConnection, file_path: str):
    """Function to save DataFrame to Json in GCS."""
    
    try:
        # Open the file in write binary mode (wb)
        with conn.open(file_path, mode="wb") as f:
            # Save DataFrame to JSON with specific orientation and line separation
            dataframe.to_json(f, orient='records', lines=True, force_ascii=False)
        
        st.success(f"File successfully saved to {file_path}.")
    
    except Exception as e:
        # Catch any exception and show a message to the user
        st.error(f':red[Failed to save the file to {file_path}. Error: {str(e)}]', icon="🚨")

# @st.cache_data
# def generate_top10_sponsor_plot(df, x:str, y:str):
#     df = df.groupby(y, as_index=False).count()[[y, 'Protocol Title']].nlargest(10, 'Protocol Title').sort_values('Protocol Title', ascending=True)
#     colors =  ["lightgray" if count != max(df['Protocol Title']) else "#ffaa00" for count in df['Protocol Title']]
#     fig = px.bar(
#         df,
#         title='Top 10 Sponsors',
#         x=x,
#         y=y,
#         orientation='h',
#     )

#     fig.update_xaxes(dtick=ceil(df['Protocol Title'].max()/10))
#     fig.update_traces(marker=dict(color=colors))
#     fig.update_layout(xaxis_title='', yaxis_title='')

#     return fig

# @st.cache_data
# def generate_top10_site_plot(df, x:str, y:str):
#     df = df['Site Name'].str.split(" :", expand=True).melt().dropna().value_counts('value').to_frame().reset_index().nlargest(10, 'count').sort_values('count', ascending=True)
#     colors =  ["lightgray" if count != max(df['count']) else "#ffaa00" for count in df['count']]
#     fig = px.bar(
#         df,
#         title='Top 10 Site',
#         x=x,
#         y=y,
#         orientation='h',
#     )

#     fig.update_xaxes(dtick=ceil(df['count'].max()/10))
#     fig.update_traces(marker=dict(color=colors))
#     fig.update_layout(xaxis_title='', yaxis_title='')

#     return fig

# @st.cache_data
# def generate_top10_developer_plot(df, x:str, y: str):
#     df = df[y].value_counts().to_frame().reset_index().nlargest(10, 'count').sort_values('count', ascending=True)
#     colors =  ["lightgray" if count != max(df['count']) else "#ffaa00" for count in df['count']]
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
#     colors =  ["lightgray" if count != max(df['count']) else "#ffaa00" for count in df['count']]
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
    

