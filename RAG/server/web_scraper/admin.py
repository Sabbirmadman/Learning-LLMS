from django.contrib import admin
from .models import WebsiteScrape, ScrapedContent

@admin.register(WebsiteScrape)
class WebsiteScrapeAdmin(admin.ModelAdmin):
    list_display = ('url', 'status', 'user', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('url', 'user__email')

@admin.register(ScrapedContent)
class ScrapedContentAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'link', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('link', 'content')