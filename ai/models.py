from django.conf import settings
from django.db import models


class AiGenerationLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='ai_generations', on_delete=models.CASCADE)
    provider = models.CharField(max_length=50)
    model = models.CharField(max_length=80)
    prompt = models.TextField()
    output = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='success')
    error_message = models.TextField(blank=True)
    latency_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
