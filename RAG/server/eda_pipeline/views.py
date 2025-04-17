from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import os
import pandas as pd
from file_uploader.models import UploadedFile
from django.db.models import Q
import numpy as np
import json

from .services.eda_csv_service import EdaCsvService
from .services.eda_groq_service import EdaGroqService
from .eda_db.eda_vectordb_handeller import EdaVectorDBHandler


class CSVFolderProcessView(APIView):
    """
    API endpoint to process CSV files from UploadedFile records and extract metadata and relationships.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Get user and scrape info
            user_id = request.user.id
            scrape_ids = request.data.get('scrape_ids', [])
            force_reindex = request.data.get('force_reindex', False)
            
            if not scrape_ids:
                return Response({
                    'error': 'No scrape_ids provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize services
            csv_service = EdaCsvService()
            vectordb_handler = EdaVectorDBHandler()
            groq_service = EdaGroqService()
            
            results = []
            all_csv_paths = []
            all_csv_metadata = []
            
            print("\n🔍 Starting CSV processing for vector database")
            print(f"👤 User ID: {user_id}")
            print(f"📁 Scrape IDs: {scrape_ids}")
            print(f"🔄 Force reindex: {force_reindex}\n")
            
            # First, process each scrape_id individually to generate metadata
            for scrape_id in scrape_ids:
                print(f"\n==== Processing Scrape ID: {scrape_id} ====")
                # Find all CSV files for this scrape_id
                csv_files = UploadedFile.objects.filter(
                    id=scrape_id,
                    content_type='text/csv',
                    user=request.user
                )
                
                if not csv_files.exists():
                    print(f"❌ No CSV files found for scrape ID: {scrape_id}")
                    results.append({
                        'scrape_id': scrape_id,
                        'error': f'No CSV files found for ID: {scrape_id}'
                    })
                    continue
                
                # Get actual file paths
                csv_paths = [file.file.path for file in csv_files]
                all_csv_paths.extend(csv_paths)
                print(f"📊 Found {len(csv_paths)} CSV files for scrape ID {scrape_id}")
                
                # Process each CSV file
                processed_files = []
                for path in csv_paths:
                    filename = os.path.basename(path)
                    print(f"\n📄 Processing file: {filename}")
                    
                    # Generate metadata
                    csv_metadata, _ = csv_service.generate_csv_metadata(
                        path, user_id=user_id, scrape_id=scrape_id
                    )
                    
                    if csv_metadata:
                        # Generate description using LLM
                        print(f"🤖 Generating description for {filename}")
                        csv_metadata = groq_service.generate_csv_description(csv_metadata)
                        print(f"📝 Description: {csv_metadata.get('description', '')[:100]}...")
                        
                        # Store in vector database
                        print(f"💾 Storing in vector database: {filename}")
                        docs = vectordb_handler.store_csv_metadata(csv_metadata)
                        
                        # Print vector DB storage details
                        if docs:
                            print(f"✅ Successfully stored in vector DB:")
                            print(f"   - CSV Description Document (length: {len(docs[0].page_content)} chars)")
                            print(f"   - Column Details Document (length: {len(docs[1].page_content)} chars)")
                            
                            # Print some metadata details
                            print(f"   - Metadata fields: {list(csv_metadata.keys())}")
                            print(f"   - Number of columns: {csv_metadata.get('num_columns', 'unknown')}")
                            print(f"   - Number of rows: {csv_metadata.get('num_rows', 'unknown')}")
                        else:
                            print(f"⚠️ No documents returned from vector DB storage")
                        
                        processed_files.append(csv_metadata)
                        all_csv_metadata.append(csv_metadata)
                
                # Add results for this scrape_id
                results.append({
                    'scrape_id': scrape_id,
                    'success': True,
                    'message': f'Processed {len(processed_files)} CSV files',
                    'files': [result.get('filename') for result in processed_files if 'filename' in result]
                })
            
            # If we have multiple CSV files, detect relationships
            if len(all_csv_paths) > 1:
                print("\n🔗 Detecting relationships between CSV files...")
                # Detect relationships
                relationship_graph, potential_joins, _ = csv_service.detect_csv_relationships(all_csv_paths)
                
                # Store relationships if found
                if relationship_graph.edges:
                    print(f"🔍 Found {len(relationship_graph.edges)} relationships between files")
                    print(f"📊 Relationship details:")
                    for (file1, file2), joins in potential_joins.items():
                        print(f"   - {file1} ↔ {file2}: {len(joins)} join keys")
                        for col1, col2 in joins:
                            print(f"     • {col1} = {col2}")
                    
                    # Store in vector DB
                    print("💾 Storing relationships in vector database...")
                    vectordb_handler.store_csv_relationships(
                        potential_joins, user_id=user_id, scrape_id=scrape_ids[0]
                    )
                    print("✅ Relationships stored successfully")
                    
                    # Add relationship information to the response
                    relationship_info = {
                        'relationships_found': len(relationship_graph.edges),
                        'file_pairs': [f"{file1} ↔ {file2}" for file1, file2 in potential_joins.keys()]
                    }
                    
                    results.append({
                        'relationship_detection': relationship_info
                    })
                else:
                    print("⚠️ No relationships detected between CSV files")
            
            print(f"\n✅ Processing complete! Total files processed: {len(all_csv_metadata)}")
            return Response({
                'results': results,
                'total_files_processed': len(all_csv_metadata)
            })
            
        except Exception as e:
            print(f"❌ Error processing CSV files: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CSVQueryView(APIView):
    """
    API endpoint to query CSV data using natural language.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            import os
            import pandas as pd
            import traceback
            from django.conf import settings
            
            user_id = request.user.id
            query = request.data.get('query')
            
            if not query:
                return Response({
                    'error': 'No query provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # The GroqService creates its own vectordb_handler
            groq_service = EdaGroqService()
            
            # Pass user_id and scrape_id directly to the process_user_query method
            result = groq_service.process_user_query(
                query=query,
                user_id=user_id,
            )
            
            # Get available dataframes from uploaded files
            dataframes = {}
            
            # Get CSV files for the user
            csv_files = UploadedFile.objects.filter(
                user=request.user,
                content_type='text/csv'
            )
            
            # Load each CSV file
            for file in csv_files:
                try:
                    # Use the filename without extension as DataFrame name
                    filename = os.path.basename(file.filename)
                    df_name = os.path.splitext(filename)[0].lower().replace(' ', '_')
                    
                    # Read the CSV file
                    dataframes[df_name] = pd.read_csv(file.file.path)
                    print(f"Loaded DataFrame '{df_name}' from {file.file.path}")
                except Exception as e:
                    print(f"Error loading CSV {file.filename}: {str(e)}")
            
            # Check if we have code blocks to execute
            if 'code_blocks' in result and result['code_blocks']:
                # Execute all code blocks
                execution_results = groq_service.execute_multiple_code_blocks(result['code_blocks'], dataframes)
                result['executions'] = execution_results
                
                # For backward compatibility
                if execution_results:
                    result['code'] = execution_results[0]['code']
                    result['result'] = execution_results[0]['result']
            
            # If old format response with single 'code' field
            elif result.get('code') and isinstance(result.get('code'), str) and not isinstance(result.get('result'), dict):
                # Execute the single code block and add to results
                execution_result = groq_service.execute_pandas_code(result['code'], dataframes)
                
                # Update the result with the execution output
                if execution_result.get('success'):
                    formatted_result = groq_service.format_output_for_display(execution_result['result'])
                    result['result'] = formatted_result
                    
                    # Add to executions array for new format
                    # result['executions'] = [{
                    #     'code': result['code'],
                    #     'result': formatted_result
                    # }]
                else:
                    error_result = {
                        'type': 'error',
                        'message': execution_result.get('error', 'Unknown error during execution')
                    }
                    result['result'] = error_result
                    result['executions'] = [{
                        'code': result['code'],
                        'result': error_result
                    }]
                    
            return Response(result)
            
        except Exception as e:
            print(f"Unhandled error in CSVQueryView: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VectorDBContentsView(APIView):
    """
    API endpoint to retrieve user's contents from the vector database.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            import traceback
            
            user_id = request.user.id
            # Optional query parameters
            scrape_id = request.query_params.get('scrape_id')
            file_type = request.query_params.get('type')  # csv_description, csv_columns, csv_relationships
            filename = request.query_params.get('filename')
            
            # Initialize the vector database handler
            vectordb_handler = EdaVectorDBHandler()
            
            # Build filter conditions
            filter_conditions = []
            
            # Always filter by user_id for security
            user_filter = {"user_id": {"$eq": str(user_id)}}
            filter_conditions.append(user_filter)
            
            # Add optional filters if provided
            if scrape_id:
                filter_conditions.append({"scrape_id": {"$eq": str(scrape_id)}})
            
            if file_type:
                filter_conditions.append({"type": {"$eq": file_type}})
                
            if filename:
                filter_conditions.append({"filename": {"$eq": filename}})
            
            # Create final filter dictionary
            # If there's only one condition, use it directly instead of $and
            if len(filter_conditions) == 1:
                filter_dict = filter_conditions[0]
            else:
                filter_dict = {"$and": filter_conditions}
            
            print(f"🔍 Applying filter: {filter_dict}")
            
            # Access the underlying Chroma collection directly
            collection = vectordb_handler.vectorstore._collection
            
            # Get all documents with their metadata and content
            results = collection.get(
                where=filter_dict,
                include=["metadatas", "documents"]            
            )
            
            # Format the response
            formatted_results = []
            for i in range(len(results["ids"])):
                formatted_results.append({
                    "id": results["ids"][i],
                    "metadata": results["metadatas"][i],
                    "content": results["documents"][i]
                })
            
            return Response({
                "count": len(formatted_results),
                "results": formatted_results,
                "filters_applied": {
                    "user_id": user_id,
                    "scrape_id": scrape_id,
                    "type": file_type,
                    "filename": filename
                }
            })
            
        except Exception as e:
            print(f"❌ Error retrieving vector DB contents: {str(e)}")
            print(traceback.format_exc())
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ResetUserDataView(APIView):
    """
    API endpoint to reset/delete all of a user's data from the vector database.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user_id = request.user.id
            scrape_id = request.data.get('scrape_id', None)
            
            # Initialize the vector database handler
            vectordb_handler = EdaVectorDBHandler()
            
            if scrape_id:
                # If scrape_id is provided, only delete data for that scrape
                # We would need to implement this method
                # deleted_count = vectordb_handler.delete_scrape_data(scrape_id)
                # message = f"Successfully deleted {deleted_count} documents for scrape ID: {scrape_id}"
                return Response({
                    "error": "Deleting by scrape_id is not implemented yet"
                }, status=status.HTTP_501_NOT_IMPLEMENTED)
            else:
                # Delete all user data
                deleted_count = vectordb_handler.delete_user_data(user_id)
                message = f"Successfully deleted {deleted_count} documents for user ID: {user_id}"
            
            return Response({
                "success": True,
                "message": message,
                "deleted_count": deleted_count,
                "user_id": str(user_id),
                "scrape_id": scrape_id if scrape_id else None
            })
            
        except Exception as e:
            import traceback
            print(f"❌ Error resetting user data: {str(e)}")
            print(traceback.format_exc())
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)