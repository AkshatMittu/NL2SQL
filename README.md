## NL2SQL

Convert natural-language questions into **accurate, executable SQL** for insurance data. Unlike one-shot LLMs, this system uses **person-based, domain filtering, schema guidance, and iterative error correction**.

### Motivation
- Insurance data is vast but SQL expertise is limited.  
- Non-technical users need fast, accurate KPI answers (loss ratio, claims, premiums).  
- LLMs alone: hallucinate tables, produce invalid SQL, miss joins, lack correctness validation.

### Problem
Enable users to ask plain English questions and get **correct SQL**, even without DB knowledge:  
- Filter irrelevant queries  
- Ground in schema  
- Generate SQL guided by knowledge  
- Detect syntax & logical errors  
- Iteratively refine or reject failures

### Pipeline
1. **Relevance Check:** Skip irrelevant queries  
2. **Knowledge Generation:** Tables, columns, KPIs, reasoning steps  
3. **SQL Generation:** Create initial SQL  
4. **Syntax Check:** Catch errors, regenerate with Judge  
5. **Logical Check:** Validate against results or reverse NL  
6. **Iterative Refinement:** Loop until correct or reject

**Flow:**  
`NL Query → Relevance → Knowledge → SQL → Syntax → Judge → Reverse NL → Iterate → Result`

---

### Schema
- Policies, Claims, Agents, Submissions, Customers  

### Dataset
- `gretelai/synthetic_text_to_sql` + 10 insurance-specific queries  

### Evaluation
- 60 queries, ~90% correctness  
- Syntax + semantic validation using LLM-as-Judge  


### Tech
- Model: `mistral-large-2411`  
- Avg runtime: ~20s/query  
- 7 LLM calls per query  
- LLM roles: Domain Specialist, SQL Analyst, Judge


### How to Run
 - Make sure the Mistral API key is still working.
 - Install packages/dependencies using `pip install -r requirements.txt`
- Finally, run `main.py` using `python main.py`

---

### Team
- Anjali Vemula (6076947)  
- Akshat Dasula (5979761)  
### Files
- Presentation: `NL2SQL 70-30.pptx`
