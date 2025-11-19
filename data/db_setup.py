import sqlite3
import pandas as pd
import re

def colname_edit(text): 
    text = text.lower().replace(" ", "_")
    return text

def update_db():
    conn = sqlite3.connect("insurancedata.db")

    data = ["agents.csv", "customers.csv", "policies.csv", "claims.csv", "submissions.csv"]

    for i in data:
        df = pd.read_csv(i)
        col_old = df.columns.tolist()
        column_new = [colname_edit(col) for col in col_old] 
        df.rename(columns=dict(zip(col_old, column_new)), inplace=True)       
        table_name = i.split(".")[0]
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    print("Database updated successfully.")


conn = sqlite3.connect("insurancedata.db")
cursor = conn.cursor()
cursor.execute("SELECT CASE WHEN SUM(p.premium_amount) = 0 THEN 0 ELSE SUM(c.approved_amount) / SUM(p.premium_amount) END AS Loss_Ratio FROM policies p LEFT JOIN claims c ON p.policy_id = c.policy_id")
rows = cursor.fetchall()
print(rows)

conn.close()
