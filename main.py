import pandas as pd
import plotly.express as px
import streamlit as st

from math import ceil
from time import sleep
from module.utils import convert_df, get_request

URL = 'http://apis.data.go.kr/1471000/MdcinClincTestInfoService02/getMdcinClincTestInfoList02'

title = st.text_input('Title')
date = st.text_input('Approval Date')

if st.button('Search'):
    params = {
        'serviceKey': st.secrets['DECODED_API_KEY'],
        'clinic_exam_title': title,
        'pageNo': 1,
        'numOfRows': 100,
        'type': 'json',
        'approval_time': date
        }
    
    response = get_request(URL, params=params)

    if response.status_code != 200:
        st.warning(f'Error occured, status_code: {response.status_code}, response: {response.text}')

    else:
        initial_result = response.json()['body']['items']
        total_count = response.json()['body']['totalCount']
        max_page = int(ceil(total_count) / params['numOfRows'])
        
        # progress_bar
        progress_bar = st.progress(0)

        # 100 건 이내인 경우
        if max_page == 1:
            for i in range(0, 100):
                sleep(0.01)
                progress_bar.progress(i, text='Processing')

        # 100 건 초과 시
        else:
            for current_page in range(2, max_page + 1):
                progress_bar.progress(current_page / max_page, text='Processing')
                params['pageNo'] = current_page

                response = get_request(URL, params=params)

                if response.status_code != 200:
                    st.warning(f'Error occured, status_code: {response.status_code}, response: {response.text}')
                else:
                    initial_result.extend(response.json()['body']['items'])

        # 가장 마지막 Column 제거
        df = pd.DataFrame(initial_result).iloc[:, :-1]
        df.columns = ['Sponsor', 'IND Approval Date', 'Site Name', 'IP Name', 'Protocol Title', 'Phase']

        # Exapmle Dataframe
        st.dataframe(df)
        st.download_button(
            label="Download",
            data=convert_df(df),
            file_name=f'clinical_trials_info.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        # Download Button
        st.download_button(
            label="Download",
            data=convert_df(df),
            file_name=f'clinical_trials_info.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        # 상위 10개 Sponsor
        top10_trial_count_per_sponsor_df = df.groupby('Sponsor', as_index=False).count()[['Sponsor', 'Protocol Title']].nlargest(10, 'Protocol Title').sort_values('Protocol Title', ascending=True)
        max_count = max(top10_trial_count_per_sponsor_df['Protocol Title'])
        min_count = min(top10_trial_count_per_sponsor_df['Protocol Title'])
        colors =  ["lightgray" if count != max_count else "#ffaa00" for count in top10_trial_count_per_sponsor_df['Protocol Title']]

        # Horizontal Bar Plot
        fig = px.bar(
            top10_trial_count_per_sponsor_df,
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

        # Sorting 하는 방법 찾아내고 다시 시도
        # top10_trial_count_per_sponsor_with_phase_df = df.groupby(['Sponsor', 'Phase'], as_index=False).count()[['Sponsor', 'Phase', 'Protocol Title']]
        # top10_trial_count_per_sponsor_with_phase_df = top10_trial_count_per_sponsor_df[['Sponsor']].merge(top10_trial_count_per_sponsor_with_phase_df, how='left', on='Sponsor')[['Sponsor', 'Phase', 'Protocol Title']].sort_values(['Protocol Title'], ascending=True)
        # # top10_trial_count_per_sponsor_with_phase_df_pivot = top10_trial_count_per_sponsor_with_phase_df.pivot(index='Sponsor', columns='Phase', values='Protocol Title')

        # fig2 = px.bar(
        #     top10_trial_count_per_sponsor_with_phase_df,
        #     x='Protocol Title',
        #     y='Sponsor',
        #     color='Phase',
        #     orientation='h'
        # )

        # fig2.update_layout(xaxis_title='', yaxis_title='')
        # fig2.update_xaxes(dtick=1)

        # st.plotly_chart(fig2)