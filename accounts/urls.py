from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    FollowCreateView,
    FollowListView,
    FollowRequestCreateView,
    FollowRequestRespondView,
    FollowToggleView,
    MessageAuditLogListView,
    MessageConversationListView,
    MessageListCreateView,
    MessageUpdateDestroyView,
    ProfileView,
    RegisterView,
    SuggestedUsersView,
    UsernameAvailabilityView,
    UserDetailView,
    UserListView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('username-check/', UsernameAvailabilityView.as_view(), name='username-check'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/suggestions/', SuggestedUsersView.as_view(), name='user-suggestions'),
    path('follows/', FollowListView.as_view(), name='follow-list'),
    path('follows/create/', FollowCreateView.as_view(), name='follow-create'),
    path('follows/<int:user_id>/toggle/', FollowToggleView.as_view(), name='follow-toggle'),
    path('follow-requests/', FollowRequestCreateView.as_view(), name='follow-request-create'),
    path('follow-requests/<int:request_id>/respond/', FollowRequestRespondView.as_view(), name='follow-request-respond'),
    path('messages/conversations/', MessageConversationListView.as_view(), name='message-conversations'),
    path('messages/', MessageListCreateView.as_view(), name='message-list-create'),
    path('messages/<int:pk>/', MessageUpdateDestroyView.as_view(), name='message-update-delete'),
    path('messages/audit-logs/', MessageAuditLogListView.as_view(), name='message-audit-logs'),
]
