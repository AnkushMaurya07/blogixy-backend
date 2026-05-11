from django.conf import settings
from django.db import models
from django.utils.text import slugify
from uuid import uuid4


class BlogPost(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='blog_posts',
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    content = models.TextField()
    is_published = models.BooleanField(default=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_posts', blank=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f'{slugify(self.title)}-{str(uuid4())[:8]}'
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class MediaType(models.TextChoices):
    IMAGE = 'image', 'Image'
    VIDEO = 'video', 'Video'


class BlogMedia(models.Model):
    blog = models.ForeignKey(BlogPost, related_name='media_items', on_delete=models.CASCADE)
    media_type = models.CharField(max_length=20, choices=MediaType.choices)
    file = models.FileField(upload_to='blog_media/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'{self.blog.title} - {self.media_type}'


class ShareLink(models.Model):
    blog = models.ForeignKey(BlogPost, related_name='share_links', on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, default=uuid4, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'ShareLink({self.blog_id})'


class Favorite(models.Model):
    """User saved a post for later — list ordered by `created_at` (when saved)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blog_favorites', on_delete=models.CASCADE)
    blog = models.ForeignKey(BlogPost, related_name='favorited_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'blog'], name='unique_user_blog_favorite')]
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user_id} → {self.blog_id}'


class Comment(models.Model):
    blog = models.ForeignKey(BlogPost, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user.username} on {self.blog.title}'
