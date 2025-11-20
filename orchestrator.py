from fastapi import FastAPI
from utils import update_db
from main import nl2sql
import sqlite3
import json
import time
import pandas as pd
import uvicorn


app = FastAPI()

@app.get("/")

@app.post("/update_db")
def database_update():
    update_db("C:/Users/anjuv/Desktop/UMN/SEM - 1/GEN AI/Project/NL2SQL/data")
    return {"status": "Database updated successfully."}

@app.post("/run_query")
def execute_query(payload: dict):
    nl_query = payload.get("query", "")
    if not nl_query:
        return {"error": "No NL query provided."}
    
    else:
        start = time.perf_counter()
        sql_query, result = nl2sql(nl_query)
        end = time.perf_counter()
        
        return {
            "nl_query": nl_query,
            "sql_query": sql_query,
            "result": result,
            "processing_time_seconds": round(end - start, 2)
        }


if __name__ == "__main__":
    uvicorn.run("orchestrator:app", host="127.0.0.1", port=8000, reload=True)
