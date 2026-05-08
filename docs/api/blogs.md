# Blogs Module API

## Purpose
Blog CRUD, home feed, media uploads, share links, direct sharing to users via messages, likes, comments, search/explore, analytics.

## Endpoints
- `GET /api/blogs/feed/` — Home feed: `following_feed` + `discovery_feed` when authenticated; anonymous users get discovery only.
- `GET/POST /api/blogs/` — List (search `?search=`, sort `?sort=latest|ranking`) and create. Anonymous list is published-only; authenticated users see published + their own drafts.
- `GET/PATCH/DELETE /api/blogs/{slug}/` — Detail/update/delete. `GET` increments `view_count`.
- `POST /api/blogs/{slug}/send/` — Authenticated. Body: `{ "receiver_ids": [<int>, ...], "content": "<optional note>" }`. Creates `blog_share` messages + notifications for each receiver.
- `POST /api/blogs/{blog_id}/media/` — Multipart media upload (author only).
- `POST /api/blogs/{slug}/share/` — Create share token (author only). Response includes `public_url`.
- `GET /api/blogs/shared/{token}/` — Public read of shared blog.
- `GET/POST /api/blogs/{slug}/comments/` — List/create comments.
- `POST /api/blogs/{slug}/like-toggle/` — Authenticated toggle like; notifies author when appropriate.
- `GET /api/blogs/analytics/` — Authenticated author aggregates (posts, views, likes).

## Request/Response notes
- Blog payloads follow `BlogPostSerializer` (author, slug, content, `is_published`, media, counts, timestamps).
- Listing uses the same serializer; ensure clients use detail route for full-length content in cards when needed.

## Error Handling
- Validation errors return standard DRF field errors.
- `403` on mutating another user’s blog; `401` when auth is required.
