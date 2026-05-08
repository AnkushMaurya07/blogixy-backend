from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    READER = 'reader', 'Reader'
    AUTHOR = 'author', 'Author'
    BUSINESS = 'business', 'Business'


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.READER,
    )
    profile_title = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.username} ({self.role})'


class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.follower.username} -> {self.following.username}'


class Message(models.Model):
    class MessageType(models.TextChoices):
        TEXT = 'text', 'Text'
        BLOG_SHARE = 'blog_share', 'Blog Share'

    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, choices=MessageType.choices, default=MessageType.TEXT)
    content = models.TextField(blank=True)
    shared_blog = models.ForeignKey(
        'blogs.BlogPost',
        related_name='shared_in_messages',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_read = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.sender.username} to {self.receiver.username}'


class MessageAuditLog(models.Model):
    class ActionType(models.TextChoices):
        EDIT = 'edit', 'Edit'
        DELETE = 'delete', 'Delete'

    message = models.ForeignKey(Message, related_name='audit_logs', on_delete=models.CASCADE)
    actor = models.ForeignKey(User, related_name='message_audit_logs', on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ActionType.choices)
    previous_content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class FollowRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'

    requester = models.ForeignKey(User, related_name='sent_follow_requests', on_delete=models.CASCADE)
    target = models.ForeignKey(User, related_name='received_follow_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('requester', 'target')
        ordering = ['-created_at']
