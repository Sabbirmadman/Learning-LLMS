import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import pandas as pd
import numpy as np
from collections import defaultdict


class EdaVectorDBHandler:
    """Handler for EDA vectorstore operations"""
    
    def __init__(self, persist_directory=None):
        """Initialize with a persistent directory for ChromaDB"""
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"}
        )
        
        # Set default persist directory if none provided
        if persist_directory is None:
            # Get the directory of the current file (eda_vectordb_handeller.py)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Set the persist directory to a 'chroma_db' subfolder
            persist_directory = os.path.join(current_dir, 'chroma_db')
        
        # Initialize ChromaDB
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        print(f"📁 Initializing ChromaDB at: {persist_directory}")
        
        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
    
    def json_serializable(self, obj):
        """Convert complex types to JSON serializable types"""
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
    


    def store_csv_in_vectordb(self, csv_metadata, force_reindex=False, user_id=None, scrape_id=None):
        """Store CSV metadata and descriptions in the vector database"""
        # First check if this CSV already exists in the database
        filename = csv_metadata['filename']
        
        # Include user_id and scrape_id in filter if provided
        filter_conditions = [
            {"filename": {"$eq": filename}},
            {"type": {"$eq": "csv_description"}}
        ]
        
        if user_id:
            filter_conditions.append({"user_id": {"$eq": user_id}})
        
        if scrape_id:
            filter_conditions.append({"scrape_id": {"$eq": scrape_id}})
        
        filter_dict = {"$and": filter_conditions}
        
        # Check if document exists
        collection = self.vectorstore._collection
        results = collection.get(
            where=filter_dict,
            include=["metadatas"]
        )
        
        if results['metadatas'] and len(results['metadatas']) > 0 and not force_reindex:
            print(f"⚠️ Document for '{filename}' already exists in vector database. Skipping.")
            return None
        
        # If document exists and we're force reindexing, delete the old documents first
        if results['metadatas'] and len(results['metadatas']) > 0 and force_reindex:
            ids_to_delete = collection.get(
                where=filter_dict,
                include=["ids"]
            )['ids']
            
            if ids_to_delete:
                self.vectorstore.delete(ids_to_delete)
                print(f"🗑️ Deleted existing documents for '{filename}' for reindexing")
        
        # Create a rich text representation for embedding
        content_for_embedding = f"""
        CSV Filename: {csv_metadata['filename']}
        Description: {csv_metadata['description']}
        
        This CSV has {csv_metadata['num_rows']} rows and {csv_metadata['num_columns']} columns.
        
        Columns:
        {', '.join([f"{col['name']} ({col['dtype']})" for col in csv_metadata['columns']])}
        
        Sample Data:
        {csv_metadata['sample_data'][:500]}  # Truncate if too long
        """
        
        # Create metadata dictionary with user and scrape IDs
        metadata_dict = {
            "filename": csv_metadata['filename'],
            "filepath": csv_metadata['filepath'],
            "type": "csv_description",
            "full_metadata": json.dumps(csv_metadata, default=self.json_serializable)
        }
        
        if user_id:
            metadata_dict["user_id"] = user_id
        
        if scrape_id:
            metadata_dict["scrape_id"] = scrape_id
        
        # Create Document object for CSV description
        csv_doc = Document(
            page_content=content_for_embedding,
            metadata=metadata_dict
        )
        
        # Only add the main CSV description document, not the column document
        self.vectorstore.add_documents([csv_doc])
        self.vectorstore.persist()
        
        print(f"✅ Stored {csv_metadata['filename']} in vector database")
        return csv_doc

    def retrieve_csv_descriptions(self, query, k=3, user_id=None, scrape_id=None):
        """Retrieve the k most relevant CSV descriptions based on a query"""
        try:
            # Search for relevant CSV descriptions
            filter_dict = {"type": {"$eq": "csv_description"}}
            
            # Add user_id and scrape_id to filter if provided
            if user_id:
                filter_dict = {"$and": [
                    filter_dict,
                    {"user_id": {"$eq": str(user_id)}}
                ]}
            
            # if scrape_id:
            #     filter_dict = {"$and": [
            #         filter_dict,
            #         {"scrape_id": {"$eq": str(scrape_id)}}
            #     ]}
            
            documents = self.vectorstore.similarity_search_with_score(
                query, 
                k=k,
                filter=filter_dict
            )
            
            # Format the results for visualization and use
            results = []
            for doc, score in documents:
                # Handle case where full_metadata might be missing
                try:
                    csv_metadata = json.loads(doc.metadata.get("full_metadata", "{}"))
                    
                    # If metadata is empty, extract what we can from the document itself
                    if not csv_metadata:
                        filename = doc.metadata.get("filename", "unknown_file")
                        filepath = doc.metadata.get("filepath", "unknown_path")
                        description = doc.page_content.split("Description:", 1)[1].split("\n", 1)[0].strip() if "Description:" in doc.page_content else "No description available"
                        
                        csv_metadata = {
                            "filename": filename,
                            "filepath": filepath,
                            "description": description
                        }
                except Exception as e:
                    print(f"Warning: Error parsing metadata for document: {str(e)}")
                    # Create minimal metadata from document
                    filename = doc.metadata.get("filename", "unknown_file")
                    filepath = doc.metadata.get("filepath", "unknown_path")
                    
                    csv_metadata = {
                        "filename": filename,
                        "filepath": filepath,
                        "description": "Metadata unavailable"
                    }
                
                results.append({
                    "filename": csv_metadata.get("filename", "unknown_file"),
                    "filepath": csv_metadata.get("filepath", "unknown_path"),
                    "description": csv_metadata.get("description", "No description available"),
                    "similarity_score": score,
                    "metadata": csv_metadata,
                    "user_id": doc.metadata.get("user_id"),
                    "scrape_id": doc.metadata.get("scrape_id")
                })
            
            # Log retrieval results
            print(f"📊 Retrieved {len(results)} relevant CSV files for query: '{query}'")
            for i, result in enumerate(results):
                print(f"  {i+1}. {result['filename']} (Score: {result['similarity_score']:.4f})")
                print(f"     Description: {result['description'][:100]}...")
                print(f"     Filepath: {result['filepath']}")
                
            return results
        
        except Exception as e:
            print(f"Error retrieving from vector database: {str(e)}")
            return []
    
    def retrieve_csv_by_filename(self, filename, user_id=None, scrape_id=None):
        """Retrieve a specific CSV description by filename"""
        try:
            # ChromaDB uses a different filtering format
            filter_conditions = [
                {"filename": {"$eq": filename}},
                {"type": {"$eq": "csv_description"}}
            ]
            
            if user_id:
                filter_conditions.append({"user_id": {"$eq": str(user_id)}})
            
            if scrape_id:
                filter_conditions.append({"scrape_id": {"$eq": str(scrape_id)}})
                
            filter_dict = {"$and": filter_conditions}
            
            # First check if the document exists
            collection = self.vectorstore._collection
            results = collection.get(
                where=filter_dict,
                include=["metadatas"]
            )
            
            if not results['metadatas'] or len(results['metadatas']) == 0:
                print(f"No metadata found for {filename} in vector database")
                return None
                
            # If we found metadata, proceed with similarity search
            documents = self.vectorstore.similarity_search("", k=1, filter=filter_dict)
            
            if documents:
                # Try to extract metadata from document
                try:
                    csv_metadata = json.loads(documents[0].metadata.get("full_metadata", "{}"))
                    if csv_metadata:
                        print(f"Found existing metadata for {filename} in vector database")
                        return csv_metadata
                        
                    # If we don't have full_metadata, reconstruct what we can
                    doc = documents[0]
                    page_content = doc.page_content
                    
                    # Extract details from content if possible
                    filename = doc.metadata.get("filename", filename)
                    filepath = doc.metadata.get("filepath", "")
                    user_id = doc.metadata.get("user_id")
                    scrape_id = doc.metadata.get("scrape_id")
                    
                    # Basic reconstruction of metadata
                    metadata = {
                        "filename": filename,
                        "filepath": filepath,
                        "description": "Metadata partially reconstructed from document"
                    }
                    
                    if user_id:
                        metadata["user_id"] = user_id
                    if scrape_id:
                        metadata["scrape_id"] = scrape_id
                        
                    return metadata
                    
                except Exception as e:
                    print(f"Error parsing metadata for {filename}: {str(e)}")
                    return None
        except Exception as e:
            print(f"Error retrieving {filename} from vector database: {str(e)}")
        
        return None
    
    def store_csv_relationships(self, potential_joins, user_id=None, scrape_id=None):
        """Store CSV relationship information in the vector database"""
        # Convert complex metadata to simple strings to avoid ChromaDB errors
        simplified_joins = {}
        for (file1, file2), joins in potential_joins.items():
            key = f"{file1}:{file2}"
            # Convert the list of column pairs to a simple string representation
            value = ",".join([f"{col1}:{col2}" for col1, col2 in joins])
            simplified_joins[key] = value
        
        # Create a textual summary of relationships
        relationships_summary = "CSV Relationship Summary:\n"
        for (file1, file2), join_keys in potential_joins.items():
            relationships_summary += f"\n{file1} can be joined with {file2} on:\n"
            for col1, col2 in join_keys:
                relationships_summary += f"  - {file1}.{col1} = {file2}.{col2}\n"
        
        # Create metadata dictionary
        metadata_dict = {
            "type": "csv_relationships",
            "join_data": json.dumps(simplified_joins)
        }
        
        # Add user_id and scrape_id if provided
        if user_id:
            metadata_dict["user_id"] = str(user_id)
        if scrape_id:
            metadata_dict["scrape_id"] = str(scrape_id)
        
        # Store in vectorstore as a document
        relationship_doc = Document(
            page_content=relationships_summary,
            metadata=metadata_dict
        )
        
        self.vectorstore.add_documents([relationship_doc])
        self.vectorstore.persist()
        print("✅ Stored CSV relationship information in vector database")
        return relationship_doc
    
    def retrieve_csv_relationships(self, user_id=None, scrape_id=None):
        """Retrieve CSV relationship information from the vector database"""
        try:
            # Build filter conditions
            filter_conditions = [
                {"type": {"$eq": "csv_relationships"}}
            ]
            
            if user_id:
                filter_conditions.append({"user_id": {"$eq": str(user_id)}})
            
            if scrape_id:
                filter_conditions.append({"scrape_id": {"$eq": str(scrape_id)}})
                
            filter_dict = {"$and": filter_conditions} if len(filter_conditions) > 1 else filter_conditions[0]
            
            # Search for relationship document
            documents = self.vectorstore.similarity_search(
                "csv relationships joins tables", 
                k=1, 
                filter=filter_dict
            )
            
            if not documents:
                return None, "No relationship information found in the database."
            
            # Get relationship info and parse from JSON string
            join_data_str = documents[0].metadata.get("join_data", "{}")
            simplified_joins = json.loads(join_data_str)
            
            # Convert back to the original format
            potential_joins = defaultdict(list)
            for key, value in simplified_joins.items():
                file1, file2 = key.split(":")
                col_pairs = value.split(",")
                for col_pair in col_pairs:
                    if ":" in col_pair:  # Ensure the string has the expected format
                        col1, col2 = col_pair.split(":")
                        potential_joins[(file1, file2)].append((col1, col2))
            
            return potential_joins, documents[0].page_content
        
        except Exception as e:
            print(f"Error retrieving relationship data: {str(e)}")
            return None, str(e)
            
    def delete_user_data(self, user_id):
        """Delete all documents for a specific user"""
        try:
            collection = self.vectorstore._collection
            
            # First, get all documents for this user
            # Use 'metadatas' instead of 'ids' in the include parameter
            user_filter = {"user_id": {"$eq": str(user_id)}}
            
            # Get the documents with their IDs
            user_docs = collection.get(
                where=user_filter,
                include=["metadatas"]  # Changed from "ids" to "metadatas"
            )
            
            # The IDs are still returned in the response regardless of the 'include' parameter
            ids_to_delete = user_docs["ids"]
            
            if ids_to_delete and len(ids_to_delete) > 0:
                # Delete the documents
                collection.delete(ids=ids_to_delete)
                deleted_count = len(ids_to_delete)
                print(f"✅ Deleted {deleted_count} documents for user_id: {user_id}")
                return deleted_count
            else:
                print(f"ℹ️ No documents found for user_id: {user_id}")
                return 0
                
        except Exception as e:
            print(f"❌ Error deleting user data: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise
            
    def delete_scrape_data(self, scrape_id):
        """Delete all documents for a specific scrape"""
        try:
            print(f"🗑️ Attempting to delete documents with scrape_id: {scrape_id}")
            
            # Get the ChromaDB collection
            collection = self.vectorstore._collection
            
            # Find all documents with this scrape_id
            results = collection.get(
                where={"scrape_id": {"$eq": str(scrape_id)}},
                include=["ids", "metadatas"]
            )
            
            if results['ids'] and len(results['ids']) > 0:
                # Delete the documents
                self.vectorstore.delete(results['ids'])
                print(f"✅ Successfully deleted {len(results['ids'])} documents with scrape_id: {scrape_id}")
                
                # Log what was deleted
                for i, metadata in enumerate(results['metadatas']):
                    file_type = metadata.get('type', 'unknown')
                    filename = metadata.get('filename', 'unknown')
                    print(f"  - Deleted {file_type} for {filename} (ID: {results['ids'][i]})")
                    
                return True
            else:
                print(f"⚠️ No documents found with scrape_id: {scrape_id}")
                return False
                    
        except Exception as e:
            print(f"❌ Error deleting documents with scrape_id {scrape_id}: {str(e)}")
            return False
    
    # Add this method or modify existing method:

    def store_csv_metadata(self, csv_metadata):
        """Store CSV metadata in the vector database"""
        filename = csv_metadata['filename']
        user_id = csv_metadata.get('user_id')
        scrape_id = csv_metadata.get('scrape_id')
        

        print(f"🔍 Storing metadata for {filename} in vector database")
        # Check if this CSV already exists in the database
        filter_conditions = [
            {"filename": {"$eq": filename}},
            {"type": {"$eq": "csv_description"}}
        ]
        
        if user_id:
            filter_conditions.append({"user_id": {"$eq": str(user_id)}})
        
        if scrape_id:
            filter_conditions.append({"scrape_id": {"$eq": str(scrape_id)}})
            
        filter_dict = {"$and": filter_conditions}
        
        # Check if document exists
        collection = self.vectorstore._collection
        results = collection.get(
            where=filter_dict,
            include=["metadatas", "documents"]  # Changed from "ids" to "documents"
        )
        
        # If document exists, delete it (forced reindexing)
        if results.get('ids') and len(results['ids']) > 0:
            self.vectorstore.delete(results['ids'])
            print(f"🔄 Removed existing metadata for {filename} to reindex")
        
        # Create a rich text representation for embedding
        content_for_embedding = f"""
        CSV Filename: {csv_metadata['filename']}
        Description: {csv_metadata.get('description', 'No description available')}
        
        This CSV has {csv_metadata['num_rows']} rows and {csv_metadata['num_columns']} columns.
        
        Columns:
        {', '.join([f"{col['name']} ({col['dtype']})" for col in csv_metadata['columns']])}
        
        Sample Data:
        {csv_metadata['sample_data'][:500]}  # Truncate if too long
        """
        
        # Create column-specific content for more targeted retrieval
        column_details = "\n".join([
            f"Column '{col['name']}' ({col['dtype']}) - Sample values: {col['sample_values']}"
            for col in csv_metadata['columns']
        ])
        
        # Create metadata dict
        metadata_dict = {
            "filename": csv_metadata['filename'],
            "filepath": csv_metadata['filepath'],
            "type": "csv_description",
            "full_metadata": json.dumps(csv_metadata, default=self.json_serializable)
        }
        
        # Add user_id and scrape_id if provided
        if user_id:
            metadata_dict["user_id"] = str(user_id)
        if scrape_id:
            metadata_dict["scrape_id"] = str(scrape_id)
        
        # Create Document objects, one for general CSV description
        csv_doc = Document(
            page_content=content_for_embedding,
            metadata=metadata_dict
        )
        
        # Create a document for column details (with same metadata)
        column_metadata = metadata_dict.copy()
        column_metadata["type"] = "csv_columns"  # Change the type
        column_doc = Document(
            page_content=column_details,
            metadata=column_metadata
        )
        
        # Add to ChromaDB
        self.vectorstore.add_documents([csv_doc, column_doc])
        self.vectorstore.persist()
        
        print(f"✅ Stored {csv_metadata['filename']} metadata in vector database")
        return [csv_doc, column_doc]