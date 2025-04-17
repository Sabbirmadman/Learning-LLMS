from django.urls import path
from .views import CSVFolderProcessView, CSVQueryView, VectorDBContentsView, ResetUserDataView

urlpatterns = [
    path('process-csv/', CSVFolderProcessView.as_view(), name='process-csv'),
    path('query/', CSVQueryView.as_view(), name='csv-query'),
    path('vectordb-contents/', VectorDBContentsView.as_view(), name='vectordb-contents'),
    path('reset-user-data/', ResetUserDataView.as_view(), name='reset-user-data'),
]