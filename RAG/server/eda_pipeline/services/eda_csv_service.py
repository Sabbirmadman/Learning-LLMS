import os
import pandas as pd
import numpy as np
import networkx as nx
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple
from django.conf import settings


class EdaCsvService:
    """Service for handling CSV metadata generation and relationship detection"""
    
    def __init__(self):
        """Initialize the CSV service"""
        pass
    
    def json_serializable(self, obj):
        """Convert numpy types to Python standard types for JSON serialization"""
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
    
    def generate_csv_metadata(self, csv_path, metadata_id=None, user_id=None, scrape_id=None):
        """Extract metadata from a CSV file"""
        filename = os.path.basename(csv_path)
        
        # Read the CSV file with error handling
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"Error reading CSV {csv_path}: {str(e)}")
            return None, None
        
        # Get basic metadata
        num_rows, num_columns = df.shape
        
        # Get column descriptions
        columns = []
        for col_name in df.columns:
            col_type = str(df[col_name].dtype)
            try:
                sample_values = df[col_name].dropna().head(5).tolist()
                sample_values = [self.json_serializable(val) for val in sample_values]
            except:
                sample_values = ["[Error getting samples]"]
                
            # Add additional column metadata
            col_info = {
                "name": col_name,
                "dtype": col_type,
                "sample_values": sample_values,
                "unique_values": len(df[col_name].unique()) if len(df[col_name].dropna()) > 0 else 0
            }
            
            # Add numeric stats if appropriate
            if pd.api.types.is_numeric_dtype(df[col_name]):
                try:
                    col_info.update({
                        "min": self.json_serializable(df[col_name].min()),
                        "max": self.json_serializable(df[col_name].max()),
                    })
                except:
                    pass  # Skip if stats calculation fails
                    
            columns.append(col_info)
        
        # Get sample data for visualization
        sample_data = df.head(2).to_string()
        
        # Create the initial metadata dictionary
        csv_metadata = {
            "filename": filename,
            "filepath": csv_path,  # Store the actual file path
            "num_rows": num_rows,
            "num_columns": num_columns,
            "columns": columns,
            "sample_data": sample_data,
        }
        
        # Add metadata_id and user_id if provided
        if metadata_id:
            csv_metadata["metadata_id"] = metadata_id
        if user_id:
            csv_metadata["user_id"] = user_id
        if scrape_id:
            csv_metadata["scrape_id"] = scrape_id

        print(f"✅ Extracted metadata for {filename} (user_id: {user_id}, scrape_id: {scrape_id})")
        return csv_metadata, df
        
    def process_csv_file(self, csv_path, user_id=None, scrape_id=None):
        """Process a single CSV file and store its metadata"""
        from eda_pipeline.eda_db.eda_vectordb_handeller import EdaVectorDBHandler
        from eda_pipeline.services.eda_groq_service import EdaGroqService
        
        # Initialize handlers
        vectordb_handler = EdaVectorDBHandler()
        groq_service = EdaGroqService()
        
        # Generate metadata
        csv_metadata, _ = self.generate_csv_metadata(
            csv_path, user_id=user_id, scrape_id=scrape_id
        )
        
        if not csv_metadata:
            return None
            
        # Generate description using LLM
        csv_metadata = groq_service.generate_csv_description(csv_metadata)
        
        # Store in vector database
        vectordb_handler.store_csv_metadata(csv_metadata)
        
        return csv_metadata
    
    
    def detect_csv_relationships(self, csv_paths):
        """Detect potential relationships between CSV files"""
        # Store dataframes and their column information
        dataframes = {}
        column_info = {}
        
        # Load all CSVs
        for path in csv_paths:
            try:
                filename = os.path.basename(path)
                df = pd.read_csv(path)
                dataframes[filename] = df
                
                # Store column information
                column_info[filename] = {
                    'cols': df.columns.tolist(),
                    'dtypes': {col: str(df[col].dtype) for col in df.columns}
                }
                
            except Exception as e:
                print(f"Error reading CSV {path}: {str(e)}")
                continue
        
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
                if file1 >= file2:  # Skip self-comparisons and duplicates
                    continue
                    
                # First look for columns with the same name
                common_cols = set(column_info[file1]['cols']).intersection(set(column_info[file2]['cols']))
                
                joins = []
                # Check for columns with same name and compatible types
                for col in common_cols:
                    type1 = column_info[file1]['dtypes'][col]
                    type2 = column_info[file2]['dtypes'][col]
                    
                    # Check if types are compatible (exact match or string-like types)
                    if (type1 == type2 or 
                        ('object' in type1 and 'object' in type2) or
                        ('str' in type1 and 'str' in type2)):
                        
                        # Check for value overlap
                        set1 = set(dataframes[file1][col].dropna().astype(str).tolist())
                        set2 = set(dataframes[file2][col].dropna().astype(str).tolist())
                        
                        if len(set1.intersection(set2)) > 0:
                            joins.append((col, col))
                
                # Now look for columns with different names but similar content
                # This is the key addition to detect relationships between differently named columns
                if not joins:  # Only if we didn't find matching column names
                    df1_cols = dataframes[file1].columns
                    df2_cols = dataframes[file2].columns
                    
                    # Check each column in the first file against each in the second
                    for col1 in df1_cols:
                        for col2 in df2_cols:
                            # Skip if column names are the same (already checked above)
                            if col1 == col2:
                                continue
                            
                            # Check if either column name contains the other
                            # Or check for common substrings like "id", "customer", etc.
                            name_similarity = (col1.lower() in col2.lower() or 
                                            col2.lower() in col1.lower() or
                                            ("id" in col1.lower() and "id" in col2.lower()) or
                                            ("customer" in col1.lower() and "id" in col2.lower()))
                            
                            if not name_similarity:
                                continue
                                
                            # Check data types for compatibility
                            type1 = column_info[file1]['dtypes'][col1]
                            type2 = column_info[file2]['dtypes'][col2]
                            
                            type_compatibility = (type1 == type2 or 
                                                ('object' in type1 and 'object' in type2) or
                                                ('str' in type1 and 'str' in type2))
                            
                            if not type_compatibility:
                                continue
                            
                            # Check for value overlap
                            set1 = set(dataframes[file1][col1].dropna().astype(str).tolist())
                            set2 = set(dataframes[file2][col2].dropna().astype(str).tolist())
                            
                            intersection = set1.intersection(set2)
                            if len(intersection) > 0:
                                print(f"Found relationship between {file1}.{col1} and {file2}.{col2} with {len(intersection)} matching values")
                                joins.append((col1, col2))
                
                # Add edge if we found potential join keys
                if joins:
                    relationship_graph.add_edge(file1, file2)
                    potential_joins[(file1, file2)] = joins
        
        return relationship_graph, potential_joins, dataframes
    
    def process_csv_files(self, csv_paths, user_id=None, scrape_id=None):
        """Process multiple CSV files and detect relationships"""
        # Process each file
        processed_files = []
        for path in csv_paths:
            csv_metadata = self.process_csv_file(path, user_id=user_id, scrape_id=scrape_id)
            if csv_metadata:
                processed_files.append(csv_metadata)
        
        # If we have multiple files, detect relationships
        if len(processed_files) > 1:
            relationship_graph, potential_joins, _ = self.detect_csv_relationships(csv_paths)
            
            if relationship_graph.edges:
                # Store relationship information
                from eda_pipeline.eda_db.eda_vectordb_handeller import EdaVectorDBHandler
                vectordb_handler = EdaVectorDBHandler()
                vectordb_handler.store_csv_relationships(
                    potential_joins, user_id=user_id, scrape_id=scrape_id
                )
                
        return processed_files