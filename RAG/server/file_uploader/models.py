from django.db import models
from django.conf import settings
import uuid
import os

def determine_upload_path(instance, filename):
    """
    Determine the upload path based on file type.
    
    For CSV files: uploads/csv/{instance.id}/{filename}
    For other files: uploads/{filename}
    """
    # For new instances, instance.id might not be set yet
    # Use a temporary UUID that will be used in post_save to move the file if needed
    instance_id = str(instance.id) if instance.id else str(uuid.uuid4())
    
    # Check if the file is a CSV based on content type or extension
    is_csv = False
    if hasattr(instance, 'content_type') and instance.content_type == 'text/csv':
        is_csv = True
    elif filename.lower().endswith('.csv'):
        is_csv = True
        
    if is_csv:
        return os.path.join('uploads', 'csv', instance_id, filename)
    return os.path.join('uploads', filename)

class UploadedFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to=determine_upload_path)
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    markdown_content = models.TextField(null=True, blank=True)
    file_size = models.BigIntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    vector_db_id = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(max_length=500, blank=True)

    class Meta:
        ordering = ['-upload_date']

    def __str__(self):
        return f"{self.filename} - {self.user.email}"

    def save(self, *args, **kwargs):
        # For new instances, save first to get an ID
        if not self.id:
            # Set a temporary ID
            temp_id = str(uuid.uuid4())
            self.id = temp_id
            super().save(*args, **kwargs)
            
            # If this is a CSV file and was saved with the temporary ID path,
            # we need to rename the directory to use the actual ID
            if self.content_type == 'text/csv':
                old_path = self.file.path
                # Generate the new path
                new_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'csv', str(self.id))
                os.makedirs(new_dir, exist_ok=True)
                new_path = os.path.join(new_dir, self.filename)
                
                # If old file exists, move it
                if os.path.exists(old_path):
                    import shutil
                    shutil.move(old_path, new_path)
                    
                    # Update the file field
                    relative_path = os.path.join('uploads', 'csv', str(self.id), self.filename)
                    self.file.name = relative_path
                    
                    # Save again to update the file path
                    super().save(update_fields=['file'])
        else:
            super().save(*args, **kwargs)