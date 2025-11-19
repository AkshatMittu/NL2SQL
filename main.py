import torch
import random
from util import metadata_toon, new_metadata, prompts, use_mistral, get_args, kpi_info_toon, run_query, update_db
from toon_format import encode, decode
import time
import sqlite3

import warnings
warnings.filterwarnings('ignore')

torch.manual_seed(42)
random.seed(42)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Using device:", device)


print("DB Set Up...")
update_db("data")


nl_query = "What is the quote to bind ratio per agent channel? Use float numbers."
args = get_args(nl_query, metadata_toon, kpi_info_toon)
n_iters = 3

# Check Relevance
start = time.perf_counter()
rel_prompt = prompts("relevance", args)
relevance_op = use_mistral(rel_prompt)
relevance_op = eval(relevance_op.split("```")[1][4:])
# relevance_op = use_qwen(rel_prompt, rel_schema, 100, 100)
print("Relevance OP:")
print(relevance_op)


# Generating Knowledge that helps the generation
if relevance_op['relevance'] == 'No':
  print(relevance_op['explanation'])
else:
  args['kpi_used'] = relevance_op['kpi']
  knowledge_op = use_mistral(prompts("knowledge", args))
  print()
  print("Knowledge OP")
  print(knowledge_op)
  knowledge_op = eval(knowledge_op.split("```")[1][4:])
  args['knowledge'] = knowledge_op
  fetched_schema = ''
  for i in knowledge_op['Tables']:
    fetched_schema += f'{i}\n'
    fetched_schema += encode(new_metadata[i])
    fetched_schema += '\n\n'
  
  args['req_schema'] = fetched_schema

  # Generating SQL Query
  sql_prompt = prompts("sql", args)
  sql_op = use_mistral(sql_prompt)
  end = time.perf_counter()
  print(f"Time taken: {round(end - start, 2)} seconds")

  sql_query = eval(sql_op.split("```")[1][4:])['sql_query']

  print(f"NL Query: {nl_query}")
  print(f"SQL Query: {sql_query}")
  args['sql_query'] = sql_query

  # Executing Query
  for i in range(n_iters):
    print(f"Passing Syntax Error Trial: {i+1}")
    print("--------------------------------------------------------------")
    try:
      result = run_query(sql_query)
      print("No Syntax Error....")
      print("--------------------------------------------------")
      # print("Results Fetched:")
      # print(result)
      # print("--------------------------------------------------")
    except sqlite3.Error as error:
      # error = e 
      print(f"Syntax Error: {error}")
      args['syntax'] = error
      print("Reflecting on Syntax Error....")
      syntax_prompt = prompts("syntax", args) # TODO: Direct query
      syntax_op = use_mistral(syntax_prompt)
      print()
      print("Syntax OP:")
      print(syntax_op)
      args['syn_sug'] = syntax_op
      sql_prompt = prompts("sql_syntax", args)
      sql_op = use_mistral(sql_prompt)
      print()
      print("SQL OP:")
      print(sql_op)
      sql_query = eval(sql_op.split("```")[1][4:])['corrected_sql_query']
      args['sql_query'] = sql_query
      continue
    
    # Checking for logical errors
    print(f"Passing Logical Error Trial: {i+1}")
    print("--------------------------------------------------------------")
    print("Reverse Engineering")
    reverse_prompt = prompts("reverse", args)
    reversed = use_mistral(reverse_prompt)
    print()
    print("Reverse OP:")
    print(reversed)
    args['reverse'] = reversed
    sql_prompt = prompts("sql_logical", args)
    sql_op = use_mistral(sql_prompt)
    sample = eval(sql_op.split("```")[1][4:])
    sql_query_sample = sample['corrected_sql_query']
    # args['sql_query'] = sql_query
    

    if sample['correct'] == 'Yes':
      print("No Logical Error....")
      print("--------------------------------------------------")
      print("Results Fetched:")
      result = run_query(sql_query)
      print(result)
      print("--------------------------------------------------")
      break
    else:
      print("Logical Error....Retrying")
      # sql_op = use_mistral(sql_prompt)
      # print()
      # print("SQL op")
      # print(sql_op)
      sql_query = sql_query_sample
      args['sql_query'] = sql_query
      continue