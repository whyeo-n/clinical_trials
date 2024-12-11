import requests
from io import BytesIO

import streamlit as st
import pandas as pd

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
