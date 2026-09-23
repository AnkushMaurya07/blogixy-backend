from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Message
from .models import BlogPost
from .pagination import BlogPageNumberPagination


class BlogPaginationTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alice', password='secretpass123')

    def test_shared_pagination_contract(self):
        paginator = BlogPageNumberPagination()
        self.assertEqual(paginator.page_size, 10)
        self.assertEqual(paginator.page_size_query_param, 'page_size')
        self.assertEqual(paginator.max_page_size, 50)

    def test_feed_endpoint_uses_consistent_paginated_response_shape(self):
        for i in range(3):
            BlogPost.objects.create(
                author=self.user,
                title=f'Post {i}',
                content='test content',
                is_published=True,
            )

        response = self.client.get(reverse('blog-home-feed'), {'page': 1, 'page_size': 2})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('results', payload)
        self.assertEqual(payload['count'], 3)
        self.assertEqual(payload['page'], 1)
        self.assertEqual(payload['page_size'], 2)
        self.assertTrue(payload['has_next'])
        self.assertEqual(len(payload['results']), 2)

    def test_blog_share_rolls_back_when_notification_creation_fails(self):
        receiver = get_user_model().objects.create_user(username='bob', password='secretpass123')
        blog = BlogPost.objects.create(
            author=self.user,
            title='Shared blog',
            content='test content',
            is_published=True,
        )

        token = str(RefreshToken.for_user(self.user).access_token)
        with patch('notifications.models.Notification.objects.create', side_effect=RuntimeError('boom')):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    reverse('blog-send-to-users', kwargs={'slug': blog.slug}),
                    {'receiver_ids': [receiver.id], 'content': 'Hello there'},
                    content_type='application/json',
                    HTTP_AUTHORIZATION=f'Bearer {token}',
                )

        self.assertEqual(Message.objects.filter(sender=self.user, receiver=receiver).count(), 0)
