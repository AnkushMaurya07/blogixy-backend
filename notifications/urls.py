from django.urls import path

from .views import NotificationListView, NotificationMarkAllReadView, NotificationUpdateView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('<int:pk>/', NotificationUpdateView.as_view(), name='notification-update'),
]
