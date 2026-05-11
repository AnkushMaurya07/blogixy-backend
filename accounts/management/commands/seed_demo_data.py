import random
from io import BytesIO
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from accounts.models import Follow, Message
from blogs.models import BlogMedia, BlogPost, Comment, MediaType
from notifications.models import Notification

User = get_user_model()

# Pexels CDN — animal / wildlife stock (same catalog as https://www.pexels.com/search/beautiful%20animal/ ).
# Landscape crop ~1200w; downloaded at seed time (no API key). See https://www.pexels.com/license/
_PEXELS_QS = '?auto=compress&cs=tinysrgb&fit=crop&h=627&w=1200'
PEXELS_ANIMAL_IMAGE_URLS = tuple(
    f'https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg{_PEXELS_QS}'
    for pid in (
        1108099,  # dogs
        2295744,  # fox
        3493730,  # kitten
        4588054,  # puppy
        1661179,  # elephant
        247502,   # hummingbird
        288621,   # zebra
        6895770,  # owl
        3844788,  # horse
        1586298,  # flamingo
        509404,   # squirrel
        1321524,  # deer
        56733,    # rabbits
        2132126,  # red panda
        5054770,  # duck
        4340344,  # swan
        730536,   # frog
    )
)


def pillow_jpeg_upload(filename: str) -> ContentFile:
    h = hash(filename) % (256 * 256 * 256)
    # Bias hues toward greens / blues when falling back offline.
    r, g, b = max((h >> 16) & 255, 40) // 4, ((h >> 8) & 255) % 180 + 60, ((h >> 16) ^ (h >> 8)) % 140 + 80
    img = Image.new('RGB', (900, 540), color=(r, g, b))
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=88)
    buf.seek(0)
    return ContentFile(buf.read(), name=filename)


def download_pexels_cover_jpeg(seed: str) -> ContentFile:
    url = PEXELS_ANIMAL_IMAGE_URLS[abs(hash(seed)) % len(PEXELS_ANIMAL_IMAGE_URLS)]
    req = Request(url, headers={'User-Agent': 'BlogixyDemoSeed/1.0'})
    try:
        with urlopen(req, timeout=45) as resp:
            data = resp.read()
        if len(data) < 2000:
            raise ValueError('too small')
        return ContentFile(data, name=f'pexels-{abs(hash(seed)) % 99999}.jpg')
    except (URLError, OSError, ValueError):
        return pillow_jpeg_upload(f'seed-cover-fallback-{uuid4().hex[:8]}.jpg')


def ensure_blog_cover_image(post: BlogPost) -> bool:
    if post.media_items.filter(media_type=MediaType.IMAGE).exists():
        return False
    BlogMedia.objects.create(
        blog=post,
        media_type=MediaType.IMAGE,
        file=download_pexels_cover_jpeg(f'cover-{post.id}'),
    )
    return True


def hydrate_feed_content(cmd: BaseCommand, min_posts_per_user: int = 3, rewrite_covers: bool = False) -> None:
    """Attach Pexels animal cover images (Pillow fallback offline). With rewrite_covers, replace existing image attachments."""

    if rewrite_covers:
        replaced = 0
        for post in BlogPost.objects.iterator():
            BlogMedia.objects.filter(blog=post, media_type=MediaType.IMAGE).delete()
            BlogMedia.objects.create(
                blog=post,
                media_type=MediaType.IMAGE,
                file=download_pexels_cover_jpeg(f'post-{post.id}'),
            )
            replaced += 1
        cmd.stdout.write(
            cmd.style.SUCCESS(
                f'Images: Pexels animal covers rewrote onto {replaced} posts (--rewrite-covers).'
            )
        )
    else:
        attached = 0
        for post in BlogPost.objects.filter(is_published=True).iterator():
            if ensure_blog_cover_image(post):
                attached += 1
        cmd.stdout.write(
            cmd.style.SUCCESS(
                f'Images: Pexels animal covers attached where missing on {attached} published posts.'
            )
        )

    created = 0
    for user in User.objects.filter(is_active=True).iterator():
        n = BlogPost.objects.filter(author=user, is_published=True).count()
        missing = max(0, min_posts_per_user - n)
        for _ in range(missing):
            post = BlogPost.objects.create(
                author=user,
                title=f'Moment {uuid4().hex[:8]} · @{user.username}',
                content=(
                    'Demo photo post for Blogixy — your home feed merges everyone’s public posts. '
                    'Like, bookmark, and open the full thread to comment.'
                ),
                is_published=True,
            )
            BlogMedia.objects.create(
                blog=post,
                media_type=MediaType.IMAGE,
                file=download_pexels_cover_jpeg(f'fill-{post.id}'),
            )
            created += 1
    cmd.stdout.write(
        cmd.style.SUCCESS(
            f'Posts: ensured at least {min_posts_per_user} published posts per user (created {created} new).'
        )
    )


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
        parser.add_argument(
            '--rewrite-covers',
            action='store_true',
            help='Replace every post image attachment with a downloaded nature photo (keeps video). Default only fills missing images.',
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

        hydrate_feed_content(self, min_posts_per_user=3, rewrite_covers=bool(options['rewrite_covers']))

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully.'))
