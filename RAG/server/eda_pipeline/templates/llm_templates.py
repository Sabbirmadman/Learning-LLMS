"""
Templates for LLM prompts used in the EDA pipeline.
"""

# Regular query template
REGULAR_QUERY_TEMPLATE = """
You are a Python Data Science Expert. Given the following CSV files and a user question,
generate clean, efficient pandas code to answer the question.

Available CSV Files:
{csv_info}

User Question:
{query}

Important instructions:
1. Your code should be complete and ready to execute.
2. Assume the CSV files are already loaded into pandas DataFrames with variable names that match
their filenames (without the .csv extension).
3. Store the final result in a variable called 'result'.
4. Add helpful comments to explain your code.
5. Handle potential errors gracefully.
6. DO NOT include visualizations or any matplotlib/seaborn code.
7. For complex operations, break down your approach into smaller steps with clear comments.
8. If there is any date-related processing, consider converting columns to datetime format.
9. If you want to provide multiple approaches or solutions, wrap each complete code snippet with 
   <CODE_BLOCK> and </CODE_BLOCK> tags. For example:
   
   <CODE_BLOCK>
   # Approach 1 - Using method X
   df = pd.DataFrame(...)
   result = df.groupby(...)
   </CODE_BLOCK>
   
   <CODE_BLOCK>
   # Approach 2 - Using method Y
   df = pd.DataFrame(...)
   result = df.pivot_table(...)
   </CODE_BLOCK>

{format_instructions}
"""

# Relationship query template
RELATIONSHIP_QUERY_TEMPLATE = """
You are a CSV Data Relationship Expert. Given the following information about CSV files 
and their relationships, generate pandas code to answer the user's question.

Available CSV Files:
{csv_info}

Relationship Information:
{relationship_text}

User Question:
{query}

Important instructions:
1. Your code should be complete and ready to execute.
2. Use the provided 'Code to load' statements to load the CSV files.
3. Store the final result in a variable called 'result'.
4. Add helpful comments to explain your code.
5. Handle potential errors gracefully.
6. DO NOT include visualizations or any matplotlib/seaborn code.
7. If there is any date-related processing, consider converting columns to datetime format.
8. If you want to provide multiple approaches or solutions, wrap each complete code snippet with 
   <CODE_BLOCK> and </CODE_BLOCK> tags. For example:
   
   <CODE_BLOCK>
   # Approach 1 - Using join
   df1 = pd.read_csv(...)
   result = df1.merge(...)
   </CODE_BLOCK>
   
   <CODE_BLOCK>
   # Approach 2 - Using SQL-like querying
   df1 = pd.read_csv(...)
   result = pd.merge(...)
   </CODE_BLOCK>

{format_instructions}
"""

# CSV Description template
CSV_DESCRIPTION_TEMPLATE = """
You are a CSV Data Analyst. Given the following metadata about a CSV file, 
provide a clear and concise description of what the data represents and what kind of 
insights or analysis could be performed with it.

CSV Metadata:
Filename: {filename}
Number of Rows: {num_rows}
Number of Columns: {num_columns}

Columns:
{columns_info}

Sample Data:
{sample_data}

Please generate a concise but informative description that explains what this 
data represents and what kind of questions it could answer. Be specific and clear.
"""
