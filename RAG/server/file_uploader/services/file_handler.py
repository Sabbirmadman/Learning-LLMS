from ..models import UploadedFile
from .content_extractor import ContentExtractor
from vectordb import vector_db
from eda_pipeline.services.eda_csv_service import EdaCsvService

class FileHandler:
    @staticmethod
    def handle_uploaded_file(file, content_type, user):
        try:
            file_size = file.size
            filename = file.name
            
            # Save file record to database with user
            uploaded_file = UploadedFile.objects.create(
                user=user,
                file=file,
                filename=filename,
                content_type=content_type,
                file_size=file_size
            )

            # Extract markdown content
            file_path = uploaded_file.file.path
            markdown_content = ContentExtractor.extract_content(file_path, content_type)
            
            if markdown_content:
                uploaded_file.markdown_content = markdown_content
                
                # Process for general vector database
                vector_db.process_markdown(
                    markdown_content=markdown_content,
                    url="",  # Empty URL for file uploads
                    scrape_id=str(uploaded_file.id),   # Using upload ID as scrape_id
                    user_id=user.id
                )
                
                # Special handling for CSV files - also process with EDA pipeline
                if content_type == 'text/csv':
                    try:
                        # Initialize the CSV service
                        eda_csv_service = EdaCsvService()
                        
                        # Generate metadata for the CSV file
                        csv_metadata, _ = eda_csv_service.generate_csv_metadata(
                            file_path, 
                            user_id=user.id,
                            scrape_id=str(uploaded_file.id), 
                        )
                        
                        if csv_metadata:
                            # Use the Groq service to generate a description
                            from eda_pipeline.services.eda_groq_service import EdaGroqService
                            groq_service = EdaGroqService()
                            csv_desc = groq_service.generate_csv_description(csv_metadata)
                            
                            # Store in the EDA vector database
                            from eda_pipeline.eda_db.eda_vectordb_handeller import EdaVectorDBHandler
                            vectordb_handler = EdaVectorDBHandler()
                            vectordb_handler.store_csv_in_vectordb(
                                csv_desc,
                                force_reindex=True,  # Force reindex to ensure it's stored
                                user_id=user.id,
                                scrape_id=str(uploaded_file.id)
                            )
                            print(f"✅ CSV file '{filename}' also processed with EDA pipeline")
                    except Exception as e:
                        print(f"⚠️ Error processing CSV in EDA pipeline: {str(e)}")
                
                uploaded_file.save()

            return uploaded_file
        except Exception as e:
            print(f"Error handling file upload: {str(e)}")
            raise