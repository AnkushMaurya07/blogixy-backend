from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    FollowCreateView,
    FollowListView,
    MessageConversationListView,
    MessageListCreateView,
    ProfileView,
    RegisterView,
    SuggestedUsersView,
    UserListView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/suggestions/', SuggestedUsersView.as_view(), name='user-suggestions'),
    path('follows/', FollowListView.as_view(), name='follow-list'),
    path('follows/create/', FollowCreateView.as_view(), name='follow-create'),
    path('messages/conversations/', MessageConversationListView.as_view(), name='message-conversations'),
    path('messages/', MessageListCreateView.as_view(), name='message-list-create'),
]
