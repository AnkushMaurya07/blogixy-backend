from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import Notification

from .models import Follow, Message
from .serializers import (
    FollowSerializer,
    MessageSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.exclude(id=self.request.user.id)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(username__icontains=search)
        return queryset.order_by('username')


class SuggestedUsersView(generics.ListAPIView):
    """Users you do not yet follow — for 'People you may know' messaging sidebar."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        followed = Follow.objects.filter(follower=self.request.user).values_list('following_id', flat=True)
        limit = min(int(self.request.query_params.get('limit', '8')), 24)
        return (
            User.objects.exclude(id=self.request.user.id)
            .exclude(id__in=followed)
            .order_by('-date_joined')[:limit]
        )


class FollowCreateView(generics.CreateAPIView):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(follower=self.request.user)


class FollowListView(generics.ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user).select_related('following', 'follower')


class MessageConversationListView(APIView):
    """Partners with whom the current user has at least one message, with last-message preview."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        partner_ids = set(
            Message.objects.filter(sender=user).values_list('receiver_id', flat=True)
        ) | set(Message.objects.filter(receiver=user).values_list('sender_id', flat=True))

        User = get_user_model()
        results = []
        for pid in partner_ids:
            other = User.objects.filter(id=pid).first()
            if not other:
                continue
            last = (
                Message.objects.filter(
                    (Q(sender=user, receiver_id=pid) | Q(receiver=user, sender_id=pid))
                )
                .select_related('sender', 'receiver')
                .order_by('-created_at')
                .first()
            )
            if not last:
                continue
            results.append(
                {
                    'user_id': other.id,
                    'username': other.username,
                    'last_message_preview': (last.content[:120] + '…')
                    if len(last.content) > 120
                    else last.content,
                    'last_at': last.created_at,
                    'last_sender_id': last.sender_id,
                }
            )
        results.sort(key=lambda row: row['last_at'], reverse=True)
        return Response(results)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        with_user = self.request.query_params.get('with_user')
        queryset = Message.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        ).select_related('sender', 'receiver')
        if with_user:
            queryset = queryset.filter(Q(sender_id=with_user) | Q(receiver_id=with_user))
        return queryset

    def perform_create(self, serializer):
        msg = serializer.save(sender=self.request.user)
        Notification.objects.create(
            user=msg.receiver,
            title='New message',
            message=f'{msg.sender.username} sent you a message.',
        )
