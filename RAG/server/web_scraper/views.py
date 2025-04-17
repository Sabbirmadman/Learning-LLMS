from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import WebsiteScrape, ScrapedContent
from .serializers import WebsiteScrapeSerializer, ScrapedContentSerializer
from .services.scraper import scrape_website
from vectordb.vectorDbHandeller import VectorDBHandler
from vectordb import vector_db
import threading

class WebsiteScrapeViewSet(viewsets.ModelViewSet):
    queryset = WebsiteScrape.objects.all()
    serializer_class = WebsiteScrapeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
        # Start scraping in a background thread
        thread = threading.Thread(
            target=scrape_website,
            args=(serializer.instance.id,)
        )
        thread.daemon = True
        thread.start()

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            # Delete from vector database first - use the pre-initialized singleton
            vector_db.delete_by_id('scrape_id', str(instance.id))
            
            # Delete all related ScrapedContent
            ScrapedContent.objects.filter(scrape=instance).delete()
            
            # Delete the scrape record
            instance.delete()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
                
        except Exception as e:
            return Response(
                {'error': f'Error deleting scrape: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def contents(self, request, pk=None):
        scrape = get_object_or_404(WebsiteScrape, pk=pk, user=request.user)
        contents = ScrapedContent.objects.filter(scrape=scrape)
        serializer = ScrapedContentSerializer(contents, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        scrape = get_object_or_404(WebsiteScrape, pk=pk, user=request.user)
        if scrape.status in ['COMPLETED', 'FAILED']:
            scrape.status = 'PENDING'
            scrape.save()
            
            # Start scraping in a background thread
            thread = threading.Thread(
                target=scrape_website,
                args=(scrape.id,)
            )
            thread.daemon = True
            thread.start()
            
            return Response({'status': 'Scrape retried'}, status=status.HTTP_200_OK)
        return Response({'status': 'Scrape is already in progress'}, status=status.HTTP_400_BAD_REQUEST)