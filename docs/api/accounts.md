# Accounts Module API

## Purpose
Authentication, profiles, user discovery, follows / follow-requests, and messaging (text + blog shares), including edit/delete audit trail for admins.

## Endpoints
- `POST /api/auth/register/`
- `POST /api/auth/login/` — JWT pair.
- `POST /api/auth/token/refresh/`
- `GET/PATCH /api/auth/profile/` — Current user profile.
- `GET /api/auth/users/` — List users (`?search=` optional). Exclude self.
- `GET /api/auth/users/<id>/` — User profile by id (authenticated).
- `GET /api/auth/users/suggestions/` — Suggested users not yet followed (`?limit=` capped).
- `GET /api/auth/follows/` — Follows where current user is follower.
- `POST /api/auth/follows/create/` — Body: `{ "following": <user_id> }`.
- `POST /api/auth/follows/<user_id>/toggle/` — Follow or unfollow target user.
- `POST /api/auth/follow-requests/` — Create pending request (body: `{ "target": <user_id> }` per serializer).
- `POST /api/auth/follow-requests/<request_id>/respond/` — Body: `{ "action": "accept" | "reject" }` (target user only).
- `GET /api/auth/messages/conversations/` — Conversation summaries + `unread_count` per partner.
- `GET/POST /api/auth/messages/` — List thread (`?with_user=<id>`); opening a thread marks inbound messages read. Create supports `message_type` (`text` | `blog_share`), `receiver`, `content`, optional `shared_blog`.
- `PATCH/DELETE /api/auth/messages/<id>/` — Sender-only update (soft-delete sets content to `[deleted]`, retains audit) or destructive path per view implementation.
- `GET /api/auth/messages/audit-logs/` — **Staff/admin only.** Query `?message_id=` optional.

## Request/Response
- Messages include `sender_name`, `receiver_name`, `message_type`, `shared_blog*`, read/edit/delete flags where applicable.

## Error Handling
- Standard DRF validation and permission responses; self-follow and invalid follow-request actions return `400`.
