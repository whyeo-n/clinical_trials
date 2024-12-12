import streamlit as st

from module.utils import *

@st.fragment
def medication_clinical_trial_search():
    st.header('의약품 임상시험 :blue[승인 정보 조회] (2012~)')
    columns = st.columns(2)
    form = columns[0].form(key='medication_clinical_trial_info_search')
    tabs = columns[1].tabs(['Top 10 Sponsor', 'Top 10 Site'])
    
    form_columns = form.columns(2)
    progress_bar = form.progress(0, text='Idle...')
    
    form_columns[0].text_input('Protocol Title Keyword', key='title')
    form_columns[1].text_input('IND Approval Date (Available Input: :blue[YYYY] | :blue[YYYY]:orange[MM] | :blue[YYYY]:orange[MM]:green[DD])', placeholder='YYYYMMDD', max_chars=8, key='date')

    dataframe = pd.DataFrame(columns=STUDY_COLUMN_NAME)

    if form.form_submit_button('Search'):
        try: 
            response_body_dict = call_api_MdcinClincTestInfoService02(initial=True)

            if response_body_dict:
                study_infos_list = response_body_dict.get('items', None)
                total_count = response_body_dict.get('totalCount', None)

                if (study_infos_list == None) | (total_count == None):
                    st.toast(f':red[Study Not Found]: {response_body_dict}')

                else:
                    max_page = int(ceil(total_count / NUM_OF_ROWS))

                    if max_page != 1:
                        i = 2

                        while i < max_page:
                            response_body_dict = call_api_MdcinClincTestInfoService02(initial=False, iter=i)
                            study_infos_list.extend(response_body_dict.get('items'))
                            progress_bar.progress(i/max_page, text=f'Processing {i}/{max_page}')
                            i += 1

                        
                        progress_bar.progress(1.0, text=f'Done')

                    else:
                        progress_bar.progress(0.5, text=f'Processing 1/1')
                        sleep(0.01)
                        progress_bar.progress(1.0, text=f'Done')
                    
                    dataframe = pd.DataFrame(study_infos_list).reset_index(drop=True)
                    dataframe.columns = STUDY_COLUMN_NAME

            # Exapmle Dataframe
            columns[0].dataframe(dataframe)

            # Download Button
            columns[0].download_button(
                label="Download",
                key='clinical_trial_info_download_button',
                data=convert_df(dataframe),
                file_name=f'clinical_trial_info.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

            # top10_trial_count_per_sponsor_fig
            top10_trial_count_per_sponsor_fig = generate_top10_sponsor_plot(dataframe)
            tabs[0].plotly_chart(top10_trial_count_per_sponsor_fig)

            # top10_trial_count_per_site_fig
            top10_trial_count_per_site_fig = generate_top10_site_plot(dataframe)
            tabs[1].plotly_chart(top10_trial_count_per_site_fig)

            # 상세항목 검색
            medication_clinical_trial_details_search(dataframe)
        
        except Exception as e:
            st.toast(f':red[Error Occured]: {e}')


@st.fragment
def medication_clinical_trial_details_search(dataframe:pd.DataFrame):
    st.header('의약품 임상시험 :blue[승인 상세 정보 조회] (2019~)')
    st.write('조회된 모든 Protocol에 대한 정보를 확인하려면 버튼을 클릭하세요. 특정한 Protocol에 대한 정보를 확인하려면 Clinical Trial ID를 직접 입력하세요.')
    
    columns = st.columns(2)
    form = columns[0].form(key='medication_clinical_trial_details_info_search')
    tabs = columns[1].tabs(['Top 10 Developer', 'Top 10 Target Disease'])
    progress_bar = form.progress(0, text='Idle...')


    if form.form_submit_button(label='Search Details'):
        study_infos_list = []
        study_count = len(dataframe)
        for i, clinical_study_id in enumerate(dataframe['Clinical Trial ID'], start=1):
            response_body_dict = call_api_ClncExamPlanDtlService2(clinical_study_id)
            if response_body_dict.get('items') == None:
                continue
            else:
                study_infos = response_body_dict['items'][0]
                study_infos_list.append(study_infos)

            progress_bar.progress(i/study_count, text=f'Process {i}/{study_count}')


        details_dataframe = pd.DataFrame(study_infos_list)
        details_dataframe.columns = STUDY_DETAILS_COLUMN_NAME

        progress_bar.progress(1.0, text='Done')

        form.dataframe(details_dataframe.reset_index(drop=True))
        st.download_button(
            label='Download',
            key="clinical_trial_details_info_excel_download_button",
            data=convert_df(details_dataframe),
            file_name=f'clinical_trial_details_info.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        # top10_trial_count_per_developer_fig
        top10_trial_count_per_developer_fig = generate_top10_developer_plot(details_dataframe)
        tabs[0].plotly_chart(top10_trial_count_per_developer_fig)

        # top10_trial_count_per_indication_fig
        top10_trial_count_per_target_disease_fig = generate_top10_disease_plot(details_dataframe)
        tabs[1].plotly_chart(top10_trial_count_per_target_disease_fig)