from django.conf import settings
from django.db import models


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        MESSAGE = 'message', 'Message'
        COMMENT = 'comment', 'Comment'
        LIKE = 'like', 'Like'
        FOLLOW = 'follow', 'Follow'
        SHARE = 'share', 'Share'
        SYSTEM = 'system', 'System'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='notifications',
        on_delete=models.CASCADE,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='triggered_notifications',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )
    title = models.CharField(max_length=120)
    message = models.TextField()
    target_blog = models.ForeignKey(
        'blogs.BlogPost',
        related_name='notifications',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    target_message = models.ForeignKey(
        'accounts.Message',
        related_name='notifications',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    payload = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user.username}: {self.title}'
