from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True)
    target_blog_slug = serializers.CharField(source='target_blog.slug', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'actor',
            'actor_name',
            'target_blog',
            'target_blog_slug',
            'target_message',
            'payload',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'actor_name', 'target_blog_slug']
