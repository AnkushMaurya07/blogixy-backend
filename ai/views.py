from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AiGenerationLog
from .serializers import AiGenerateRequestSerializer, AiGenerationLogSerializer
from .services import generate_blog_draft


class AiGenerateDraftView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AiGenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        result = generate_blog_draft(
            prompt=payload['prompt'],
            tone=payload.get('tone', ''),
            length=payload.get('length', 'medium'),
        )

        log = AiGenerationLog.objects.create(
            user=request.user,
            provider=result['provider'],
            model=result['model'],
            prompt=payload['prompt'],
            output=result['content'],
            status='success',
            latency_ms=result['latency_ms'],
        )
        return Response(
            {
                'title': result['title'],
                'content': result['content'],
                'provider': result['provider'],
                'model': result['model'],
                'generation_id': log.id,
            },
            status=status.HTTP_200_OK,
        )


class AiGenerationLogListView(generics.ListAPIView):
    serializer_class = AiGenerationLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AiGenerationLog.objects.filter(user=self.request.user)
