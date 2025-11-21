import pandas as pd
import random
from toon_format import encode
from mistralai import Mistral
import torch
import os
import sqlite3

import warnings
warnings.filterwarnings('ignore')

torch.manual_seed(42)
random.seed(42)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)


# Defining the API keys and other constants
mistral_key = "139Pm7bUuU1EOnpI7lPaSIa8zvXDsFh0"

metadata = {
  "tables": [
    {
        "table_name": "customers",
        "columns":{
    "customer_id": "Unique identifier for each customer, format 'CUST_' followed by 6-digit number (string)",
    "name": "Full name of the customer (string)",
    "phone": "Phone number of the customer (string)",
    "city": "City where the customer resides (string, categorical examples: ['Minneapolis', 'New York', 'Chicago', 'Dallas', 'San Jose', 'Miami', 'Seattle'])",
    "state": "State where the customer resides (string, categorical examples: ['Minnesota', 'New York', 'Illinois', 'Texas', 'California', 'Florida', 'Washington'])",
    "zipcode": "ZIP code of the customer's location (string, categorical examples: ['55414', '10001', '60601', '75201', '95101', '33101', '98101'])",
    "age": "Age of the customer in years (integer, 20–75)",
    "gender": "Gender of the customer, categorical, values: ['male', 'female', 'nonbinary']",
    "marital_status": "Marital status, categorical, values: ['single', 'married', 'divorced', 'widowed']",
    "dependents": "Number of dependents (integer)",
    "education_level": "Highest education level, categorical, values: ['high_school', 'bachelor', 'master', 'phd']",
    "occupation": "Occupation of the customer (string, categorical, examples depend on age group)",
    "employment_status": "Employment status, categorical, values: ['employed', 'self-employed', 'unemployed', 'retired', 'student']",
    "annual_income": "Annual income in USD (integer)",
    "credit_score": "Credit score of the customer (integer, 550–850)",
    "existing_loans": "Type of existing loans, categorical, values: ['none', 'home', 'car', 'personal', 'multiple']",
    "avg_monthly_expense": "Average monthly expense in USD (float)",
    "vehicle_owner": "Whether the customer owns a vehicle (boolean, True/False)",
    "vehicle_type": "Type of vehicle owned, categorical, values: ['car', 'bike', 'none']",
    "budget_per_month": "Monthly budget allocated for insurance/expenses in USD (integer)",
    "customer_tenure_years": "Customer tenure in years (float, 0.5–10)",
    "coverage_preferences": "Preferred types of insurance coverage, list of 1–2 items, categorical, values: ['health', 'life', 'auto', 'home']",
    "risk_tolerance": "Risk tolerance level, categorical, values: ['Low', 'Medium', 'High']",
    "interest_tags": "List of interest tags related to lifestyle or insurance needs, examples: ['family', 'education', 'vehicle', 'retirement', 'travel', 'maternity']"
          }
    },
    {
        "table_name": "policies",
        "columns": {
    "policy_id": "Unique identifier for each policy, format 'POL_' followed by 6-digit number (string)",
    "customer_id": "Identifier for the customer who owns the policy (string, foreign key to customers table)",
    "policy_type": "Type of insurance policy, categorical, values: ['health', 'life', 'auto', 'home']",
    "premium_amount": "Premium amount charged for the policy in USD (integer)",
    "coverage_amount": "Coverage amount provided by the policy in USD (integer)",
    "policy_duration_years": "Duration of the policy in years (integer)",
    "policy_start_date": "Start year of the policy (integer, e.g., 2015–2024)",
    "policy_end_date": "End year of the policy (integer)",
    "policy_risk_level": "Risk level assigned to the policy, categorical, values: ['low', 'medium', 'high']",
    "policy_status": "Current status of the policy, categorical, values: ['active', 'inactive']"
        }
    },
    {
        "table_name": "submissions",
        "columns":{
    "submission_id": "Unique identifier for each submission, format 'SUB-' followed by 6-character alphanumeric code (string)",
    "submission_date": "Date when the submission was created (YYYY-MM-DD, string)",
    "policy_type": "Type of insurance policy, categorical, values: ['health', 'life', 'auto', 'home']",
    "statusid": "Submission status code, categorical, values: ['BND' (Bound), 'QTE' (Quote Only), 'DEC' (Declined), 'UNQ' (Unquoted)]",
    "assignment_date": "Date when submission was assigned to an agent (YYYY-MM-DD, string, may be empty)",
    "first_contact": "Date of first contact with customer (YYYY-MM-DD, string, may be empty)",
    "quote_date": "Date when quote was provided (YYYY-MM-DD, string, may be empty)",
    "declined_date": "Date when submission was declined (YYYY-MM-DD, string, may be empty)",
    "contacted": "Indicates if customer was contacted, categorical, values: ['Yes', 'No']",
    "overwritten_flag": "Indicates if submission was overwritten, categorical, values: ['Yes', 'No']",
    "reclassification_flag": "Indicates if submission was reclassified, categorical, values: ['Yes', 'No']",
    "additional_info_requested": "Indicates if additional info was requested, categorical, values: ['Yes', 'No']",
    "agent_id": "Identifier for the agent assigned to this submission (string, foreign key to agents table)",
    "policy_id": "Identifier for the policy bound to this submission, if applicable (string, foreign key to policies table, may be empty)"
}
    },

    {
       "table_name": "claims", 
       "columns":{
    "claim_id": "Unique identifier for each claim, format 'CLM_' followed by 6-digit number (string)",
    "policy_id": "Identifier for the policy associated with the claim (string, foreign key to policies table)",
    "customer_id": "Identifier for the customer making the claim (string, foreign key to customers table)",
    "claim_date": "Date when the claim was made (YYYY-MM-DD, string)",
    "claim_amount": "Total claimed amount in USD (float)",
    "approved_amount": "Amount approved for payout; 0 if rejected (float)",
    "claim_status": "Status of the claim, categorical, values: ['approved', 'rejected']",
    "processing_time_days": "Number of days taken to process the claim (integer)",
    "settlement_date": "Date when the claim was settled; None if rejected (YYYY-MM-DD, string or null)",
    "fraud_flag": "Indicates potential fraud, binary, values: [0, 1]"
}
    },
 
  {
    "table_name": "agents",
    "columns":{
    "agent_id": "Unique identifier for each agent, format 'A' followed by a number (e.g., A1000), categorical",
    "agent_name": "Full name of the agent (string)",
    "agent_license_number": "Unique license number for the agent, format 'LIC-' followed by 8-character alphanumeric code (string)",
    "agency_name": "Name of the agency the agent belongs to (string)",
    "channel": "The sales channel the agent operates in, categorical, values: ['Telemarketing', 'Digital', 'Branch']",
    "policy_type": "Line of business the agent handles, categorical, values: ['auto', 'home', 'health', 'life']"
    }
  }
]
}


new_metadata = dict()
for i in metadata['tables']:
  new_metadata[i['table_name']] = dict()
  # new_metadata[i['table_name']]['description'] = i['description']
  new_metadata[i['table_name']]['columns'] = i['columns']

metadata_toon = ''
for i in new_metadata:
  metadata_toon += f'Table: {i}\n'
  metadata_toon += encode(new_metadata[i])
  metadata_toon += '\n\n'


# Fetching KPIs in TOON format
kpi_info = {
  "customer_lifetime_value": {
    "meaning": "Total premium revenue expected from a customer over their entire relationship with the insurer.",
    "math_formula": "SUM(premium_amount) WHERE policy.customer_id = customer.customer_id"
  },
  "premium_to_income_ratio": {
    "meaning": "Percentage of a customer’s income spent on insurance premiums. Indicates affordability.",
    "math_formula": "(premium_amount / annual_income) * 100"
  },
  "cross_sell_rate": {
    "meaning": "Percentage of customers who purchased more than one type of policy.",
    "math_formula": "(COUNT(customers_with_multiple_policies) / COUNT(total_customers)) * 100"
  },
  "lead_to_policy_conversion_rate": {
    "meaning": "Percentage of submissions that convert into active insurance policies.",
    "math_formula": "(COUNT(policies_created) / COUNT(total_submissions)) * 100"
  },
  "quote_conversion_rate": {
    "meaning": "Percentage of quotes that result in a bound policy.",
    "math_formula": "(COUNT(quotes_bound) / COUNT(total_quotes)) * 100"
  },
  "average_conversion_time": {
    "meaning": "Average number of days between submission and policy issuance.",
    "math_formula": "AVG(policy_start_date - submission_date)"
  },
  "agent_productivity": {
    "meaning": "Number of policies sold by each agent.",
    "math_formula": "COUNT(policies WHERE policies.agent_id = agents.agent_id)"
  },
  "agent_premium_contribution": {
    "meaning": "Total premium generated by an agent.",
    "math_formula": "SUM(premium_amount WHERE policy.agent_id = agent.agent_id)"
  },
  "submission_to_quote_time": {
    "meaning": "Average time taken to convert a submission to a quote.",
    "math_formula": "AVG(quote_date - submission_date)"
  },
  "claim_frequency": {
    "meaning": "Number of claims filed per 1000 policies.",
    "math_formula": "(COUNT(claims) / COUNT(policies)) * 1000"
  },
  "claim_severity": {
    "meaning": "Average financial size of claims filed.",
    "math_formula": "AVG(claim_amount)"
  },
  "loss_ratio": {
    "meaning": "Measures insurer profitability by comparing claim payouts to premium revenue.",
    "math_formula": "SUM(approved_amount) / SUM(premium_amount)"
  },
  "claim_processing_time": {
    "meaning": "Average number of days taken to resolve a claim.",
    "math_formula": "AVG(settlement_date - claim_date)"
  },
  "sla_compliance_rate": {
    "meaning": "Percentage of claims resolved within the defined service time.",
    "math_formula": "(COUNT(claims_within_SLA) / COUNT(total_claims)) * 100"
  },
  "high_loss_customers": {
    "meaning": "Customers whose claim payouts exceed premium contributions.",
    "math_formula": "SUM(approved_amount) > SUM(premium_amount)"
  },
  "policy_growth_rate": {
    "meaning": "Business growth based on increase in number of active policies.",
    "math_formula": "((policies_this_period - policies_last_period) / policies_last_period) * 100"
  },
  "premium_growth_rate": {
    "meaning": "Growth in premium revenue over a period.",
    "math_formula": "((total_premium_this_period - total_premium_last_period) / total_premium_last_period) * 100"
  },
  "customer_retention_rate": {
    "meaning": "Percentage of customers who renewed or kept policies active.",
    "math_formula": "(active_customers_current_period / active_customers_previous_period) * 100"
  },
  "expense_ratio": {
    "meaning": "Portion of earned premium consumed by operational expenses.",
    "math_formula": "operational_expenses / earned_premium"
  },
  "combined_ratio": {
    "meaning": "Core profitability metric combining loss and expense performance.",
    "math_formula": "loss_ratio + expense_ratio"
  },
  "customer_profitability": {
    "meaning": "Net financial value of a customer based on premium vs claim payout.",
    "math_formula": "SUM(premium_amount) - SUM(approved_amount)"
  },
  "risk_adjusted_premium_ratio": {
    "meaning": "Premium collected relative to risk level of a policy.",
    "math_formula": "premium_amount / policy_risk_level"
  },
  "claims_per_customer": {
    "meaning": "Average number of claims filed per customer.",
    "math_formula": "COUNT(claim_id) / COUNT(customer_id)"
  },
  "pending_claim_ratio": {
    "meaning": "Percentage of claims still under review or not yet settled.",
    "math_formula": "(COUNT(claims WHERE claim_status IN ['pending','review']) / COUNT(total_claims)) * 100"
  }
}


kpi_info_toon = ''
for i in kpi_info:
  kpi_info_toon += f'{i}\n'
  kpi_info_toon += encode(kpi_info[i])
  kpi_info_toon += '\n\n'


def use_mistral(prompt, model="mistral-large-2411", op_type="json_object"):

  with Mistral(
    api_key=mistral_key,
) as mistral:

    res = mistral.chat.complete(model=model, messages=[
        {
            "content": prompt,
            "role": "user",
        },
    ], response_format= { "type": op_type }, stream=False)

    return res.choices[0].message.content



def get_args(nl_query, schema, kpi_info_toon):
  return {"nl_query": nl_query,
          "schema": schema,
          "kpi": kpi_info_toon}

# Setting Up DB
def colname_edit(text): 
    text = text.lower().replace(" ", "_")
    return text

def update_db(dir="data"):
    conn = sqlite3.connect("insurancedata.db")

    # data = ["agents.csv", "customers.csv", "policies.csv", "claims.csv", "submissions.csv"]
    data = os.listdir(dir)

    for i in data:
        df = pd.read_csv(f"{dir}/{i}")
        col_old = df.columns.tolist()
        column_new = [colname_edit(col) for col in col_old] 
        df.rename(columns=dict(zip(col_old, column_new)), inplace=True)       
        table_name = i.split(".")[0]
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    print("Database updated successfully.")

def run_query(query):
  conn = sqlite3.connect("insurancedata.db")
  cursor = conn.cursor()
  cursor.execute(query)
  rows = cursor.fetchall()
  result = pd.DataFrame(rows, columns=[description[0] for description in cursor.description])
  
  conn.close()
  return result
    


def prompts(prompt_type, args):
  nl_query = args['nl_query']
  
  if prompt_type == "knowledge":
    schema = args['schema']
    kpi_used = args['kpi_used']
    prompt = f"""You are a insurance domain specialist, who provides knowledge and steps for the natural language query given to you so that these steps can used to convert this NL query to SQL query.
Additionally, you will also be given the KPI information used in the NL query.
Give good and detailed knowledge in 300 words for the schema given below.
Your output should be in a JSON FORMAT and NO OTHER TEXT.

This knowledge SHOULD include:
- What tables to select
- What columns to use
- Steps to fetch and answer the query completely and correctly. If KPI was used, include steps to do that in SQL as well

Output format:
{{
  Tables: list of tables that should be used,
  Columns: List of columns from each table,
  Steps: Necessary steps to take to generate the SQL query, include how to approach the KPI formula if KPI was used.
}}

Schema:
{schema}

KPI Information:
{kpi_used}

Natural Language Query:
{nl_query}
"""
  
  if prompt_type == "relevance":
    kpi_info_args = args['kpi']
    prompt = f"""You are a insurance domain specialist, you'll be given a natural language query and KPIs related to the domain.
Your task is to check if this natural language query is relevant to insurance domain or not, so that if it is relevant the downstream task will be to convert this natural language query to SQL.
If the natural language query asks or uses any KPI, give that KPI information as well else give None.
You should also explain your choice.
Your output should be in JSON FORMAT and NO OTHER TEXT.

KPIs:
{kpi_info_args}

Output Format:
{{
  relevance: Yes/No,
  explanation: Explain why you chose yes or no.
  kpi: If a KPI is used give formula and information related to that KPI, else give None.
}}

Natural Language Query:
{nl_query}
"""
  
  if prompt_type == "sql":
    knowledge = args['knowledge']
    fetched_schema = args['req_schema']
    prompt = f"""You are a Insurance SQL Analyst, you'll be given a natural language query and steps to generate the SQL query.
Your task is to convert this natural language query to SQL. Return a case insensitive single line SQL query.

Your output should be in a JSON format and NO OTHER TEXT.

Tables to use: {knowledge['Tables']}

Columns to use: 
{encode(knowledge['Columns'])}

Steps to generate SQL query: 
{knowledge['Steps']}


Schema of these tables:
{fetched_schema}

Output Format:
{{
  sql_query: Executable SQL query to answer the natural language query.
}}

Natural Language Query:
{nl_query}
"""
  if prompt_type == "reverse":
    sql_query = args['sql_query']
    prompt = f"""You are an Insurance domain SQL query analyst and guide. 
You will be given an SQL query and your job is to clearly describe what that query is doing tying it to the insurance domain.

Your output should only be the explanation of the SQL query and NO OTHER TEXT.

SQL Query:
{sql_query}
    """
  
  if prompt_type == "sql_logical":
    sql_query = args['sql_query']
    fetched_schema = args['req_schema']
    knowledge = args['knowledge']
    reverse = args['reverse']
    prompt = f"""You are an Insurance domain SQL query analyst and guide.
You will be given a natural language query, its generated SQL query and the text description of that the SQL query is doing.
You'll also be given the tables and their schemas, and columns in SQL along with the steps used in generating SQL query that answer's the natural language query.

Use this information and check if the text description answers the natural language query or not, additionally also give the correct, case insensitive single line SQL query if it is wrong.

Your output should be in a JSON format and NO OTHER TEXT.

Output Format:
{{
  correct: Yes/No,
  corrected_sql_query: If no, give the corrected SQL query to better answer the natural language query. If yes, repeat the same SQL query.
}}


Tables to use: {knowledge['Tables']}

Columns to use: 
{encode(knowledge['Columns'])}

Steps to generate SQL query: 
{f"""{knowledge['Steps']}"""}

Schema of these tables:
{fetched_schema}

Natural Language Query:
{nl_query}

SQL Query:
{sql_query}

Explanation of SQL query as text:
{reverse}

"""
  
  if prompt_type == "sql_syntax":
    sql_query = args['sql_query']
    syn_sug = args['syn_sug']
    prompt = f"""You are an SQL query generator who reflects on their own mistakes and gives out the correct query.
You will be given the natural language query which was converted to SQL query in the previous iteration, the SQL query, database schema and the suggestions to correct the syntax error that occured previously.
Your job is to go through the given information and correct the SQL query syntactically. Return a case insensitive single line SQL query.

Your output should be in a JSON format and NO OTHER TEXT.

Output Format:
{{
  corrected_sql_query: Executable SQL query to answer the natural language query.
}}

Database Schema:
{metadata_toon}

Natural Language Query:
{nl_query}
    
SQL Query:
{sql_query}

Suggestion to correct error occured previously: 
{syn_sug}
    
    """

  if prompt_type == "syntax":
    error = args['syntax']
    sql_query = args['sql_query']
    fetched_schema = args['req_schema']
    knowledge = args['knowledge']
    prompt = f"""You are an evaluator and a guide for SQL query executions. You'll be given a natural language query, the SQL query for it that faced an error, tables, the schema of the entire database, and columns that the SQL query is using to answer the natural language query.
Your job is to suggest revisions to the SQL query to ensure safe execution of the SQL query generated from the natural language query.

Tables to use: {knowledge['Tables']}

Columns to use: 
{encode(knowledge['Columns'])}

Steps to generate SQL query: 
{knowledge['Steps']}

Database Schema:
{metadata_toon}

Natural Language Query:
{nl_query}

SQL Query:
{sql_query}

Error:
{error}
"""

  return prompt
