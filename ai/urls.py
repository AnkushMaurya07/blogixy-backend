from django.urls import path

from .views import AiGenerationLogListView, AiGenerateDraftView

urlpatterns = [
    path('generate-draft/', AiGenerateDraftView.as_view(), name='ai-generate-draft'),
    path('history/', AiGenerationLogListView.as_view(), name='ai-generation-history'),
]
