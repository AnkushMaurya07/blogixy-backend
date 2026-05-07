from rest_framework import serializers

from .models import BlogMedia, BlogPost, Comment, ShareLink


class BlogMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogMedia
        fields = ['id', 'media_type', 'file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class BlogPostSerializer(serializers.ModelSerializer):
    media_items = BlogMediaSerializer(many=True, read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True)
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    ranking_score = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            'id',
            'author',
            'author_name',
            'title',
            'slug',
            'content',
            'is_published',
            'media_items',
            'view_count',
            'likes_count',
            'comments_count',
            'ranking_score',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'author',
            'slug',
            'view_count',
            'likes_count',
            'comments_count',
            'ranking_score',
            'created_at',
            'updated_at',
        ]

    def get_ranking_score(self, obj):
        return (obj.likes.count() * 3) + (obj.comments.count() * 2) + obj.view_count


class ShareLinkSerializer(serializers.ModelSerializer):
    public_url = serializers.SerializerMethodField()

    class Meta:
        model = ShareLink
        fields = ['id', 'token', 'public_url', 'created_at']
        read_only_fields = ['id', 'token', 'public_url', 'created_at']

    def get_public_url(self, obj):
        request = self.context.get('request')
        if not request:
            return obj.token
        return request.build_absolute_uri(f'/api/blogs/shared/{obj.token}/')


class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'blog', 'user', 'user_name', 'content', 'created_at']
        read_only_fields = ['id', 'blog', 'user', 'user_name', 'created_at']
