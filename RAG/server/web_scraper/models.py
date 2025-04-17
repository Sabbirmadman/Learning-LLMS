from django.db import models
from django.conf import settings
import uuid

class WebsiteScrape(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    url = models.URLField(max_length=2000)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

class ScrapedContent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scrape = models.ForeignKey(WebsiteScrape, on_delete=models.CASCADE, related_name='contents')
    content_type = models.CharField(max_length=20, choices=[
        ('TEXT', 'Text'),
        ('LINK', 'Link'),
        ('IMAGE', 'Image'),
        ('MARKDOWN', 'Markdown')
    ])
    metaData = models.TextField(default='No metadata available')
    link = models.URLField(max_length=2000, default='')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)