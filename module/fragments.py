import pandas as pd
import plotly.express as px
import streamlit as st

from math import ceil
from time import sleep
from module.utils import convert_df, get_request
from module.constants import STUDY_COLUMN_NAME, STUDY_DETAILS_COLUMN_NAME

@st.fragment
def medication_clinical_trial_search():
    st.header('의약품 임상시험 승인 정보 조회')
    
    # progress_bar
    progress_bar = st.progress(0, text='Idle...')

    title = st.text_input('Protocol Title Keyword')
    date = st.text_input('IND Approval Date (Available Input: :blue[YYYY] | :blue[YYYY]:orange[MM] | :blue[YYYY]:orange[MM]:green[DD])', placeholder='YYYYMMDD', max_chars=8)

    if st.button('Search', key='serch_button'):
        URL = 'http://apis.data.go.kr/1471000/MdcinClincTestInfoService02/getMdcinClincTestInfoList02'
        PARAMS = {
            'serviceKey': st.secrets['DECODED_API_KEY'],
            'clinic_exam_title': title,
            'pageNo': 1,
            'numOfRows': 100,
            'type': 'json',
            'approval_time': date
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
                    for i in range(0, 100):
                        sleep(0.01)
                        progress_bar.progress(i, text='Processing')

                # 100 건 초과 시
                else:
                    for current_page in range(2, max_page + 1):
                        progress_bar.progress(current_page / max_page, text='Processing')
                        PARAMS['pageNo'] = current_page

                        response = get_request(URL, params=PARAMS)

                        if response.status_code != 200:
                            st.toast(f'Error occured, status_code: {response.status_code}, response: {response.text}')
                        else:
                            initial_result.extend(response.json()['body']['items'])

                df = pd.DataFrame(initial_result)
                df.columns = STUDY_COLUMN_NAME

                # session state에 저장
                st.session_state['medication_clinical_trial_dataframe'] = df

                # Exapmle Dataframe
                st.dataframe(df.reset_index(drop=True))

                # Download Button
                st.download_button(
                    label="Download",
                    key='clinical_trials_info_download_button',
                    data=convert_df(df),
                    file_name=f'clinical_trials_info.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

                # 상위 10개 Sponsor
                top10_trial_count_per_sponsor_df = df.groupby('Sponsor', as_index=False).count()[['Sponsor', 'Protocol Title']].nlargest(10, 'Protocol Title').sort_values('Protocol Title', ascending=True)
                max_count = max(top10_trial_count_per_sponsor_df['Protocol Title'])
                min_count = min(top10_trial_count_per_sponsor_df['Protocol Title'])
                colors =  ["lightgray" if count != max_count else "#ffaa00" for count in top10_trial_count_per_sponsor_df['Protocol Title']]

                # Horizontal Bar Plot
                fig = px.bar(
                    top10_trial_count_per_sponsor_df,
                    title='Top 10 Sponsors',
                    x='Protocol Title',
                    y='Sponsor',
                    orientation='h',
                )
                fig.update_xaxes(dtick=1)
                fig.update_traces(
                    marker=dict(color=colors)
                )
                fig.update_layout(xaxis_title='', yaxis_title='')

                st.plotly_chart(fig)

                # 상세항목 검색
                medication_clinical_trial_details_search()

            except KeyError as e:
                if str(e) == "'items'":
                    st.toast('검색 결과가 존재하지 않습니다.')
                else:
                    st.toast(f'KeyError: {e}')

@st.fragment
def medication_clinical_trial_details_search():
    st.subheader('의약품 임상시험 상세 정보 조회 (2019~)')
    st.write('조회된 모든 Protocol에 대한 정보를 확인하려면 버튼을 클릭하세요. 특정한 Protocol에 대한 정보를 확인하려면 Clinical Trial ID를 직접 입력하세요.')
    # progress_bar
    progress_bar = st.progress(0, text='Idle...')

    # session_state에서 첫 번째 fragment가 완료되었는지 확인
    df = st.session_state.get('medication_clinical_trial_dataframe', pd.DataFrame())
    if not df.empty:
        clinical_trial_id = st.text_input('Clinical Trial ID')
        clinical_trial_ids = df['Clinical Trial ID']

        if clinical_trial_id:
            for i in range(0, 100):
                sleep(0.01)
                progress_bar.progress(i, text='Processing')

            if st.button(label='Search Details', key='search_details_button_for_single_ids'):
                URL = 'http://apis.data.go.kr/1471000/ClncExamPlanDtlService2/getClncExamPlanDtlInq2'
                PARAMS = {
                    'serviceKey': st.secrets['DECODED_API_KEY'],
                    'pageNo': 1,
                    'numOfRows': 100,
                    'type': 'json',
                    'CLNC_TEST_SN': clinical_trial_id
                    }

                response = get_request(URL, params=PARAMS)
                if response.status_code != 200:
                    st.toast(f'Error occured, status_code: {response.status_code}, response: {response.text}')

                else:
                    temp_df = pd.DataFrame(response.json()['body']['items'])
                    temp_df.columns = STUDY_DETAILS_COLUMN_NAME
                    st.dataframe(temp_df)

        else:
            clinical_trial_ids = df['Clinical Trial ID']
            temp_list = []
            if st.button(label='Search Details', key='search_details_button_for_multi_ids'):
                for i, clinical_trial_id in enumerate(clinical_trial_ids, start=1):
                    progress_bar.progress(i / len(clinical_trial_ids), text='Processing')

                    URL = 'http://apis.data.go.kr/1471000/ClncExamPlanDtlService2/getClncExamPlanDtlInq2'
                    PARAMS = {
                        'serviceKey': st.secrets['DECODED_API_KEY'],
                        'pageNo': 1,
                        'numOfRows': 100,
                        'type': 'json',
                        'CLNC_TEST_SN': clinical_trial_id
                        }

                    response = get_request(URL, params=PARAMS)

                    if response.status_code != 200:
                        st.toast(f'Error occured, status_code: {response.status_code}, response: {response.text}')

                    else:
                        # 상세 정보가 존재하지 않는 경우에 대한 예외처리
                        try:
                            temp_list.append(pd.DataFrame(response.json()['body']['items']))
                        except KeyError as e:
                            if str(e) == "'items'":
                                st.toast(f'ID {clinical_trial_id} Study의 상세 정보가 존재하지 않습니다.')
                            else:
                                st.toast(f'{clinical_trial_id} KeyError: {e}')
                            continue

                clinical_trials_details_info_df = pd.concat(temp_list)
                clinical_trials_details_info_df.columns = STUDY_DETAILS_COLUMN_NAME

                st.dataframe(clinical_trials_details_info_df.reset_index(drop=True))

                st.download_button(
                    label='Download',
                    key="clinical_trials_details_info_excel_download_button",
                    data=convert_df(clinical_trials_details_info_df),
                    file_name=f'clinical_trials_details_info.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )