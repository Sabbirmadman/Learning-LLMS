from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebsiteScrapeViewSet

router = DefaultRouter()
router.register(r'scrapes', WebsiteScrapeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]