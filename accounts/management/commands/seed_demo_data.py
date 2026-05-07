from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
import random

from accounts.models import Follow, Message
from blogs.models import BlogPost, Comment
from notifications.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo users, posts, comments, follows, messages, and notifications.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing demo data before seeding.',
        )
        parser.add_argument(
            '--extra-users',
            type=int,
            default=20,
            help='Number of additional users to seed.',
        )
        parser.add_argument(
            '--extra-posts',
            type=int,
            default=40,
            help='Number of additional posts to seed.',
        )

    def handle(self, *args, **options):
        if options['reset']:
            Comment.objects.all().delete()
            BlogPost.objects.all().delete()
            Follow.objects.all().delete()
            Message.objects.all().delete()
            Notification.objects.all().delete()
            User.objects.filter(username__in=['ankush', 'mira', 'devraj']).delete()
            self.stdout.write(self.style.WARNING('Existing demo records removed.'))

        users_data = [
            {
                'username': 'ankush',
                'email': 'ankush@example.com',
                'password': 'Ankush@123',
                'role': 'author',
                'profile_title': 'Tech Writer',
                'bio': 'Building Blogixy.',
            },
            {
                'username': 'mira',
                'email': 'mira@example.com',
                'password': 'Mira@1234',
                'role': 'business',
                'profile_title': 'Startup Founder',
                'bio': 'Sharing startup playbooks.',
            },
            {
                'username': 'devraj',
                'email': 'devraj@example.com',
                'password': 'Devraj@123',
                'role': 'reader',
                'profile_title': 'Learner',
                'bio': 'Reading daily.',
            },
        ]

        created_users = []
        for data in users_data:
            username = data['username']
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': data['email'],
                    'role': data['role'],
                    'profile_title': data['profile_title'],
                    'bio': data['bio'],
                },
            )
            if created:
                user.set_password(data['password'])
                user.save()
            created_users.append(user)
            status = 'created' if created else 'exists'
            self.stdout.write(f'User {username} ({status}) -> id={user.id}')

        ankush = User.objects.get(username='ankush')
        mira = User.objects.get(username='mira')
        devraj = User.objects.get(username='devraj')

        posts = [
            ('React in Production', 'How we structure scalable React modules.', ankush),
            ('Growth Metrics 101', 'A simple way to read weekly growth trends.', mira),
            ('Django DRF Tips', 'Fast patterns for API-first teams.', ankush),
        ]
        created_posts = []
        for title, content, author in posts:
            post, _ = BlogPost.objects.get_or_create(
                title=title,
                author=author,
                defaults={'content': content, 'is_published': True},
            )
            created_posts.append(post)
            self.stdout.write(f'Post "{post.title}" -> id={post.id}, slug={post.slug}')

        Follow.objects.get_or_create(follower=devraj, following=ankush)
        Follow.objects.get_or_create(follower=devraj, following=mira)
        self.stdout.write('Follow relationships created/verified.')

        Message.objects.get_or_create(
            sender=devraj,
            receiver=ankush,
            content='Hey, loved your DRF blog. Can you post a tutorial series?',
        )
        Message.objects.get_or_create(
            sender=ankush,
            receiver=devraj,
            content='Absolutely. I will publish one this week.',
        )
        self.stdout.write('Messages created/verified.')

        first_post = created_posts[0]
        second_post = created_posts[1]
        Comment.objects.get_or_create(
            blog=first_post,
            user=devraj,
            content='This post helped me understand architecture decisions.',
        )
        Comment.objects.get_or_create(
            blog=second_post,
            user=ankush,
            content='Great metrics framework. Thanks for sharing!',
        )

        for post in created_posts:
            post.likes.add(devraj)
            post.view_count = max(post.view_count, 15)
            post.save(update_fields=['view_count'])

        Notification.objects.get_or_create(
            user=ankush,
            title='Welcome to Blogixy',
            message='Your dashboard is ready. Start publishing.',
        )
        Notification.objects.get_or_create(
            user=mira,
            title='Post performance',
            message='Your latest post is trending in Explore.',
        )

        extra_users = []
        role_choices = ['reader', 'author', 'business']
        for index in range(1, options['extra_users'] + 1):
            username = f'user{index:02d}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'role': random.choice(role_choices),
                    'profile_title': f'Demo Profile {index}',
                    'bio': f'I am demo user {index}.',
                },
            )
            if created:
                user.set_password('DemoPass@123')
                user.save()
            extra_users.append(user)

        post_topics = [
            'AI Product Design',
            'Remote Team Ops',
            'Django Performance',
            'React Patterns',
            'Growth Analytics',
            'Creator Economy',
            'Startup Finance',
            'Content Strategy',
            'System Design',
            'Cloud Scaling',
        ]
        all_authors = [ankush, mira] + extra_users
        for index in range(1, options['extra_posts'] + 1):
            author = random.choice(all_authors)
            topic = random.choice(post_topics)
            title = f'{topic} #{index}'
            content = f'Detailed practical guide about {topic.lower()} for production teams.'
            post, _ = BlogPost.objects.get_or_create(
                title=title,
                author=author,
                defaults={'content': content, 'is_published': True},
            )

            post.view_count = random.randint(5, 300)
            post.save(update_fields=['view_count'])

            like_candidates = random.sample(all_authors + [devraj], k=min(random.randint(1, 8), len(all_authors) + 1))
            for user in like_candidates:
                post.likes.add(user)

            comment_candidates = random.sample(all_authors + [devraj], k=min(random.randint(1, 4), len(all_authors) + 1))
            for c_index, commenter in enumerate(comment_candidates, start=1):
                Comment.objects.get_or_create(
                    blog=post,
                    user=commenter,
                    content=f'Insightful point {c_index} on {topic.lower()}.',
                )

        for extra_user in extra_users[:10]:
            Follow.objects.get_or_create(follower=extra_user, following=ankush)
            Follow.objects.get_or_create(follower=extra_user, following=mira)
            Message.objects.get_or_create(
                sender=extra_user,
                receiver=ankush,
                content='Hi! I discovered your post in Explore.',
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Extra seeded: users={len(extra_users)}, posts={options["extra_posts"]}'
            )
        )

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully.'))
