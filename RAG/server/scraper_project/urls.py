from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('web_scraper.urls')),
    path('api/users/', include('users.urls')),
    path('api-chat/', include('chatLlm.urls')),
    path('api/files/', include('file_uploader.urls')),
    path('api/eda/', include('eda_pipeline.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)