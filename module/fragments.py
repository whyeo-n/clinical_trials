import streamlit as st
# from langchain_google_vertexai import ChatVertexAI
# from google.oauth2 import service_account

from module.utils import *
from module.constants import *

gcs_info = st.secrets.connections.gcs

# llm = ChatVertexAI(
#     project=gcs_info['project_id'],
#     model='gemini-1.5-flash-001',
#     temperature=0,
#     max_tokens=None,
#     max_retries=6,
#     stop=None,
#     credentials=service_account.Credentials.from_service_account_info(gcs_info),
#     # other params...
# )

@st.fragment
def home() -> None:
    # Set Layout
    columns = st.columns([2, 1], vertical_alignment='top', border=False)
    status = columns[0].status('Checking for updates...', expanded=True)
    
    logs_result, logs_e = check_api_call_logs()
    if logs_result == Function_Status.FAIL:
        status.error(f'API Call Log Check Failed: {str(logs_e)}]', icon='🚨')
    elif logs_result == Function_Status.SUCCESS:
        status.success(f'API Call Log Check Success!')

        # Check if today's date is missing from the DataFrame
        if st.session_state['today'].split('T')[0] not in st.session_state['api_call_logs_df'].loc[:, 'date'].values:
            # Fetching Data for update
            fetch_data(st.session_state['files_connection'], st.session_state['api_call_logs_df'], st.session_state['today'], status)
            if st.session_state['fetch_data_result_dict']['total_result'] == Function_Status.FAIL:
                del st.session_state['fetch_data_result_dict']['total_result']
                for result in st.session_state['fetch_data_result_dict'].keys():
                    if st.session_state['fetch_data_result_dict'][result]['status'] == Function_Status.SUCCESS:
                        status.success(st.session_state['fetch_data_result_dict'][result]['message'])
                    elif st.session_state['fetch_data_result_dict'][result]['status'] == Function_Status.FAIL:
                        status.error(st.session_state['fetch_data_result_dict'][result]['message'], icon='🚨')
            else:
                status.update(label='Update Success. Every data is up to date!', expanded=False, state='complete')
            
        else:
            status.update(label=f'Already updated today. Every data is up to date!', expanded=False, state='complete')

    if columns[1].button('Update Now'):
        status.update(label='Update Now...', expanded=True)
        # Fetching Data for update
        fetch_data(st.session_state['files_connection'], st.session_state['api_call_logs_df'], st.session_state['today'], status)
        if st.session_state['fetch_data_result_dict']['total_result'] == Function_Status.FAIL:
            del st.session_state['fetch_data_result_dict']['total_result']
            for result in st.session_state['fetch_data_result_dict'].keys():
                if st.session_state['fetch_data_result_dict'][result]['status'] == Function_Status.SUCCESS:
                    status.success(st.session_state['fetch_data_result_dict'][result]['message'])
                elif st.session_state['fetch_data_result_dict'][result]['status'] == Function_Status.FAIL:
                    status.error(st.session_state['fetch_data_result_dict'][result]['message'], icon='🚨')
        else:
            status.update(label='Update Success. Every data is up to date!', expanded=False, state='complete')

@st.fragment
def medication_tirals_page() -> None:
    conn = st.session_state['files_connection']
    medication_trial_json_bytes = conn.open(f'{GCS_BUCKET_NAME}/medication_trial_info.json', mode='rb')
    
    columns = st.columns([2,1], border=True)
    tabs = columns[1].tabs(['Top 10 Sponsors', 'Top 10 Sites'])

    with columns[0]:
        st.title(':blue[Medication] Clinical Trial Information :blue[Finder] (2012~)')
        medication_trial_list = decoding_json_bytes(medication_trial_json_bytes)
        st.session_state['medication_df'] = pd.DataFrame(medication_trial_list)
    
        # Calling API done
        st.session_state['medication_retrieve'] = 'DONE'

        if st.session_state['medication_retrieve'] == 'DONE':
            medication_trials()

        if st.session_state['medication_filter'] == 'DONE':
            if st.session_state['medication_filtered_df'].empty:
                st.error('Study Not Found')
            else: 
                st.dataframe(st.session_state['medication_filtered_df'])

                medication_details()

                with tabs[0]:
                    st.plotly_chart(top10_sponsors_plot(st.session_state['medication_filtered_df']))
                with tabs[1]:
                    st.plotly_chart(top10_sites_plot(st.session_state['medication_filtered_df']))

@st.fragment
def medication_trials() -> None:
    if st.session_state['medication_retrieve'] != 'DONE':
        st.empty()

    else:
        form = st.form(key='medication_trials_filter', enter_to_submit=True)
        form_columns = form.columns(2)
        with form_columns[0]:
            st.text_input('Sponsor', key='sponsor', placeholder='삼진제약')
            st.text_input(
                '''IND Approval Date (Available Input: :blue[YYYY] | 
                :blue[YYYY]:orange[MM] | :blue[YYYY]:orange[MM]:green[DD])''', 
                key='date', 
                max_chars=8, 
                placeholder='YYYYMMDD'
                )
        with form_columns[1]:
            st.text_input('Site', key='site', placeholder='서울대학교병원')
            st.text_input('Protocol Title', key='title', placeholder='급성')
        
        # Filtering Dataframe
        if form.form_submit_button('Search', use_container_width=True):
            medication_filtered_df = st.session_state['medication_df'].copy()
            medication_filtered_df = medication_filtered_df[
                medication_filtered_df['Sponsor'].str.contains(st.session_state['sponsor'], case=False)
                &medication_filtered_df['IND Approval Date'].str.contains(st.session_state['date'], case=False)
                &medication_filtered_df['Site'].str.contains(st.session_state['site'], case=False)
                &medication_filtered_df['Protocol Title'].str.contains(st.session_state['title'], case=False)
                ]
            st.session_state['medication_filtered_df'] = medication_filtered_df
            st.session_state['medication_filter'] = 'DONE'

            # rerun superier fragment
            st.rerun()

    return None

@st.fragment
def medication_details() -> None:
    # Displaying the details button
    if st.button('Search Details', use_container_width=True):
        medication_details_df = fetch_medication_details_data(dataframe=st.session_state['medication_filtered_df'])
        st.dataframe(medication_details_df)

        return None

def device_tirals_page() -> None:
    conn = st.session_state['files_connection']
    device_trial_json_bytes = conn.open(f'{GCS_BUCKET_NAME}/device_trial_info.json', mode='rb')
    
    columns = st.columns([2,1], border=True)
    tabs = columns[1].tabs(['Top 10 Manufacturer'])
    
    with columns[0]:
        st.title(':green[Device] Clinical Trial Information :green[Finder] (2003~)')
        # device_trial_df = conn.read(f'{GCS_BUCKET_NAME}/device_trial_info.json', input_format='jsonl', encoding='utf-8', dtype=str)
        device_trial_list = decoding_json_bytes(device_trial_json_bytes)
        device_df = pd.DataFrame(device_trial_list)

        # Cleaning device trail dataframe
        device_df.drop(columns=[
            'Unknown', 
            'Category ID', 
            'Clinical Trial ID Code', 
            'Clinical Trial ID Name', 
            'Clinical Trial Detail Code', 
            'Clinical Trial Detail Name'
            ], inplace=True)
        device_df['IND Approval Date'] = device_df['IND Approval Date'].str.replace('-', '')

        st.session_state['device_df'] = device_df

        # Calling API done
        st.session_state['device_retrieve'] = 'DONE'

        if st.session_state['device_retrieve'] == 'DONE':
            device_trials()

        if st.session_state['device_filter'] == 'DONE':
            if st.session_state['device_filtered_df'].empty:
                st.error('Study Not Found')
            else:
                st.dataframe(st.session_state['device_filtered_df'])

                with tabs[0]:
                    st.plotly_chart(top10_Manufacturer_plot(st.session_state['device_filtered_df']))

def device_trials() -> None:
    form = st.form(key='search_device_trial')
    form_columns = form.columns(2)
    with form_columns[0]:
        st.text_input('Manufacturer', key='manufacturer', placeholder='뷰노')
        st.text_input(
            '''IND Approval Date (Available Input: :blue[YYYY] | 
            :blue[YYYY]:orange[MM] | :blue[YYYY]:orange[MM]:green[DD])''', 
            key='date', 
            max_chars=8, 
            placeholder='YYYYMMDD'
            )
    with form_columns[1]:
        st.text_input('Device ID', key='device_id', placeholder='D06080.01')
        st.text_input('Protocol Title', key='title', placeholder='파킨슨')
    
    if form.form_submit_button('Search', use_container_width=True):
        device_filtered_df = st.session_state['device_df'].copy()
        device_filtered_df = device_filtered_df[
            device_filtered_df['Manufacturer'].str.contains(st.session_state['manufacturer'], case=False)
            &device_filtered_df['IND Approval Date'].str.contains(st.session_state['date'], case=False)
            &device_filtered_df['Device ID'].str.contains(st.session_state['device_id'], case=False)
            &device_filtered_df['Protocol Title'].str.contains(st.session_state['title'], case=False)
            ]
        st.session_state['device_filtered_df'] = device_filtered_df
        st.session_state['device_filter'] = 'DONE'

        # rerun superier fragment
        st.rerun()

# @st.fragment
# def medication_chatbot(medication_df) -> None:
#     # AI Chatbot
#     st.title(':blue[AI] Chatbot')
#     st.write('Ask me anything about the clinical trial information!')
#     user_input = st.text_input('User Input', key='user_input')
#     submit_button = st.button('Submit')

#     if submit_button:
#         with st.spinner():
#             df_str = medication_df.to_string()

#             messages = [
#                 (
#                     'system',
#                     '''You are a helpful assistant that summarize and answer questions about the clinical trial information.\n
#                     [examples]\n
#                     question: What is the most frequent indication in the clinical trial?\n
#                     answer: The most frequent indication in the clinical trial is Parkinson's disease./n
#                     answer (korean): 임상시험에서 가장 빈도가 높은 질병은 파킨슨병입니다.\n'''
#                 ),
#                 (
#                     'user',
#                     f'''{user_input}\n
#                     dataframe: {df_str}'''
#                 )
#             ]

#             response = llm.invoke(messages)
#             st.write(response.content)
#             # response = call_api_chatbot(user_input)
#             # columns[1].write(response)