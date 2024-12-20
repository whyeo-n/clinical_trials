from time import sleep
from datetime import datetime

import streamlit as st

from module.utils import *
from module.constants import *

@st.fragment
def medication_tirals(today:datetime):
    columns = st.columns([2,1])
    with st.spinner("Checking Updates..."):
        conn = st.connection('gcs', type=FilesConnection)
        try:
            # Attempt to read the api_call_logs.json file from GCS
            api_call_logs_df = conn.read(f'{GCS_BUCKET_NAME}/api_call_logs.json', input_format='jsonl', dtype=str)
        except FileNotFoundError as e:
            # If reading fails, create a new empty DataFrame
            columns[0].warning(f"File read failed: {e}")
            api_call_logs_df = pd.DataFrame(columns=['date', 'time'], dtype=str)
            # Save the empty DataFrame to GCS
            update_data(dataframe=api_call_logs_df, conn=conn, file_path=f'{GCS_BUCKET_NAME}/api_call_logs.json')
            columns[0].warning(f"A new api call logs file has been created")
        
        # Check if today's date is missing from the DataFrame
        if today.split('T')[0] not in api_call_logs_df['date'].values:
            # Update Medication Trial Data
            fetched_medication_trial_df = fetch_medication_trial_data()
            update_data(dataframe=fetched_medication_trial_df, conn=conn, file_path=f'{GCS_BUCKET_NAME}/medication_trial_info.json')

            # Update API Call Logs with the current date and time
            max_row = api_call_logs_df.shape[0]
            api_call_logs_df.loc[max_row, 'date'] = today.split('T')[0]
            api_call_logs_df.loc[max_row, 'time'] = today.split('T')[0]
            update_data(dataframe=api_call_logs_df, conn=conn, file_path=f'{GCS_BUCKET_NAME}/api_call_logs.json')
        else:
            columns[0].info('Every data is up to date!')

    medication_trial_df = conn.read(f'{GCS_BUCKET_NAME}/medication_trial_info.json', input_format='jsonl', dtype=str)

    columns[0].dataframe(medication_trial_df)
    
    # Calling API done
    st.session_state['medication_api'] = 'DONE'

    # Displaying the filter form
    if st.session_state['medication_api'] == 'DONE':
        form = columns[0].form(key='filter_medication_trial')
        form_columns = form.columns(2)
        form_columns[0].text_input('Sponsor', key='sponsor', placeholder='삼진제약')
        form_columns[0].text_input(
            '''IND Approval Date (Available Input: :blue[YYYY] | 
            :blue[YYYY]:orange[MM] | :blue[YYYY]:orange[MM]:green[DD])''', 
            key='date', 
            max_chars=8, 
            placeholder='YYYYMMDD')
        form_columns[1].text_input('Site', key='site', placeholder='서울대학교병원')
        form_columns[1].text_input('Protocol Title', key='title', placeholder='급성')
        submit_button = form.form_submit_button('Filter')
        
        if submit_button:
            with st.spinner():
                sponsor = st.session_state['sponsor']
                date = st.session_state['date']
                site = st.session_state['site']
                title = st.session_state['title']
                st.session_state['medication_trial_df'] = medication_trial_df[
                    medication_trial_df['Sponsor'].str.contains(sponsor)
                    &medication_trial_df['IND Approval Date'].str.contains(date)
                    &medication_trial_df['Site Name'].str.contains(site)
                    &medication_trial_df['Protocol Title'].str.contains(title)
                    ]
                columns[0].dataframe(st.session_state['medication_trial_df'])

@st.fragment
def medication_details():
    columns = st.columns([2,1])
    details_button = columns[0].button('Search Details')
    if details_button:
        with st.spinner():
            medication_details_df = fetch_medication_details_data(dataframe=st.session_state['medication_trial_df'])
            columns[0].dataframe(medication_details_df)
# @st.fragment
# def medication_clinical_trial_search():
#     st.title('Clinical Trial Information :blue[Finder]')
#     st.write('식품의약품 안전처의 의약품 임상시험 승인 정보를 검색하려면 :blue[임상시험 제목 및/또는 승인년월일]을 입력하고 :blue[버튼]을 클릭하세요.')
#     st.header(':blue[의약품] 임상시험 :blue[승인 정보 조회] (2012~)')
#     columns = st.columns(2)
#     form = columns[0].form(key='medication_clinical_trial_info_search')
#     tabs = columns[1].tabs(['Top 10 Sponsor', 'Top 10 Site'])
    
#     form_columns = form.columns(2)
#     progress_bar = form.progress(0, text='Idle...')
    
#     form_columns[0].text_input('Protocol Title Keyword', key='title')
#     form_columns[1].text_input('IND Approval Date (Available Input: :blue[YYYY] | :blue[YYYY]:orange[MM] | :blue[YYYY]:orange[MM]:green[DD])', placeholder='YYYYMMDD', max_chars=8, key='date')


#     if form.form_submit_button('Search'):
#         try: 
#             response_body_dict = call_api_MdcinClincTestInfoService02(initial=True)

#             if response_body_dict:
#                 study_infos_list = response_body_dict.get('items', None)
#                 total_count = response_body_dict.get('totalCount', None)

#                 if (study_infos_list == None) | (total_count == None):
#                     st.toast(f':red[Study Not Found]: {response_body_dict}')

#                 else:
#                     max_page = int(ceil(total_count / NUM_OF_ROWS))

#                     if max_page != 1:
#                         i = 2

#                         while i < max_page:
#                             response_body_dict = call_api_MdcinClincTestInfoService02(initial=False, iter=i)
#                             study_infos_list.extend(response_body_dict.get('items'))
#                             progress_bar.progress(i/max_page, text=f'Processing {i}/{max_page}')
#                             i += 1

                        
#                         progress_bar.progress(1.0, text=f'Done')

#                     else:
#                         progress_bar.progress(0.5, text=f'Processing 1/1')
#                         sleep(0.01)
#                         progress_bar.progress(1.0, text=f'Done')
                    
#                     dataframe = pd.DataFrame(study_infos_list).reset_index(drop=True)

#             # Exapmle Dataframe
#             columns[0].dataframe(dataframe)

#             # Download Button
#             columns[0].download_button(
#                 label="Download",
#                 key='clinical_trial_info_download_button',
#                 data=convert_df(dataframe),
#                 file_name=f'clinical_trial_info.xlsx',
#                 mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

#             # top10_trial_count_per_sponsor_fig
#             top10_trial_count_per_sponsor_fig = generate_top10_sponsor_plot(dataframe, x='Protocol Title', y='Sponsor')
#             tabs[0].plotly_chart(top10_trial_count_per_sponsor_fig)

#             # top10_trial_count_per_site_fig
#             top10_trial_count_per_site_fig = generate_top10_site_plot(dataframe, x='count', y='value')
#             tabs[1].plotly_chart(top10_trial_count_per_site_fig)

#             # 상세항목 검색
#             medication_clinical_trial_details_search(dataframe)
        
#         except Exception as e:
#             st.toast(f':red[Error Occured]: {e}')


# @st.fragment
# def medication_clinical_trial_details_search(dataframe:pd.DataFrame):
#     st.header('의약품 임상시험 :blue[승인 상세 정보 조회] (2019~)')
#     st.write('조회된 모든 Protocol에 대한 정보를 확인하려면 버튼을 클릭하세요. 특정한 Protocol에 대한 정보를 확인하려면 Clinical Trial ID를 직접 입력하세요.')
    
#     columns = st.columns(2)
#     form = columns[0].form(key='medication_clinical_trial_details_info_search')
#     tabs = columns[1].tabs(['Top 10 Developer', 'Top 10 Target Disease'])
#     progress_bar = form.progress(0, text='Idle...')


#     if form.form_submit_button(label='Search Details'):
#         study_infos_list = []
#         study_count = len(dataframe)
#         for i, clinical_study_id in enumerate(dataframe['Clinical Trial ID'], start=1):
#             response_body_dict = call_api_ClncExamPlanDtlService2(clinical_study_id)
#             if response_body_dict.get('items') == None:
#                 continue
#             else:
#                 study_infos = response_body_dict['items'][0]
#                 study_infos_list.append(study_infos)

#             progress_bar.progress(i/study_count, text=f'Process {i}/{study_count}')


#         details_dataframe = pd.DataFrame(study_infos_list)
#         details_dataframe.columns = MEDICATION_STUDY_DETAILS_COLUMN_NAME

#         progress_bar.progress(1.0, text='Done')

#         form.dataframe(details_dataframe.reset_index(drop=True))
#         st.download_button(
#             label='Download',
#             key="clinical_trial_details_info_excel_download_button",
#             data=convert_df(details_dataframe),
#             file_name=f'clinical_trial_details_info.xlsx',
#             mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#         )

#         # top10_trial_count_per_developer_fig
#         top10_trial_count_per_developer_fig = generate_top10_developer_plot(details_dataframe, x='count', y='Original Developer of the IP')
#         tabs[0].plotly_chart(top10_trial_count_per_developer_fig)

#         # top10_trial_count_per_indication_fig
#         top10_trial_count_per_target_disease_fig = generate_top10_disease_plot(details_dataframe)
#         tabs[1].plotly_chart(top10_trial_count_per_target_disease_fig)

# @st.fragment
# def medical_device_clinical_trial_search():
#     st.title('Clinical Trial Information :green[Finder]')
#     st.write('식품의약품 안전처의 의료기기 임상시험 승인 정보를 검색하려면 :green[버튼]을 클릭하세요.')
#     st.header(':green[의료기기] 임상시험 :green[승인 정보 조회] (2003~)')
#     columns = st.columns(2)
#     form = columns[0].form(key='medication_clinical_trial_info_search')
#     tabs = columns[1].tabs(['Top 10 Sponsor', 'Top 10 Manufacturer'])
    
#     form_columns = form.columns(2)
#     progress_bar = form.progress(0.00, text='Idle...')
    
#     # form_columns[0].text_input('Protocol Title Keyword', key='title')
#     # form_columns[1].text_input('IND Approval Date (Available Input: :blue[YYYY] | :blue[YYYY]:orange[MM] | :blue[YYYY]:orange[MM]:green[DD])', placeholder='YYYYMMDD', max_chars=8, key='date')

#     if form.form_submit_button('Search'):
#         try: 
#             response_body_dict = call_api_MdeqClncTestPlanAprvAplyDtlService01(initial=True)
#             total_count = response_body_dict.get('totalCount')
#             max_page = int(ceil(total_count/NUM_OF_ROWS))
#             study_infos_list = response_body_dict.get('items')
#             progress_bar.progress(1/max_page, text=f'Process 1/{max_page}')


#             for i in range(2, max_page+1):
#                 response_body_dict = call_api_MdeqClncTestPlanAprvAplyDtlService01(initial=False, iter=i)
#                 study_infos_list.extend(response_body_dict.get('items'))
#                 progress_bar.progress(i/max_page, text=f'Process {i}/{max_page}')


#             dataframe = pd.DataFrame(study_infos_list)
#             dataframe.columns = MEDICAL_DEVICE_STUDY_COLUMN_NAME
#             progress_bar.progress(1.00, text='Done')
#             form.dataframe(dataframe)

#             st.download_button(
#                 label='Download',
#                 key="clinical_trial_details_info_excel_download_button",
#                 data=convert_df(dataframe.sort_values('Approval Date', ascending=False)),
#                 file_name=f'clinical_trial_details_info.xlsx',
#                 mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#             )

#             # top10_trial_count_per_sponsor_fig
#             top10_trial_count_per_sponsor_fig = generate_top10_sponsor_plot(dataframe, x='Protocol Title', y='Sponsor')
#             tabs[0].plotly_chart(top10_trial_count_per_sponsor_fig)

#             # top10_trial_count_per_manufecturer_fig
#             top10_trial_count_per_developer_fig = generate_top10_developer_plot(dataframe, x='count', y='Manufacturer Name')
#             tabs[1].plotly_chart(top10_trial_count_per_developer_fig)


#         except Exception as e:
#             st.toast(f':red[Error Occured]: {e}')
