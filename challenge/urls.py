from django.urls import path
from api.views import CSVUploadView

urlpatterns = [
    path('process-csv/', CSVUploadView.as_view(), name='csv-upload'),
]
