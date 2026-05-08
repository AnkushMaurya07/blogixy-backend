from django.urls import path

from .views import (
    BlogAnalyticsView,
    BlogDetailView,
    BlogHomeFeedView,
    BlogListCreateView,
    BlogMediaUploadView,
    CommentListCreateView,
    LikeToggleView,
    ShareLinkCreateView,
    SharedBlogView,
)

urlpatterns = [
    path('feed/', BlogHomeFeedView.as_view(), name='blog-home-feed'),
    path('', BlogListCreateView.as_view(), name='blog-list-create'),
    path('analytics/', BlogAnalyticsView.as_view(), name='blog-analytics'),
    path('<slug:slug>/', BlogDetailView.as_view(), name='blog-detail'),
    path('<slug:slug>/comments/', CommentListCreateView.as_view(), name='blog-comments'),
    path('<slug:slug>/like-toggle/', LikeToggleView.as_view(), name='blog-like-toggle'),
    path('<slug:slug>/share/', ShareLinkCreateView.as_view(), name='blog-share'),
    path('<int:blog_id>/media/', BlogMediaUploadView.as_view(), name='blog-media'),
    path('shared/<str:token>/', SharedBlogView.as_view(), name='shared-blog'),
]
