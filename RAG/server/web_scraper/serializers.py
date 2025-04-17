from rest_framework import serializers
from .models import WebsiteScrape, ScrapedContent

class ScrapedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapedContent
        fields = ['id', 'content_type', 'metaData', 'link', 'content', 'created_at']

class WebsiteScrapeSerializer(serializers.ModelSerializer):
    contents = ScrapedContentSerializer(many=True, read_only=True)

    class Meta:
        model = WebsiteScrape
        fields = ['id', 'url', 'status', 'created_at', 'updated_at', 'contents']
        read_only_fields = ['status', 'created_at', 'updated_at']
