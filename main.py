import requests
from time import sleep

import pandas as pd
import streamlit as st

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
    
    response = requests.get(URL, params=params)

    if response.status_code != 200:
        st.warning(f'Error occured, status_code: {response.status_code}, response: {response.text}')
    
    else:
        initial_result = response.json()['body']['items']
        total_count = response.json()['body']['totalCount']
        max_page = (total_count // params['numOfRows']) + 1
        
        # progress_bar
        progress_bar = st.progress(0)

        # 100 건 이내인 경우
        if max_page == 1:
            for i in range(0, 100):
                sleep(0.01)
                progress_bar.progress(i, text='Processing')
        
        # 100 건 초과 시
        else:
            for current_page in range(2, max_page+1):
                progress_bar.progress(current_page / max_page, text='Processing')
                params['pageNo'] = current_page

                response = requests.get(URL, params=params)
                if response.status_code != 200:
                    st.warning(f'Error occured, status_code: {response.status_code}, response: {response.text}')

                else:
                    initial_result.extend(response.json()['body']['items'])
            
        df = pd.DataFrame(initial_result).iloc[:, :-1]
        df.columns = ['Sponsor', 'IND Approval Date', 'Site Name', 'IP Name', 'Protocol Title', 'Phase']
        st.dataframe(df)



