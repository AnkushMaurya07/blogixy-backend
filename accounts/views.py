from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import Notification

from .models import Follow, FollowRequest, Message, MessageAuditLog
from .serializers import (
    FollowRequestSerializer,
    FollowSerializer,
    MessageAuditLogSerializer,
    MessageSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class UsernameAvailabilityView(APIView):
    """Return whether `username` is free. Authenticated callers exclude their own account."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        username = (request.query_params.get('username') or '').strip()
        if not username:
            return Response(
                {'available': False, 'detail': 'Username is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = User.objects.filter(username=username)
        user = getattr(request, 'user', None)
        if getattr(user, 'is_authenticated', False):
            queryset = queryset.exclude(pk=user.pk)
        return Response({'available': not queryset.exists()})


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        print(f'[ProfileView.get] user_id={request.user.pk} username={request.user.username!r}', flush=True)
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        # Multipart: drop zero-byte avatar parts (curl mistakes / aborted uploads) so text fields still save.
        data_keys = list(request.data.keys()) if hasattr(request.data, 'keys') else []
        ctype = getattr(request, 'content_type', None) or request.META.get('CONTENT_TYPE', '')
        print(
            f'[ProfileView.patch] user_id={request.user.pk} content_type={ctype!r} data_keys={data_keys}',
            flush=True,
        )
        data = request.data.copy() if hasattr(request.data, 'copy') else request.data
        av = data.get('avatar') if hasattr(data, 'get') else None
        if av is not None and getattr(av, 'size', None) == 0 and hasattr(data, 'pop'):
            print('[ProfileView.patch] dropping zero-byte avatar part', flush=True)
            data.pop('avatar', None)
        serializer = UserSerializer(request.user, data=data, partial=True)
        if not serializer.is_valid():
            print(f'[ProfileView.patch] validation_errors={dict(serializer.errors)}', flush=True)
            serializer.is_valid(raise_exception=True)
        serializer.save()
        print(f'[ProfileView.patch] saved ok user_id={request.user.pk}', flush=True)
        return Response(serializer.data)

    def post(self, request):
        """Same semantics as PATCH (partial update). Used from the SPA when CORS preflight omits PATCH."""
        return self.patch(request)


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.exclude(id=self.request.user.id)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(username__icontains=search)
        return queryset.order_by('username')


class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()


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
        follow = serializer.save(follower=self.request.user)
        Notification.objects.create(
            user=follow.following,
            actor=self.request.user,
            notification_type=Notification.NotificationType.FOLLOW,
            title='New follow',
            message=f'{self.request.user.username} started following you.',
            payload={'follower_id': self.request.user.id},
        )


class FollowToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id: int):
        if request.user.id == user_id:
            return Response({'detail': 'Cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        target = generics.get_object_or_404(User, id=user_id)
        existing = Follow.objects.filter(follower=request.user, following=target).first()
        if existing:
            existing.delete()
            return Response({'following': False})
        Follow.objects.create(follower=request.user, following=target)
        Notification.objects.create(
            user=target,
            actor=request.user,
            notification_type=Notification.NotificationType.FOLLOW,
            title='New follow',
            message=f'{request.user.username} started following you.',
            payload={'follower_id': request.user.id},
        )
        return Response({'following': True})


class FollowListView(generics.ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user).select_related('following', 'follower')


class FollowRequestCreateView(generics.CreateAPIView):
    serializer_class = FollowRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        follow_request = serializer.save(requester=self.request.user, status=FollowRequest.Status.PENDING)
        Notification.objects.create(
            user=follow_request.target,
            actor=self.request.user,
            notification_type=Notification.NotificationType.FOLLOW,
            title='Follow request',
            message=f'{self.request.user.username} requested to follow you.',
            payload={'request_id': follow_request.id},
        )


class FollowRequestRespondView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, request_id: int):
        action = request.data.get('action', '').lower()
        follow_request = generics.get_object_or_404(
            FollowRequest.objects.select_related('requester', 'target'),
            id=request_id,
            target=request.user,
        )
        if action == 'accept':
            follow_request.status = FollowRequest.Status.ACCEPTED
            follow_request.save(update_fields=['status', 'updated_at'])
            Follow.objects.get_or_create(
                follower=follow_request.requester,
                following=follow_request.target,
            )
        elif action == 'reject':
            follow_request.status = FollowRequest.Status.REJECTED
            follow_request.save(update_fields=['status', 'updated_at'])
        else:
            return Response({'detail': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': follow_request.status})


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
            text = last.content or ''
            preview = (text[:120] + '…') if len(text) > 120 else text
            results.append(
                {
                    'user_id': other.id,
                    'username': other.username,
                    'last_message_preview': preview,
                    'last_at': last.created_at,
                    'last_sender_id': last.sender_id,
                    'unread_count': Message.objects.filter(sender_id=pid, receiver=user, is_read=False).count(),
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
            queryset.filter(receiver=self.request.user, sender_id=with_user, is_read=False).update(is_read=True)
        return queryset

    def perform_create(self, serializer):
        msg = serializer.save(sender=self.request.user)
        Notification.objects.create(
            user=msg.receiver,
            actor=msg.sender,
            notification_type=Notification.NotificationType.MESSAGE,
            title='New message',
            message=f'{msg.sender.username} sent you a message.',
            target_message=msg,
            target_blog=msg.shared_blog,
            payload={'sender_id': msg.sender_id, 'message_type': msg.message_type},
        )


class MessageUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Message.objects.select_related('sender', 'receiver')

    def get_queryset(self):
        return self.queryset.filter(sender=self.request.user)

    def perform_update(self, serializer):
        message = self.get_object()
        MessageAuditLog.objects.create(
            message=message,
            actor=self.request.user,
            action=MessageAuditLog.ActionType.EDIT,
            previous_content=message.content,
        )
        serializer.save(edited_at=timezone.now())

    def perform_destroy(self, instance):
        MessageAuditLog.objects.create(
            message=instance,
            actor=self.request.user,
            action=MessageAuditLog.ActionType.DELETE,
            previous_content=instance.content,
        )
        instance.is_deleted = True
        instance.content = '[deleted]'
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['is_deleted', 'content', 'deleted_at'])


class MessageAuditLogListView(generics.ListAPIView):
    serializer_class = MessageAuditLogSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        message_id = self.request.query_params.get('message_id')
        qs = MessageAuditLog.objects.select_related('actor', 'message')
        if message_id:
            qs = qs.filter(message_id=message_id)
        return qs
