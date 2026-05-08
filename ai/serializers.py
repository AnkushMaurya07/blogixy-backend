from rest_framework import serializers

from .models import AiGenerationLog


class AiGenerateRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=2000)
    tone = serializers.CharField(max_length=40, required=False, allow_blank=True)
    length = serializers.ChoiceField(choices=['short', 'medium', 'long'], required=False)


class AiGenerationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiGenerationLog
        fields = ['id', 'provider', 'model', 'prompt', 'output', 'status', 'error_message', 'latency_ms', 'created_at']
        read_only_fields = fields
