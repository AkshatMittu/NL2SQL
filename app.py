import streamlit as st
import requests
from utils import update_db
from main import nl2sql
import sqlite3
import json
import time
import pandas as pd
import uvicorn

st.title("NL → SQL Query App")

nl_query = st.text_input("Enter your natural language query:")

if st.button("Run"):
    if nl_query.strip():

        # Call FastAPI
        # res = requests.post(
        #     "http://127.0.0.1:8000/run_query",
        #     json={"query": nl_query}
        # )
        
        if not nl_query:
            st.error("No NL query provided.")
    
        else:
            start = time.perf_counter()
            sql_query, result = nl2sql(nl_query)
            end = time.perf_counter()

            if result is None:
                result = []
            else:

                st.subheader("Generated SQL Query:")
                st.code(sql_query)

                st.subheader("Results:")
                df = pd.DataFrame(result)
                st.dataframe(df)
