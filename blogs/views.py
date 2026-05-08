from django.db.models import Count, F, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions, views
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from accounts.models import Follow
from notifications.models import Notification

from .models import BlogMedia, BlogPost, Comment, ShareLink
from .serializers import BlogMediaSerializer, BlogPostSerializer, CommentSerializer, ShareLinkSerializer


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author_id == request.user.id


class BlogHomeFeedView(views.APIView):
    """
    Home feed: posts from people you follow vs. published posts from everyone else you don't follow.

    Anonymous users receive only discovery (full public feed).
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        base_qs = (
            BlogPost.objects.filter(is_published=True)
            .select_related('author')
            .prefetch_related('likes', 'comments', 'media_items')
        )

        ctx = {'request': request}

        if not request.user.is_authenticated:
            discovery = base_qs.order_by('-created_at')[:48]
            return Response(
                {
                    'following_feed': [],
                    'discovery_feed': BlogPostSerializer(discovery, many=True, context=ctx).data,
                }
            )

        following_ids = set(
            Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        )
        following_feed = (
            base_qs.filter(author_id__in=following_ids).order_by('-created_at')[:48]
            if following_ids
            else BlogPost.objects.none()
        )
        discovery_feed = (
            base_qs.exclude(author_id__in=following_ids)
            .exclude(author=request.user)
            .order_by('-created_at')[:48]
        )

        return Response(
            {
                'following_feed': BlogPostSerializer(following_feed, many=True, context=ctx).data,
                'discovery_feed': BlogPostSerializer(discovery_feed, many=True, context=ctx).data,
            }
        )


class BlogListCreateView(generics.ListCreateAPIView):
    queryset = BlogPost.objects.select_related('author').all()
    serializer_class = BlogPostSerializer

    def get_queryset(self):
        queryset = BlogPost.objects.select_related('author').prefetch_related('likes', 'comments')
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
            title='Blog published',
            message=f'Your blog "{blog.title}" is now live.',
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
        serializer.save(blog=blog, user=self.request.user)


class LikeToggleView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        blog = generics.get_object_or_404(BlogPost, slug=slug)
        if blog.likes.filter(id=request.user.id).exists():
            blog.likes.remove(request.user)
            return Response({'liked': False})
        blog.likes.add(request.user)
        return Response({'liked': True})


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
