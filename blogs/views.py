from django.contrib.auth import get_user_model
from django.db.models import Count, F, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions, views
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from accounts.models import Follow, Message
from notifications.models import Notification

from .models import BlogMedia, BlogPost, Comment, Favorite, ShareLink
from .serializers import (
    BlogMediaSerializer,
    BlogPostSerializer,
    CommentSerializer,
    FavoriteEntrySerializer,
    ShareLinkSerializer,
)


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author_id == request.user.id


class BlogHomeFeedView(views.APIView):
    """
    Home feeds (paginated):

    - `section=all` (default): everything public except your own posts (merged “for you” stream).
    - `section=following`: only authors you follow.
    - `section=discover`: published posts excluding you and excluding authors you follow.

    Anonymous: all published posts (section ignored).

    Paginated with `page` (default 1) and `page_size` (default 10, max 50).
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            page = int(request.query_params.get('page', 1))
        except (TypeError, ValueError):
            page = 1
        page = max(1, page)
        try:
            page_size = int(request.query_params.get('page_size', 10))
        except (TypeError, ValueError):
            page_size = 10
        page_size = min(50, max(1, page_size))

        base_qs = (
            BlogPost.objects.filter(is_published=True)
            .select_related('author')
            .prefetch_related('likes', 'comments', 'media_items')
        )

        ctx = {'request': request}

        section = request.query_params.get('section', 'all')
        if section not in ('all', 'following', 'discover'):
            section = 'all'

        if not request.user.is_authenticated:
            timeline_qs = base_qs.order_by('-created_at')
        elif section == 'all':
            timeline_qs = base_qs.exclude(author=request.user).order_by('-created_at')
        elif section == 'following':
            following_ids = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
            if not following_ids:
                timeline_qs = BlogPost.objects.none()
            else:
                timeline_qs = base_qs.filter(author_id__in=following_ids).order_by('-created_at')
        else:
            following_ids = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
            timeline_qs = base_qs.exclude(author=request.user)
            if following_ids:
                timeline_qs = timeline_qs.exclude(author_id__in=following_ids)
            timeline_qs = timeline_qs.order_by('-created_at')

        total = timeline_qs.count()
        offset = (page - 1) * page_size
        page_objs = list(timeline_qs[offset : offset + page_size])

        if request.user.is_authenticated:
            blog_ids_on_page = [b.id for b in page_objs]
            fav_id_set = set(
                Favorite.objects.filter(user=request.user, blog_id__in=blog_ids_on_page).values_list(
                    'blog_id', flat=True
                )
            )
            ctx_page = {**ctx, 'favorite_blog_ids': fav_id_set}
        else:
            ctx_page = ctx

        results = BlogPostSerializer(page_objs, many=True, context=ctx_page).data
        has_next = offset + len(page_objs) < total

        return Response(
            {
                'results': results,
                'count': total,
                'page': page,
                'page_size': page_size,
                'has_next': has_next,
            }
        )


class BlogListCreateView(generics.ListCreateAPIView):
    queryset = BlogPost.objects.select_related('author').all()
    serializer_class = BlogPostSerializer

    def get_queryset(self):
        queryset = BlogPost.objects.select_related('author').prefetch_related(
            'likes', 'comments', 'media_items'
        )
        user = self.request.user
        author_param = self.request.query_params.get('author')

        if author_param is not None:
            try:
                author_id = int(author_param)
            except (TypeError, ValueError):
                author_id = None
            if author_id is not None:
                queryset = queryset.filter(author_id=author_id)
                if not user.is_authenticated:
                    queryset = queryset.filter(is_published=True)
                elif not user.is_staff and getattr(user, 'id', None) != author_id:
                    queryset = queryset.filter(is_published=True)
        else:
            if not user.is_authenticated:
                queryset = queryset.filter(is_published=True)
            elif not user.is_staff:
                queryset = queryset.filter(Q(is_published=True) | Q(author=user))

        search = self.request.query_params.get('search')
        sort = self.request.query_params.get('sort', 'latest')
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(content__icontains=search))
        if sort == 'ranking':
            queryset = queryset.annotate(
                likes_count=Count('likes', distinct=True),
                comments_count=Count('comments', distinct=True),
            ).annotate(
                ranking_score=Coalesce(F('likes_count') * Value(3), 0, output_field=IntegerField())
                + Coalesce(F('comments_count') * Value(2), 0, output_field=IntegerField())
                + F('view_count')
            ).order_by('-ranking_score', '-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        return queryset

    def perform_create(self, serializer):
        blog = serializer.save(author=self.request.user)
        Notification.objects.create(
            user=self.request.user,
            actor=self.request.user,
            notification_type=Notification.NotificationType.SYSTEM,
            title='Blog published',
            message=f'Your blog "{blog.title}" is now live.',
            target_blog=blog,
            payload={'blog_id': blog.id},
        )

    def list(self, request, *args, **kwargs):
        """
        Global blog list (no `author` filter) returns a paginated envelope when using the explore
        endpoint pattern. Per-author profile lists (`?author=`) stay a plain JSON array for compatibility.
        """
        if request.query_params.get('author') is not None:
            return super().list(request, *args, **kwargs)

        queryset = self.filter_queryset(self.get_queryset())

        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = min(50, max(1, int(request.query_params.get('page_size', 10))))
        except (TypeError, ValueError):
            page_size = 10

        total = queryset.count()
        offset = (page - 1) * page_size
        page_objs = list(queryset[offset : offset + page_size])

        ctx = self.get_serializer_context()
        user = request.user
        if user.is_authenticated:
            ids = [b.id for b in page_objs]
            ctx = {
                **ctx,
                'favorite_blog_ids': set(
                    Favorite.objects.filter(user=user, blog_id__in=ids).values_list('blog_id', flat=True)
                ),
            }

        serializer = self.get_serializer(page_objs, many=True, context=ctx)
        has_next = offset + len(page_objs) < total

        return Response(
            {
                'results': serializer.data,
                'count': total,
                'page': page,
                'page_size': page_size,
                'has_next': has_next,
            }
        )


class BlogDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BlogPost.objects.select_related('author').all()
    serializer_class = BlogPostSerializer
    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = 'slug'

    def get_object(self):
        blog = super().get_object()
        blog.view_count += 1
        blog.save(update_fields=['view_count'])
        return blog


class BlogMediaUploadView(generics.CreateAPIView):
    serializer_class = BlogMediaSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        blog_id = self.kwargs.get('blog_id')
        blog = generics.get_object_or_404(BlogPost, id=blog_id, author=self.request.user)
        serializer.save(blog=blog)


class ShareLinkCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        blog = generics.get_object_or_404(BlogPost, slug=slug, author=request.user)
        share_link = ShareLink.objects.create(blog=blog, created_by=request.user)
        serializer = ShareLinkSerializer(share_link, context={'request': request})
        return Response(serializer.data)


class BlogSendToUsersView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        blog = generics.get_object_or_404(BlogPost, slug=slug)
        receiver_ids = request.data.get('receiver_ids') or []
        if not isinstance(receiver_ids, list) or not receiver_ids:
            return Response({'detail': 'receiver_ids must be a non-empty list.'}, status=400)
        users = get_user_model().objects.filter(id__in=receiver_ids).exclude(id=request.user.id)
        created = 0
        for receiver in users:
            msg = Message.objects.create(
                sender=request.user,
                receiver=receiver,
                message_type=Message.MessageType.BLOG_SHARE,
                content=request.data.get('content', ''),
                shared_blog=blog,
            )
            Notification.objects.create(
                user=receiver,
                actor=request.user,
                notification_type=Notification.NotificationType.SHARE,
                title='Blog shared with you',
                message=f'{request.user.username} shared "{blog.title}" with you.',
                target_blog=blog,
                target_message=msg,
                payload={'blog_slug': blog.slug},
            )
            created += 1
        return Response({'sent': created})


class SharedBlogView(generics.RetrieveAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        share = generics.get_object_or_404(ShareLink.objects.select_related('blog'), token=self.kwargs['token'])
        return share.blog


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        blog = generics.get_object_or_404(BlogPost, slug=self.kwargs['slug'])
        return Comment.objects.filter(blog=blog).select_related('user')

    def perform_create(self, serializer):
        blog = generics.get_object_or_404(BlogPost, slug=self.kwargs['slug'])
        comment = serializer.save(blog=blog, user=self.request.user)
        if blog.author_id != self.request.user.id:
            Notification.objects.create(
                user=blog.author,
                actor=self.request.user,
                notification_type=Notification.NotificationType.COMMENT,
                title='New comment',
                message=f'{self.request.user.username} commented on your blog.',
                target_blog=blog,
                payload={'comment_id': comment.id},
            )


class LikeToggleView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        blog = generics.get_object_or_404(BlogPost, slug=slug)
        if blog.likes.filter(id=request.user.id).exists():
            blog.likes.remove(request.user)
            return Response({'liked': False})
        blog.likes.add(request.user)
        if blog.author_id != request.user.id:
            Notification.objects.create(
                user=blog.author,
                actor=request.user,
                notification_type=Notification.NotificationType.LIKE,
                title='New like',
                message=f'{request.user.username} liked your blog.',
                target_blog=blog,
                payload={'blog_slug': blog.slug},
            )
        return Response({'liked': True})


class FavoriteToggleView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        blog = generics.get_object_or_404(BlogPost, slug=slug)
        existing = Favorite.objects.filter(user=request.user, blog=blog).first()
        if existing:
            existing.delete()
            return Response({'favorited': False})
        Favorite.objects.create(user=request.user, blog=blog)
        return Response({'favorited': True})


class FavoriteListView(generics.ListAPIView):
    """Current user's saved posts, newest save first (`created_at` on Favorite)."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FavoriteEntrySerializer

    def get_queryset(self):
        return (
            Favorite.objects.filter(user=self.request.user)
            .select_related('blog', 'blog__author')
            .prefetch_related('blog__likes', 'blog__comments', 'blog__media_items')
            .order_by('-created_at')
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['favorite_blog_ids'] = set(
            Favorite.objects.filter(user=self.request.user).values_list('blog_id', flat=True)
        )
        return ctx


class BlogAnalyticsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total_posts = BlogPost.objects.filter(author=request.user).count()
        total_views = (
            BlogPost.objects.filter(author=request.user).aggregate(total=Coalesce(Sum('view_count'), 0)).get('total')
        )
        total_likes = (
            BlogPost.objects.filter(author=request.user).annotate(like_count=Count('likes'))
            .aggregate(total=Coalesce(Sum('like_count'), 0))
            .get('total')
        )
        return Response(
            {
                'total_posts': total_posts,
                'total_views': total_views,
                'total_likes': total_likes,
            }
        )
