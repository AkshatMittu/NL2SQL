# from main import nl2sql
# import pandas as pd
# from tqdm import tqdm


# df = pd.read_csv("eval_df.csv")
# op_query = []

# for i in tqdm(df['nl_query']):
#     print("NL Query:", i)
    
#     try:
#         sql_query, result = nl2sql(i)
#         op_query.append(sql_query)
        
#     except Exception as e:
#         print("Error occurred:", e)
#         op_query.append(None)
#         continue
    
#     print("SQL Query:", sql_query)
#     print("Result:", result)
#     print("--------------------------------------------------")
    
# df['sql_query'] = op_query
# df.to_csv("eval_df_output.csv", index=False)
    
