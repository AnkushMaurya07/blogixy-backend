from rest_framework import serializers

from .models import BlogMedia, BlogPost, Comment, Favorite, ShareLink


class BlogMediaSerializer(serializers.ModelSerializer):
    MAX_IMAGE_BYTES = 10 * 1024 * 1024
    MAX_VIDEO_BYTES = 20 * 1024 * 1024

    class Meta:
        model = BlogMedia
        fields = ['id', 'media_type', 'file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    def validate(self, attrs):
        file = attrs.get('file')
        media_type = attrs.get('media_type')
        if file is not None and media_type:
            limit = self.MAX_VIDEO_BYTES if media_type == 'video' else self.MAX_IMAGE_BYTES
            size = getattr(file, 'size', 0) or 0
            if size > limit:
                label = 'Video' if media_type == 'video' else 'Image'
                mb = limit // (1024 * 1024)
                raise serializers.ValidationError({'file': f'{label} uploads must be {mb}MB or smaller.'})
        return attrs


class BlogPostSerializer(serializers.ModelSerializer):
    media_items = BlogMediaSerializer(many=True, read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True)
    author_avatar = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    ranking_score = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            'id',
            'author',
            'author_name',
            'author_avatar',
            'is_favorited',
            'is_liked',
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

    def get_author_avatar(self, obj):
        field = getattr(obj.author, 'avatar', None)
        if not field:
            return None
        request = self.context.get('request')
        path = field.url
        if request and path and path.startswith('/'):
            return request.build_absolute_uri(path)
        return path

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        fav_ids = self.context.get('favorite_blog_ids')
        if fav_ids is not None:
            return obj.id in fav_ids
        return Favorite.objects.filter(user=request.user, blog=obj).exists()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        uid = request.user.id
        cache = getattr(obj, '_prefetched_objects_cache', None)
        if cache is not None and 'likes' in cache:
            return any(like.id == uid for like in obj.likes.all())
        return obj.likes.filter(pk=uid).exists()

    def get_ranking_score(self, obj):
        return (obj.likes.count() * 3) + (obj.comments.count() * 2) + obj.view_count


class FavoriteEntrySerializer(serializers.ModelSerializer):
    blog = BlogPostSerializer(read_only=True)
    favorited_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Favorite
        fields = ['favorited_at', 'blog']


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
