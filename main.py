import torch
import random
from util import metadata_toon, new_metadata, rel_schema, prompts, use_qwen, use_mistral, get_args
from toon_format import encode, decode


import warnings
warnings.filterwarnings('ignore')


torch.manual_seed(42)
random.seed(42)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Using device:", device)


nl_query = "How many submissions have misclassification flag?" # sample
args = get_args(nl_query, metadata_toon)

# Check Relevance
rel_prompt = prompts("relevance", args)
relevance_op = use_qwen(rel_prompt, rel_schema, 100, 100)

# Generating Knowledge that helps the generation
if relevance_op['relevance'] == 'No':
  print(relevance_op['explanation'])
else:
  knowledge_op = use_mistral(prompts("knowledge", args))
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
  sql_query = eval(sql_op.split("```")[1][4:])['sql_query']
  print(sql_query)

  print(f"NL Query: {nl_query}")
  print(f"SQL Query: {sql_query}")

  # Executing query
  print("Checking for Syntax Errors")

  print("Fetching Results")
  
