# Notifications Module API

## Purpose
User notification inbox with typed events, actor and target metadata, read state, and bulk mark-read.

## Endpoints
- `GET /api/notifications/` — List for current user. Query: `?is_read=true|false`, `?type=<notification_type>`.
- `POST /api/notifications/mark-all-read/` — Marks all unread notifications read for current user.
- `PATCH /api/notifications/<id>/` — Partial update (e.g. `{ "is_read": true }`).

## Payload fields (read-oriented)
- `notification_type`: `message`, `comment`, `like`, `follow`, `share`, `system`.
- `actor`, `actor_name` — Who triggered the event when applicable.
- `target_blog`, `target_blog_slug`, `target_message` — Related entities when set.
- `payload` — JSON envelope for extras (IDs, slugs, etc.).
- `title`, `message`, `is_read`, `created_at`.

## Error Handling
- `404` for notifications not owned by the user; standard auth errors elsewhere.
