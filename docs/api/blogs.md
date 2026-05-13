# Blogs Module API

## Purpose
Blog CRUD, home feed, media uploads, share links, direct sharing to users via messages, likes, comments, search/explore, analytics.

## Endpoints
- `GET /api/blogs/feed/?page=1&page_size=10&section=all|following|discover` — Home feeds (paginated). **`all`** (default) = all published posts except yours; **`following`** = only people you follow; **`discover`** = excluding you and people you follow. Anonymous: full public stream (`section` ignored). Response: `{ results, count, page, page_size, has_next }`.
- `GET/POST /api/blogs/` — **List without `author`:** paginated envelope `results`, `count`, `page`, `page_size`, `has_next` with `?page=` & `?page_size=` (default 10); supports `search`, `sort=latest|ranking`. **`?drafts_only=true`** (authenticated): your unpublished drafts only, ordered by `updated_at` desc. **`?author=<id>`** still returns a **plain JSON array** of posts (profile). Create: authenticated.
- `GET/PATCH/DELETE /api/blogs/{slug}/` — Detail/update/delete. **`GET`** increments `view_count`; PATCH/DELETE do not.
- `POST /api/blogs/{slug}/send/` — Authenticated. Body: `{ "receiver_ids": [<int>, ...], "content": "<optional note>" }`. Creates `blog_share` messages + notifications for each receiver.
- `POST /api/blogs/{blog_id}/media/` — Multipart media upload (author only).
- `POST /api/blogs/{slug}/share/` — Create share token (author only). Response includes `public_url`.
- `GET /api/blogs/shared/{token}/` — Public read of shared blog.
- `GET/POST /api/blogs/{slug}/comments/` — List/create comments.
- `POST /api/blogs/{slug}/like-toggle/` — Authenticated toggle like; notifies author when appropriate.
- `GET /api/blogs/analytics/` — Authenticated author analytics: `total_posts`, `total_views`, `total_likes`, `total_comments`, `avg_views_per_post`, `most_viewed_post` (`slug`, `title`, `view_count` or `null`), `recent_activity` (up to 10 recent posts with `slug`, `title`, `view_count`, `like_count`, `comment_count`, `created_at`, `updated_at`, `is_published`).

## Request/Response notes
- Blog payloads follow `BlogPostSerializer` (author, slug, content, `is_published`, media, counts, timestamps).
- Listing uses the same serializer; ensure clients use detail route for full-length content in cards when needed.

## Error Handling
- Validation errors return standard DRF field errors.
- `403` on mutating another user’s blog; `401` when auth is required.
