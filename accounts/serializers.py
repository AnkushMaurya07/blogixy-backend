from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Follow, FollowRequest, Message, MessageAuditLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'profile_title', 'bio', 'avatar', 'is_following']
        read_only_fields = ['id', 'is_following']

    def get_is_following(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or request.user.id == obj.id:
            return False
        return Follow.objects.filter(follower=request.user, following=obj).exists()

    def validate(self, attrs):
        f = attrs.get('avatar')
        if f is not None and hasattr(f, 'size') and f.size == 0:
            attrs.pop('avatar', None)
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'role',
            'profile_title',
            'bio',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class FollowSerializer(serializers.ModelSerializer):
    follower_name = serializers.CharField(source='follower.username', read_only=True)
    following_name = serializers.CharField(source='following.username', read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'follower_name', 'following', 'following_name', 'created_at']
        read_only_fields = ['id', 'follower', 'follower_name', 'following_name', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    receiver_name = serializers.CharField(source='receiver.username', read_only=True)
    shared_blog_slug = serializers.CharField(source='shared_blog.slug', read_only=True)
    shared_blog_title = serializers.CharField(source='shared_blog.title', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'sender_name',
            'receiver',
            'receiver_name',
            'message_type',
            'content',
            'shared_blog',
            'shared_blog_slug',
            'shared_blog_title',
            'is_read',
            'edited_at',
            'deleted_at',
            'is_deleted',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'sender',
            'sender_name',
            'receiver_name',
            'shared_blog_slug',
            'shared_blog_title',
            'is_read',
            'edited_at',
            'deleted_at',
            'is_deleted',
            'created_at',
        ]

    def validate(self, attrs):
        message_type = attrs.get('message_type')
        if message_type is None and self.instance:
            message_type = self.instance.message_type
        if message_type is None:
            message_type = Message.MessageType.TEXT
        shared_blog = attrs.get('shared_blog')
        content = attrs.get('content', '')
        if message_type == Message.MessageType.BLOG_SHARE and not shared_blog:
            raise serializers.ValidationError({'shared_blog': 'Blog share messages require a blog.'})
        if message_type == Message.MessageType.TEXT and not content.strip():
            raise serializers.ValidationError({'content': 'Text message cannot be empty.'})
        return attrs


class MessageAuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = MessageAuditLog
        fields = ['id', 'message', 'actor', 'actor_name', 'action', 'previous_content', 'created_at']
        read_only_fields = ['id', 'message', 'actor', 'actor_name', 'created_at']


class FollowRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.username', read_only=True)
    target_name = serializers.CharField(source='target.username', read_only=True)

    class Meta:
        model = FollowRequest
        fields = ['id', 'requester', 'requester_name', 'target', 'target_name', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'requester', 'requester_name', 'target_name', 'created_at', 'updated_at']
