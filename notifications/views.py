from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user).select_related('actor', 'target_blog')
        is_read = self.request.query_params.get('is_read')
        if is_read in {'true', 'false'}:
            queryset = queryset.filter(is_read=(is_read == 'true'))
        notif_type = self.request.query_params.get('type')
        if notif_type:
            queryset = queryset.filter(notification_type=notif_type)
        return queryset


class NotificationUpdateView(generics.UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkAllReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'updated': count})
