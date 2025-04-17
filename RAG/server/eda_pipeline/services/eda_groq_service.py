import os
import re
import pandas as pd
import numpy as np
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from collections import defaultdict

# Langchain imports
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.output_parsers import PydanticOutputParser

# Import custom modules
from eda_pipeline.eda_db.eda_vectordb_handeller import EdaVectorDBHandler
from eda_pipeline.templates.llm_templates import (
    REGULAR_QUERY_TEMPLATE, 
    RELATIONSHIP_QUERY_TEMPLATE,
    CSV_DESCRIPTION_TEMPLATE
)

class PandasQueryGenerator(BaseModel):
    """Model for generating pandas queries"""
    analysis: str = Field(description="Analysis of the user's question and how it relates to the CSV data")
    pandas_code: str = Field(description="Complete pandas code to answer the user's question. Wrap each code block with <CODE_BLOCK> and </CODE_BLOCK> tags if multiple approaches are provided.")
    explanation: str = Field(description="Explanation of what the code does and why it answers the question")

class SimplePandasExecutor:
    """Executes pandas queries in a controlled environment"""
    def __init__(self, dataframes=None):
        """Initialize with one or more dataframes"""
        if dataframes is None:
            dataframes = {}
        self.dataframes = dataframes
        print(f"[DEBUG] SimplePandasExecutor initialized with {len(dataframes)} dataframes: {list(dataframes.keys())}")
    
    def add_dataframe(self, name, df):
        """Add a dataframe to the execution environment"""
        self.dataframes[name] = df
        print(f"[DEBUG] Added dataframe '{name}' with shape {df.shape}")
    
    def execute_query(self, code):
        """Execute pandas code and return the result"""
        print(f"[DEBUG] SimplePandasExecutor.execute_query() - Starting execution")
        print(f"[DEBUG] Available dataframes: {list(self.dataframes.keys())}")
        
        # Create execution environment with dataframes and common libraries
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        from datetime import datetime, timedelta
        
        local_vars = {
            "pd": pd, 
            "np": np, 
            "plt": plt,
            "datetime": datetime,
            "timedelta": timedelta,
            **self.dataframes
        }
        
        try:
            print(f"[DEBUG] Executing pandas code...")
            # Execute the code
            exec(code, globals(), local_vars)
            
            # Return the result if available
            if 'result' in local_vars:
                return local_vars['result']
            else:
                print(f"[DEBUG] No 'result' variable found in executed code")
                return None
                
        except Exception as e:
            print(f"[DEBUG] Error executing code: {str(e)}")
            raise

class EdaGroqService:
    """Service for handling Groq LLM interactions"""
    
    def __init__(self, api_key=None, model_name="llama3-70b-8192"):
        """Initialize with optional API key"""
        # Use provided API key or get from environment
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "your_default_api_key")
        self.model_name = model_name
        
        # Initialize LLM instances for different purposes
        self.llm = ChatGroq(
            api_key=self.api_key,
            model_name=self.model_name,
            temperature=0.2
        )
        
        # Initialize the vector database handler
        self.vectordb_handler = EdaVectorDBHandler()
        
        # Initialize the pandas query generator parser
        self.pandas_query_parser = PydanticOutputParser(pydantic_object=PandasQueryGenerator)

    def _extract_code_from_raw_response(self, raw_response):
        """Extract code blocks from raw LLM response when parsing fails"""
        # First check for custom code block delimiters
        code_delimiter_pattern = r"<CODE_BLOCK>([\s\S]*?)</CODE_BLOCK>"
        code_blocks = re.findall(code_delimiter_pattern, raw_response)
        
        if code_blocks:
            return code_blocks
            
        # Try to extract Python code blocks with triple backticks
        code_block_pattern = r"```(?:python)?\s*([\s\S]*?)```"
        code_blocks = re.findall(code_block_pattern, raw_response)
        
        if code_blocks:
            return code_blocks
        
        # If no code blocks found, try to extract code between 'pandas_code' markers
        pandas_code_pattern = r"pandas_code[\"']\s*:\s*[\"']+([\s\S]*?)[\"']+"
        pandas_matches = re.findall(pandas_code_pattern, raw_response)
        
        if pandas_matches:
            return [pandas_matches[0]]
        
        # If all else fails, return empty list
        return []

    
    def generate_csv_description(self, csv_metadata):
        """Generate a descriptive summary of a CSV file from its metadata"""
        # Create a prompt for the LLM to generate a description
        prompt = ChatPromptTemplate.from_template(CSV_DESCRIPTION_TEMPLATE)
        
        # Format column information
        columns_info = "\n".join([
            f"- {col['name']} ({col['dtype']}): Sample values: {col['sample_values'][:3]}"
            for col in csv_metadata['columns']
        ])
        
        # Set up the chain
        chain = LLMChain(llm= ChatGroq(
            groq_api_key=self.api_key,
            model_name="llama-3.1-8b-instant",
            temperature=0.1,
            streaming=False
        ), prompt=prompt)
        
        # Generate the description
        description = chain.run({
            "filename": csv_metadata['filename'],
            "num_rows": csv_metadata['num_rows'],
            "num_columns": csv_metadata['num_columns'],
            "columns_info": columns_info,
            "sample_data": csv_metadata['sample_data'][:500]  # Truncate if too long
        })
        
        # Update the metadata with the description
        csv_metadata['description'] = description.strip()
        
        print(f"✅ Generated description for {csv_metadata['filename']}")
        # Return the updated metadata
        return csv_metadata
    
    def process_user_query(self, query: str, user_id=None, scrape_id=None):
        """Process a user query about CSV data"""

        print(f"\n[DEBUG] Processing query: '{query}' for user_id: {user_id}, scrape_id: {scrape_id}")

            # Check if this is a conversational query
        if self._is_conversational_query(query):
            return self._handle_conversational_query(query)
            
        # First, retrieve relevant CSV descriptions from the vector database
        relevant_csvs = self.vectordb_handler.retrieve_csv_descriptions(
            query=query, k=3, user_id=user_id, scrape_id=scrape_id
        )

        # First, retrieve relevant CSV descriptions from the vector database
        relevant_csvs = self.vectordb_handler.retrieve_csv_descriptions(
            query=query, k=3, user_id=user_id, scrape_id=scrape_id
        )

        print(f"[DEBUG] Found {len(relevant_csvs)} relevant CSVs: {[csv['filename'] for csv in relevant_csvs]}")

        
        if not relevant_csvs:
            return {
                "answer": "I couldn't find any relevant CSV data to answer your question.",
                "sources": [],
                "code": None,
                "result": None
            }
        
        # Format the retrieved CSV information for the LLM
        csv_info = self._format_csv_info_for_llm(relevant_csvs)
        
        # Check if we have relationship data AND if the query might be about relationships
        # First get relationship information
        relationships, relationship_text = self.vectordb_handler.retrieve_csv_relationships(user_id=user_id)
        
        # Check if relationships exist AND (query suggests relationships OR we have multiple CSVs)
        is_relationship_query = re.search(r'relation|connect|join|link|between', query.lower())
        has_multiple_csvs = len(set([csv.get('filename', '') for csv in relevant_csvs])) > 1
        
        if relationships and (is_relationship_query or has_multiple_csvs):
            print(f"[DEBUG] Routing to relationship handler: is_relationship_query={is_relationship_query}, has_multiple_csvs={has_multiple_csvs}")
            return self._handle_relationship_query(query, relevant_csvs, user_id, scrape_id)
        
        # Generate answer for regular query
        return self._handle_regular_query(query, relevant_csvs, csv_info)


    def _is_conversational_query(self, query):
        """Determine if a query is conversational rather than data-related"""
        # Simple heuristic - can be improved with more patterns
        conversational_patterns = [
            r'^hi\b', r'^hello\b', r'^hey\b', r'^greetings', 
            r'^how are you', r'^what\'s up', r'^good morning',
            r'^good afternoon', r'^good evening', r'^thanks', r'^thank you',
            r'^who are you', r'^what can you do', r'^help me'
        ]
        
        return any(re.search(pattern, query.lower()) for pattern in conversational_patterns)

    def _handle_conversational_query(self, query):
        """Handle general conversational queries that don't require code"""
        # Use a simple template for conversational responses
        conversational_llm = ChatGroq(
            api_key=self.api_key, 
            model_name="llama-3.1-8b-instant",  # Use smaller model for simple responses
            temperature=0.7
        )
        
        prompt = ChatPromptTemplate.from_template(
            """You are a helpful data assistant that can analyze CSV files. 
            The user has sent a conversational message: "{query}"
            
            Respond in a friendly, concise way. If they're greeting you, greet them back
            and briefly mention you can help analyze their data with Python and pandas.
            If they're asking what you can do, explain your capabilities with CSV analysis.
            Keep your response under 3 sentences."""
        )
        
        chain = LLMChain(llm=conversational_llm, prompt=prompt)
        response = chain.run({"query": query})
        
        return {
            "answer": response.strip(),
            "sources": [],
            "code_blocks": [],
            "result": None
        }
    
    def _format_csv_info_for_llm(self, relevant_csvs):
        """Format CSV information for the LLM prompt"""
        csv_info = ""
        for idx, csv in enumerate(relevant_csvs):
            metadata = csv.get("metadata", {})
            filename = csv['filename']  # e.g., retail_sales.csv
            filepath = csv.get('filepath', '')  # Full filepath
            
            # Format the filepath to be relative to media/uploads
            # Check if filepath contains a full Windows path
            if filepath and '\\' in filepath:
                # Extract the path structure after "media/uploads"
                try:
                    # Try to find "media\\uploads" or its Windows path variant
                    if "media\\uploads" in filepath:
                        parts = filepath.split("media\\uploads\\")
                        if len(parts) > 1:
                            filepath = f"media/uploads/{parts[1].replace('\\', '/')}"
                    elif "media/uploads" in filepath:
                        parts = filepath.split("media/uploads/")
                        if len(parts) > 1:
                            filepath = f"media/uploads/{parts[1]}"
                except Exception:
                    # If any error occurs, keep original path
                    pass
            
            # Create filename without extension for variable name
            variable_name = os.path.splitext(filename)[0]  # e.g., retail_sales
            
            csv_info += f"\n--- CSV {idx+1}: {filename} ---\n"
            # Format the filepath in a code-friendly way
            csv_info += f"Variable name to use: {variable_name}\n"
            csv_info += f"Code to load: {variable_name} = pd.read_csv('{filepath}')\n"
            csv_info += f"Description: {csv.get('description', '')}\n"
            csv_info += f"Rows: {metadata.get('num_rows', 'Unknown')}, Columns: {metadata.get('num_columns', 'Unknown')}\n"
            
            # Add column information
            if "columns" in metadata:
                csv_info += "Columns:\n"
                for col in metadata["columns"]:
                    csv_info += f"- {col['name']} ({col['dtype']}): {col['sample_values'][:3]}\n"
            
            # Add sample data if available
            if "sample_data" in metadata:
                csv_info += f"Sample Data:\n{metadata['sample_data'][:300]}...\n"
        
        return csv_info
        

    def _handle_relationship_query(self, query, relevant_csvs, user_id, scrape_id):
        """Handle queries about relationships between CSVs"""
        print(f"[DEBUG] Handling relationship query: {query}")
        # Get relationship information from vector database
        relationships, relationship_text = self.vectordb_handler.retrieve_csv_relationships(
            user_id=user_id
        )
        
        if not relationships:
            return {
                "answer": "I couldn't find any relationship information between the CSV files.",
                "sources": [csv["filename"] for csv in relevant_csvs],
                "code_blocks": [],
                "result": None
            }
        
        # Format CSV information
        csv_info = self._format_csv_info_for_llm(relevant_csvs)
        
        # Create a prompt for the LLM to generate pandas code for relationships
        format_instructions = self.pandas_query_parser.get_format_instructions()
        prompt = ChatPromptTemplate.from_template(RELATIONSHIP_QUERY_TEMPLATE)
        
        # Set up the chain with a higher temperature for more creative responses
        creative_llm = ChatGroq(
            api_key=self.api_key,
            model_name=self.model_name,
            temperature=0.4
        )
        
        chain = LLMChain(llm=creative_llm, prompt=prompt)
        
        try:
            # Generate the pandas code
            response = chain.run({
                "csv_info": csv_info,
                "relationship_text": relationship_text,
                "query": query,
                "format_instructions": format_instructions
            })
            
            try:
                # Try to parse the response properly
                parsed_response = self.pandas_query_parser.parse(response)
                
                # Extract multiple code blocks if present
                code_blocks = [parsed_response.pandas_code]
                if "<CODE_BLOCK>" in parsed_response.pandas_code:
                    code_blocks = re.findall(r"<CODE_BLOCK>([\s\S]*?)</CODE_BLOCK>", parsed_response.pandas_code)
                
                return {
                    "answer": parsed_response.explanation,
                    "sources": [csv["filename"] for csv in relevant_csvs],
                    "code_blocks": code_blocks,
                    "result": None
                }
            except Exception as parsing_error:
                print(f"[ERROR] Error parsing relationship LLM response: {str(parsing_error)}")
                print(f"[DEBUG] Raw relationship LLM response: {response[:500]}...")
                
                # Try to extract code blocks using regex
                code_blocks = self._extract_code_from_raw_response(response)
                
                # Try to extract explanation 
                explanation_pattern = r"explanation[\"']\s*:\s*[\"']+([\s\S]*?)[\"']+"
                explanation_matches = re.findall(explanation_pattern, response)
                explanation = explanation_matches[0] if explanation_matches else "Analysis of the relationship between datasets."
                
                if code_blocks:
                    return {
                        "answer": explanation,
                        "sources": [csv["filename"] for csv in relevant_csvs],
                        "code_blocks": code_blocks,
                        "result": None
                    }
                else:
                    return {
                        "answer": "I'm sorry, I couldn't generate appropriate code for your relationship query.",
                        "sources": [csv["filename"] for csv in relevant_csvs],
                        "code_blocks": [],
                        "result": f"Error parsing generated code: {str(parsing_error)}"
                    }
        except Exception as e:
                print(f"[ERROR] Relationship chain execution error: {str(e)}")
                
                return {
                    "answer": "I'm sorry, I encountered an error while processing your relationship query.",
                    "sources": [csv["filename"] for csv in relevant_csvs],
                    "code_blocks": [],
                    "result": {
                        "type": "error",
                        "message": f"Error generating relationship code: {str(e)}"
                    }
                }


    def _handle_regular_query(self, query, relevant_csvs, csv_info):
        """Handle regular queries about CSV data"""
        # Create a prompt for the LLM to generate pandas code
        format_instructions = self.pandas_query_parser.get_format_instructions()
        prompt = ChatPromptTemplate.from_template(REGULAR_QUERY_TEMPLATE)
        
        # Set up the chain with a higher temperature for more creative responses
        creative_llm = ChatGroq(
            api_key=self.api_key,
            model_name=self.model_name,
            temperature=0.4
        )
        
        chain = LLMChain(llm=creative_llm, prompt=prompt)
        
        try:
            # Generate the pandas code
            response = chain.run({
                "csv_info": csv_info,
                "query": query,
                "format_instructions": format_instructions
            })
            
            # Parse the response
            try:
                parsed_response = self.pandas_query_parser.parse(response)
                
                # Extract multiple code blocks if present
                code_blocks = [parsed_response.pandas_code]
                if "<CODE_BLOCK>" in parsed_response.pandas_code:
                    code_blocks = re.findall(r"<CODE_BLOCK>([\s\S]*?)</CODE_BLOCK>", parsed_response.pandas_code)
                
                # Return the code without executing it yet - execution will happen in the view
                return {
                    "answer": parsed_response.explanation,
                    "sources": [csv["filename"] for csv in relevant_csvs],
                    "code_blocks": code_blocks,
                    "result": None  # The code will be executed in the view
                }
            except Exception as e:
                print(f"[ERROR]_handle_regular_query Error parsing LLM response: {str(e)}")
                print(f"[DEBUG]_handle_regular_query Raw LLM response: {response}...") 
                
                # Try to extract code blocks using regex
                code_blocks = self._extract_code_from_raw_response(response)
                
                # Try to extract explanation
                explanation_pattern = r"explanation[\"']\s*:\s*[\"']+([\s\S]*?)[\"']+"
                explanation_matches = re.findall(explanation_pattern, response)
                explanation = explanation_matches[0] if explanation_matches else "Analysis of the data."
                
                return {
                    "answer": explanation,
                    "sources": [csv["filename"] for csv in relevant_csvs],
                    "code_blocks": code_blocks,
                    "result": None
                }
        
        except Exception as e:
            print(f"[ERROR]_handle_regular_query Error handling query: {str(e)}")
            
            return {
                "answer": "I'm sorry",
                "sources": [csv["filename"] for csv in relevant_csvs],
                "code_blocks": [],
                "result": f"Error generating code: {str(e)}"
            }

 
    def format_output_for_display(self, result):
        """Format the output for display in a web interface"""
        if isinstance(result, pd.DataFrame):
            # Convert DataFrame to HTML for display
            return {
                "type": "dataframe",
                "html": result.to_html(classes="table table-striped", index=True),
                "records": result.to_dict(orient="records"),
                "columns": result.columns.tolist(),
                "shape": result.shape
            }
        
        elif isinstance(result, pd.Series):
            # Convert Series to dictionary
            return {
                "type": "series",
                "data": result.to_dict(),
                "name": result.name
            }
        
        elif isinstance(result, (dict, list)):
            # Return dictionaries and lists directly
            return {
                "type": "collection",
                "data": result
            }
        
        else:
            # For other types, convert to string
            return {
                "type": "other",
                "data": str(result)
            }
    
    def execute_pandas_code(self, code, dataframes):
        """Execute pandas code and return the result"""
        print(f"[DEBUG] SimplePandasExecutor.execute_query() - Starting execution")
        print(f"[DEBUG] Available dataframes: {list(dataframes.keys())}")
        
        # Create execution environment with dataframes and common libraries
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import os
        import re
        import json
        from datetime import datetime, timedelta
        
        # First, check if code is trying to directly load CSVs with specific paths
        path_pattern = r"pd\.read_csv\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        path_matches = re.findall(path_pattern, code)
        
        # If there are direct path references and dataframes were provided
        if path_matches and dataframes:
            try:
                # Try to modify the code to use provided dataframes instead
                for path in path_matches:
                    # Extract the filename from the path
                    filename = os.path.basename(path)
                    name_without_ext = os.path.splitext(filename)[0].lower().replace(' ', '_')
                    
                    # If we have this dataframe already loaded, replace the read_csv call
                    if name_without_ext in dataframes:
                        code = code.replace(f"pd.read_csv('{path}')", name_without_ext)
                        code = code.replace(f'pd.read_csv("{path}")', name_without_ext)
                        print(f"[DEBUG] Replaced file path {path} with pre-loaded dataframe {name_without_ext}")
            except Exception as e:
                print(f"[DEBUG] Error while trying to replace file paths: {str(e)}")
        
        local_vars = {
            "pd": pd, 
            "np": np, 
            "plt": plt,
            "datetime": datetime,
            "timedelta": timedelta,
            "json": json,
            "os": os,
            **dataframes
        }
        
        try:
            # Add safeguards for executing code
            # - Don't allow imports
            # - Don't allow file operations except in read mode
            if re.search(r"^\s*import\s+", code, re.MULTILINE):
                return {"success": False, "error": "Direct imports are not allowed for security reasons"}
            
            if re.search(r"open\s*\(.+[^'r][\'\"]", code):
                return {"success": False, "error": "File writing operations are not allowed for security reasons"}
            
            # Execute the code
            exec_result = {}
            print("[DEBUG] Executing code:")
            print(code)
            
            exec(code, globals(), local_vars)
            
            # Try to find the result variable
            if 'result' in local_vars:
                exec_result = {"success": True, "result": local_vars['result']}
            else:
                # If no explicit result variable, try to find the most relevant DataFrame
                for var_name, var_value in local_vars.items():
                    # Skip original dataframes and built-in modules
                    if var_name in list(dataframes.keys()) + ["pd", "np", "plt", "datetime", "timedelta", "json", "os"]:
                        continue
                    
                    if isinstance(var_value, pd.DataFrame):
                        exec_result = {"success": True, "result": var_value}
                        break
                
                # If still no result found
                if not exec_result:
                    exec_result = {"success": True, "result": "Code executed successfully, but no result was produced"}
            
            return exec_result
                
        except Exception as e:
            print(f"[DEBUG] Error executing code: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def execute_multiple_code_blocks(self, code_blocks, dataframes):
        """Execute multiple code blocks and return results for each"""
        results = []
        
        for i, code in enumerate(code_blocks):
            print(f"[DEBUG] Executing code block {i+1} of {len(code_blocks)}")
            result = self.execute_pandas_code(code, dataframes)
            
            # Format the result
            if result.get("success"):
                formatted_result = self.format_output_for_display(result.get("result"))
            else:
                formatted_result = {
                    "type": "error",
                    "message": result.get("error", "Unknown error")
                }
            
            # Add to results array
            results.append({
                "code": code,
                "result": formatted_result
            })
        
        return results