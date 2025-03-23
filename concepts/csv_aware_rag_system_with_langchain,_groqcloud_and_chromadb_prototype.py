# -*- coding: utf-8 -*-
"""CSV-Aware RAG System with Langchain, GroqCloud and ChromaDB refined.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1HL9gd4gIkjGmY6XOQEzdfABjV_9ZLmCf
"""

!pip install -q langchain langchain_groq chromadb pandas pydantic python-dotenv langchain_community

import os
import pandas as pd
import numpy as np
import json
import ast
import re
from typing import List, Dict, Any, Optional
import tempfile
import uuid
from io import StringIO

# Langchain imports
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import LLMChain
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser

import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

# Set up environment
from google.colab import userdata
import os

GROQ_API_KEY = userdata.get('GROQ_API_KEY')
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# Initialize models
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant",  # Using llama3-70b for better reasoning
    temperature=0,
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()]
)

# Initialize models
llmSmall = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant",  # Using llama3-70b for better reasoning
    temperature=0,
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()]
)

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

# Initialize ChromaDB
persist_directory = "./chroma_db"
vectorstore = Chroma(
    persist_directory=persist_directory,
    embedding_function=embeddings
)

# Define Pydantic model for CSV description
class CSVDescription(BaseModel):
    filename: str = Field(description="The name of the CSV file")
    num_rows: int = Field(description="Number of rows in the CSV")
    num_columns: int = Field(description="Number of columns in the CSV")
    columns: List[Dict[str, str]] = Field(
        description="List of column names and their data types")
    description: str = Field(
        description="A descriptive overview of what the CSV contains")
    sample_data: str = Field(
        description="Sample rows from the CSV in string format")
    basic_stats: Optional[Dict[str, Any]] = Field(
        description="Basic statistical information about numerical columns")

# Define Pydantic model for the pandas query generator


class PandasQueryGenerator(BaseModel):
    analysis: str = Field(
        description="Analysis of the user's question and how it relates to the CSV data")
    pandas_code: str = Field(
        description="Complete pandas code to answer the user's question")
    explanation: str = Field(
        description="Explanation of what the code does and why it answers the question")

def scan_csv_folder(folder_path):
    """Scan a folder for CSV files and return their paths"""
    csv_files = []
    for file in os.listdir(folder_path):
        if file.endswith('.csv'):
            csv_files.append(os.path.join(folder_path, file))
    return csv_files


def detect_csv_relationships(csv_paths):
    """Detect potential relationships between CSV files"""
    # Store dataframes and their column information
    dataframes = {}
    column_info = {}

    # Load all CSVs
    for path in csv_paths:
        filename = os.path.basename(path)
        df = pd.read_csv(path)
        dataframes[filename] = df

        # Store column names and sample values for each dataframe
        column_info[filename] = {
            "columns": df.columns.tolist(),
            "samples": {col: df[col].dropna().head(5).tolist() for col in df.columns}
        }

    # Create a graph to represent relationships
    relationship_graph = nx.Graph()

    # Add all CSV files as nodes
    for filename in dataframes.keys():
        relationship_graph.add_node(filename)

    # Dictionary to store potential join keys
    potential_joins = defaultdict(list)

    # Detect potential relationships
    for file1 in dataframes.keys():
        for file2 in dataframes.keys():
            if file1 != file2:
                for col1 in column_info[file1]["columns"]:
                    for col2 in column_info[file2]["columns"]:
                        # Check if column names match exactly or contain common patterns (id, key, etc.)
                        name_match = (col1.lower() == col2.lower() or
                                      (("id" in col1.lower() and "id" in col2.lower()) and
                                      (col1.replace("id", "") == col2.replace("id", ""))))

                        # Check for data type compatibility
                        try:
                            type_match = (
                                dataframes[file1][col1].dtype == dataframes[file2][col2].dtype)
                        except:
                            type_match = False

                        # Check for value overlaps in samples
                        sample1 = set(str(x)
                                      for x in column_info[file1]["samples"][col1])
                        sample2 = set(str(x)
                                      for x in column_info[file2]["samples"][col2])
                        value_overlap = len(sample1.intersection(sample2)) > 0

                        if (name_match and type_match) or (type_match and value_overlap):
                            relationship_graph.add_edge(file1, file2)
                            potential_joins[(file1, file2)].append(
                                (col1, col2))

    return relationship_graph, potential_joins, dataframes


def visualize_csv_relationships(graph):
    """Visualize the relationships between CSV files"""
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(graph)
    nx.draw(graph, pos, with_labels=True, node_color='lightblue',
            node_size=1500, font_size=10, font_weight='bold')
    plt.title("CSV Relationships")
    plt.savefig('csv_relationships.png')
    plt.close()


def generate_multi_csv_description(csv_folder):
    """Generate descriptions for multiple CSVs and detect relationships"""
    csv_paths = scan_csv_folder(csv_folder)

    if not csv_paths:
        return "No CSV files found in the specified folder."

    # Process each CSV to get descriptions
    csv_descriptions = {}
    dataframes = {}

    for path in csv_paths:
        filename = os.path.basename(path)
        csv_desc, df = generate_csv_description(path, filename)
        csv_descriptions[filename] = csv_desc
        dataframes[filename] = df
        store_csv_description(csv_desc)

    # Detect relationships between CSVs
    relationship_graph, potential_joins, _ = detect_csv_relationships(
        csv_paths)

    # Visualize relationships
    visualize_csv_relationships(relationship_graph)

    # Create a textual summary of relationships
    relationships_summary = "CSV Relationship Summary:\n"
    for (file1, file2), join_keys in potential_joins.items():
        relationships_summary += f"\n{file1} can be joined with {file2} on:\n"
        for col1, col2 in join_keys:
            relationships_summary += f"  - {file1}.{col1} = {file2}.{col2}\n"

    # Store relationship information in vectorstore for retrieval
    # Convert complex metadata to simple strings to avoid ChromaDB errors
    simplified_joins = {}
    for (file1, file2), joins in potential_joins.items():
        key = f"{file1}:{file2}"
        # Convert the list of column pairs to a simple string representation
        value = ",".join([f"{col1}:{col2}" for col1, col2 in joins])
        simplified_joins[key] = value

    relationship_doc = Document(
        page_content=relationships_summary,
        metadata={
            "type": "csv_relationships",
            "join_data": json.dumps(simplified_joins)  # Convert to JSON string
        }
    )
    vectorstore.add_documents([relationship_doc])
    vectorstore.persist()

    return {
        "csv_descriptions": csv_descriptions,
        "dataframes": dataframes,
        "relationship_graph": relationship_graph,
        "potential_joins": potential_joins,
        "relationships_summary": relationships_summary
    }

class SimplePandasExecutor:
    """
    Executes pandas queries directly without strict safety checks.
    Use only with trusted inputs in controlled environments.
    """

    def __init__(self, dataframe):
        """Initialize with the dataframe to be queried"""
        self.df = dataframe

    def execute_query(self, code: str):
        """Execute the pandas query using exec() and return the result"""
        # print(f"Executing query:\n{code}\n")

        # Create execution environment with dataframe and common libraries
        local_vars = {"df": self.df, "pd": pd, "np": np}

        try:
            # Execute the code using exec()
            exec(code, globals(), local_vars)

            # Return the result if available
            if 'result' in local_vars:
                # print("Query executed successfully.")
                return local_vars['result']
            else:
                # print("Query executed but no result variable was defined.")
                return "Query executed successfully, but no result variable was found."
        except Exception as e:
            print(f"Error during execution: {str(e)}")
            raise

def generate_csv_description(csv_path, filename=None):
    """Generate a detailed description of a CSV file including metadata and statistics"""
    if filename is None:
        filename = os.path.basename(csv_path)

    # Read the CSV file
    df = pd.read_csv(csv_path)

    # Get basic metadata
    num_rows, num_columns = df.shape

    # Get column descriptions
    columns = []
    for col_name in df.columns:
        col_type = str(df[col_name].dtype)
        sample_values = df[col_name].dropna().head(5).tolist()
        # Ensure sample values are serializable
        sample_values = [json_serializable(val) for val in sample_values]

        columns.append({
            "name": col_name,
            "dtype": col_type,
            "sample_values": sample_values
        })

    # Get sample data for visualization
    sample_data = df.head(5).to_string()

    # Calculate basic statistics for numerical columns
    basic_stats = {}
    for col in df.select_dtypes(include=['number']).columns:
        basic_stats[col] = {
            "mean": json_serializable(df[col].mean()),
            "median": json_serializable(df[col].median()),
            "std": json_serializable(df[col].std()),
            "min": json_serializable(df[col].min()),
            "max": json_serializable(df[col].max())
        }

    # Generate a description of the dataset
    description_prompt = f"""
    Please provide a concise description of this CSV dataset based on the following information:
    - Filename: {filename}
    - Number of rows: {num_rows}
    - Number of columns: {num_columns}
    - Columns: {', '.join([f"{col['name']} ({col['dtype']})" for col in columns])}
    - Sample data: {sample_data}

    Describe what kind of data this is and what it might be used for in 2-3 sentences.
    """

    # Use the small LLM model to generate description
    description_chain = LLMChain(
        llm=llmSmall,
        prompt=ChatPromptTemplate.from_template("{input}")
    )
    description = description_chain.run(description_prompt).strip()

    # Create the description dictionary
    csv_desc = {
        "filename": filename,
        "num_rows": num_rows,
        "num_columns": num_columns,
        "columns": columns,
        "description": description,
        "sample_data": sample_data,
        "basic_stats": basic_stats
    }

    return csv_desc, df


# Add this function to your code before the generate_csv_description function
def json_serializable(obj):
    """Convert numpy types to Python standard types for JSON serialization"""
    import numpy as np

    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    else:
        return obj

    # Then modify the store_csv_description function to use this converter:


def store_csv_description(csv_desc):
    """Store the CSV description in ChromaDB"""
    # Convert the description object to a string for embedding
    description_text = f"""
    Filename: {csv_desc['filename']}
    Description: {csv_desc['description']}
    Columns: {', '.join([col['name'] for col in csv_desc['columns']])}
    """

    # Create a Document object
    document = Document(
        page_content=description_text,
        metadata={
            "filename": csv_desc['filename'],
            "type": "csv_description",
            "full_description": json.dumps(csv_desc, default=json_serializable)
        }
    )

    # Add to ChromaDB
    vectorstore.add_documents([document])
    vectorstore.persist()

    return document


def retrieve_csv_description(query, filename=None):
    """Retrieve the relevant CSV description based on the query"""
    try:
        # Search for relevant documents
        if filename:
            # ChromaDB uses a different filtering format
            filter_dict = {"$and": [
                {"filename": {"$eq": filename}},
                {"type": {"$eq": "csv_description"}}
            ]}
            documents = vectorstore.similarity_search(
                query, k=1, filter=filter_dict)
        else:
            documents = vectorstore.similarity_search(query, k=1)

        if documents:
            # Extract the full description from metadata
            csv_desc = json.loads(documents[0].metadata["full_description"])
            return csv_desc

    except Exception as e:
        print(f"Error retrieving from vector database: {str(e)}")

    return None

def generate_pandas_multi_query(csv_descriptions, potential_joins, user_question):
    """Generate a pandas query that can work across multiple CSV files"""

    # Create a description of all available tables and their relationships
    tables_description = ""
    for filename, desc in csv_descriptions.items():
        tables_description += f"\nTable: {filename}\n"
        tables_description += f"Description: {desc['description']}\n"
        tables_description += "Columns:\n"
        for col in desc['columns']:
            tables_description += f"  - {col['name']}: {col['dtype']} (Sample values: {col['sample_values']})\n"
        tables_description += "\n"

    # Create a description of table relationships
    join_description = "Table Relationships:\n"
    for (file1, file2), joins in potential_joins.items():
        join_description += f"{file1} can be joined with {file2} on:\n"
        for col1, col2 in joins:
            join_description += f"  - {file1}.{col1} = {file2}.{col2}\n"

    # Create the prompt for the LLM
    prompt_template = """
        You are a data analyst expert in pandas. Based on the CSV descriptions and relationships,
        generate pandas code that answers the user's question by potentially joining multiple tables.

        Available Tables:
        {tables_description}

        Table Relationships:
        {join_description}

        User Question: {question}

        First, analyze the question and determine:
        1. Which tables are needed to answer the question
        2. How these tables should be joined (if multiple tables are needed)
        3. What operations are required on the joined data

        Then, write clean, efficient pandas code that answers the question.

        The code should:
        1. Start by loading each required dataframe (assume they're already loaded with names matching their filenames)
        2. All the files are in csv_data folder so for pd.read_csv use pd.read_csv('csv_data/filename.csv')
        3. Perform necessary joins if multiple tables are needed
        4. Use only standard pandas and numpy operations
        5. Assign the final result to a variable named "result"
        6. Include comments explaining key steps
        7. Avoid using .item() method which can cause errors
        8. When accessing single values from DataFrames or Series, prefer using .iloc[0] or direct indexing
        9. Avoid using any disallowed functions and modules (os, sys, eval, exec, open, etc.)

        {format_instructions}
    """

    parser = PydanticOutputParser(pydantic_object=PandasQueryGenerator)

    prompt = ChatPromptTemplate.from_template(
        template=prompt_template,
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        }
    )

    # Run the chain
    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.run(
        tables_description=tables_description,
        join_description=join_description,
        question=user_question
    )

    # Parse the response
    try:
        query_generator = parser.parse(response)
        return query_generator
    except Exception as e:
        # If parsing fails, extract code using regex as fallback
        code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            pandas_code = code_match.group(1)
            return PandasQueryGenerator(
                analysis="Unable to parse full analysis",
                pandas_code=pandas_code,
                explanation="Code extracted from response"
            )
        else:
            raise ValueError(
                f"Failed to extract pandas code from LLM response: {e}")


def process_multi_csv_query(csv_folder, user_question):
    """Process a user query that may involve multiple CSV files"""

    # Step 1: Scan folder and analyze CSVs
    # Check if we already have relationship info in ChromaDB
    relationships_doc = vectorstore.similarity_search(
        "csv relationships joins tables",
        k=1,
        filter={"type": {"$eq": "csv_relationships"}}
    )

    if relationships_doc:
        # We have existing relationship info, retrieve individual CSV descriptions
        csv_paths = scan_csv_folder(csv_folder)
        csv_descriptions = {}
        dataframes = {}

        for path in csv_paths:
            filename = os.path.basename(path)
            csv_desc = retrieve_csv_description("", filename=filename)
            if csv_desc:
                csv_descriptions[filename] = csv_desc
                dataframes[filename] = pd.read_csv(path)
            else:
                # Generate for this file if not found
                csv_desc, df = generate_csv_description(path, filename)
                csv_descriptions[filename] = csv_desc
                dataframes[filename] = df
                store_csv_description(csv_desc)

        # Get relationship info and parse from JSON string
        join_data_str = relationships_doc[0].metadata.get("join_data", "{}")
        simplified_joins = json.loads(join_data_str)

        # Convert back to the original format
        potential_joins_dict = defaultdict(list)
        for key, value in simplified_joins.items():
            file1, file2 = key.split(":")
            col_pairs = value.split(",")
            for col_pair in col_pairs:
                if ":" in col_pair:  # Ensure the string has the expected format
                    col1, col2 = col_pair.split(":")
                    potential_joins_dict[(file1, file2)].append((col1, col2))

        potential_joins = potential_joins_dict
    else:
        # Generate everything from scratch
        analysis_result = generate_multi_csv_description(csv_folder)
        csv_descriptions = analysis_result["csv_descriptions"]
        dataframes = analysis_result["dataframes"]
        potential_joins = analysis_result["potential_joins"]

    # Step 2: Generate pandas query for multi-table operation
    query_generator = generate_pandas_multi_query(
        csv_descriptions, potential_joins, user_question)

    # Step 3: Execute the query
    return execute_generated_query(query_generator, dataframes)


def execute_generated_query(query_generator, dataframes):
    """Execute the generated pandas query with the provided dataframes"""
    local_vars = {"pd": pd, "np": np}

    for filename, df in dataframes.items():
        var_name = os.path.splitext(filename)[0]
        local_vars[var_name] = df

        local_vars[filename] = df

        query_generator.pandas_code = query_generator.pandas_code.replace(
            f"pd.read_csv('{filename}')",
            f"locals()['{filename}']"
        )
        query_generator.pandas_code = query_generator.pandas_code.replace(
            f"pd.read_csv('{var_name}.csv')",
            f"locals()['{filename}']"
        )

        # Handle path with folder
        full_path = os.path.join("csv_data", filename)
        query_generator.pandas_code = query_generator.pandas_code.replace(
            f"pd.read_csv('{full_path}')",
            f"locals()['{filename}']"
        )

    try:
        # Execute the code
        exec(query_generator.pandas_code, globals(), local_vars)

        # Return the result if available
        if 'result' in local_vars:
            result = local_vars['result']
            return {
                "result": result,
                "explanation": query_generator.explanation,
                "code": query_generator.pandas_code,
                "status": "success"
            }
        else:
            return {
                "result": None,
                "explanation": "No result found in the executed code.",
                "code": query_generator.pandas_code,
                "status": "no_result"
            }

    except Exception as e:
        return {
            "result": None,
            "explanation": f"Error executing the query: {str(e)}",
            "code": query_generator.pandas_code,
            "status": "error"
        }


# Function to process and add CSVs to the vector database
def process_and_store_csvs(csv_folder):
    """Process CSV files in the folder and store their descriptions in the vector database."""
    csv_paths = scan_csv_folder(csv_folder)
    for path in csv_paths:
        filename = os.path.basename(path)
        # Check if the CSV is already in the vector database
        existing_desc = retrieve_csv_description("", filename=filename)
        if not existing_desc:
            # Generate and store the description if not already present
            csv_desc, _ = generate_csv_description(path, filename)
            store_csv_description(csv_desc)

    # Generate relationships between CSVs
    analysis_result = generate_multi_csv_description(csv_folder)
    print(
        f"Processed {len(csv_paths)} CSV files and stored in the vector database.")
    return analysis_result

# Function to handle user queries
def handle_user_query(user_question, csv_folder="csv_data"):
    """Handle user queries by interacting with the vector database."""
    # Retrieve relationship information from the vector database
    relationships_doc = vectorstore.similarity_search(
        "csv relationships joins tables",
        k=1,
        filter={"type": {"$eq": "csv_relationships"}}
    )

    if relationships_doc:
        # If relationships exist, retrieve CSV descriptions
        csv_descriptions = {}
        dataframes = {}
        csv_paths = scan_csv_folder(csv_folder)

        for path in csv_paths:
            filename = os.path.basename(path)
            csv_desc = retrieve_csv_description("", filename=filename)
            if csv_desc:
                csv_descriptions[filename] = csv_desc
                dataframes[filename] = pd.read_csv(path)

        # Parse relationships from the vector database
        join_data_str = relationships_doc[0].metadata.get("join_data", "{}")
        simplified_joins = json.loads(join_data_str)
        potential_joins = defaultdict(list)

        for key, value in simplified_joins.items():
            file1, file2 = key.split(":")
            col_pairs = value.split(",")
            for col_pair in col_pairs:
                if ":" in col_pair:
                    col1, col2 = col_pair.split(":")
                    potential_joins[(file1, file2)].append((col1, col2))

        # Generate and execute the query
        query_generator = generate_pandas_multi_query(
            csv_descriptions, potential_joins, user_question
        )
        return execute_generated_query(query_generator, dataframes)
    else:
        return {
            "result": None,
            "explanation": "No relationships found in the vector database. Please process CSVs first.",
            "code": None,
            "status": "no_relationships"
        }


# Function to display query results in a better way
def display_query_result(result_dict):
    """Display the query result in a nicely formatted way"""
    if result_dict["status"] == "success":
        print("\n=== QUERY RESULT ===")
        print(result_dict["result"])

        print("\n=== EXPLANATION ===")
        print(result_dict["explanation"])

    else:
        print("\n=== ERROR ===")
        print(result_dict["explanation"])

# add the files into the vectior database
os.makedirs("csv_data", exist_ok=True)

analysis_result = process_and_store_csvs("csv_data")
print("CSV processing complete.")
print(
        f"Found relationships between these files: {list(analysis_result['potential_joins'].keys())}")

#user query
result = handle_user_query("How many employees do i have?")
display_query_result(result)

#user query
result = handle_user_query("Create a table of all the employees with name , department and their average salary?")
display_query_result(result)

#user query
result = handle_user_query("Create a pie chart to show department wise employee destribution")
display_query_result(result)

#user query
result = handle_user_query("Show department wise employee average salary")
display_query_result(result)

#user query
result = handle_user_query("Show a line graph of daily attendance of employee Jesse	Sanchez, use month as interval and use multiple line to show Absent,Vacation,Present or Sick Leave ")
display_query_result(result)