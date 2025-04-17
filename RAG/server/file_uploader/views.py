from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from .models import UploadedFile
from .serializers import FileUploadSerializer
from .services.file_handler import FileHandler
from vectordb import vector_db
import os
import shutil
from django.db import transaction

class FileUploadViewSet(viewsets.ModelViewSet):
    serializer_class = FileUploadSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UploadedFile.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('file')
        if not files:
            return Response(
                {'error': 'No files provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_files = []
        errors = []

        for file in files:
            try:
                content_type = file.content_type
                uploaded_file = FileHandler.handle_uploaded_file(
                    file=file, 
                    content_type=content_type,
                    user=request.user
                )
                uploaded_files.append(uploaded_file)
            except Exception as e:
                errors.append({"filename": file.name, "error": str(e)})
        
        if uploaded_files:
            serializer = self.get_serializer(uploaded_files, many=True)
            response_data = {
                "files": serializer.data
            }
            if errors:
                response_data["errors"] = errors
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': 'All files failed to upload', 'details': errors},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            file_id = str(instance.id)
            print(f"🔍 Attempting to delete file with ID: {file_id}")

            with transaction.atomic():
                # Delete from general vector database first
                if not vector_db.delete_by_id('scrape_id', file_id):
                    raise Exception("Failed to delete from general vector database")

                print(f"✅ File '{instance.filename}' deleted from general vector DB, content type: {instance.content_type}")
                
                # For CSV files, also delete from EDA vector database
                if instance.content_type == 'text/csv':
                    try:
                        from eda_pipeline.eda_db.eda_vectordb_handeller import EdaVectorDBHandler
                        vectordb_handler = EdaVectorDBHandler()
                        vectordb_handler.delete_scrape_data(file_id)
                        print(f"✅ CSV file '{instance.filename}' removed from EDA vector database")
                        
                        # Check both potential locations for CSV folders
                        # First check media/processed path
                        processed_folder_path = os.path.join('media', 'processed', file_id)
                        if os.path.exists(processed_folder_path):
                            shutil.rmtree(processed_folder_path)
                            print(f"✅ Processed folder for ID '{file_id}' removed: {processed_folder_path}")
                        
                        # Also check media/uploads/csv path based on folder structure
                        csv_folder_path = os.path.join('media', 'uploads', 'csv', file_id)
                        if os.path.exists(csv_folder_path):
                            shutil.rmtree(csv_folder_path)
                            print(f"✅ CSV folder for ID '{file_id}' removed: {csv_folder_path}")
                            
                    except Exception as e:
                        print(f"⚠️ Error cleaning up CSV data: {str(e)}")

                # Delete the actual file
                if instance.file:
                    file_path = instance.file.path
                    print(f"🔍 Checking file path: {file_path}")
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            print(f"✅ File '{file_path}' has been removed")
                        except OSError as e:
                            print(f"❌ Error removing file: {str(e)}")
                            raise Exception(f"Failed to delete file: {str(e)}")

                # Delete database record
                instance.delete()
                print(f"✅ Database record for '{instance.filename}' deleted")

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            print(f"❌ Error in destroy method: {str(e)}")
            return Response(
                {'error': f'Error deleting file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )