# Blogixy Backend (Django + DRF)

## Purpose
Backend APIs for Blogixy web app with:
- authentication and JWT-based session flow
- role-based profile setup at registration
- blog creation with media attachments (image/video)
- shareable blog links
- notification center APIs

## Tech Stack
- Django 5
- Django REST Framework
- Simple JWT
- SQLite (default)

## Module Documentation

### Accounts Module
- **Purpose:** user registration, login, role/profile management.
- **Components:** `User` model with `role`, `profile_title`, `bio`, `avatar`; `RegisterView`; `ProfileView`.
- **State Management:** DB-driven user and profile state.
- **APIs involved:**
  - `POST /api/auth/register/`
  - `POST /api/auth/login/`
  - `POST /api/auth/token/refresh/`
  - `GET/PATCH /api/auth/profile/`
- **User flow:** user selects role during register -> logs in -> updates profile.
- **Edge cases:** invalid role, weak password, missing credentials.

### Blogs Module
- **Purpose:** create and manage blog posts with media and sharing.
- **Components:** `BlogPost`, `BlogMedia`, `ShareLink`; list/create/detail APIs.
- **State Management:** DB-backed post/media/share entities.
- **APIs involved:**
  - `GET/POST /api/blogs/`
  - `GET/PATCH/DELETE /api/blogs/{slug}/`
  - `POST /api/blogs/{slug}/share/`
  - `POST /api/blogs/{blog_id}/media/`
  - `GET /api/blogs/shared/{token}/`
- **User flow:** author creates blog -> uploads image/video -> generates share link.
- **Edge cases:** unauthorized edits, invalid file uploads, invalid share token.

### Notifications Module
- **Purpose:** show user events (ex: blog published).
- **Components:** `Notification` model, list/update APIs.
- **State Management:** DB-backed user-specific notifications.
- **APIs involved:**
  - `GET /api/notifications/`
  - `PATCH /api/notifications/{id}/`
- **User flow:** notification created on publish -> user reads/marks notification.
- **Edge cases:** cross-user data access blocked by user filtering.

## API Contract (Core)

### Register
- **Endpoint:** `/api/auth/register/`
- **Method:** `POST`
- **Request payload:** `username`, `email`, `password`, `role`, `profile_title`, `bio`
- **Response structure:** created user fields (without password)
- **Error handling:** validation errors for missing/invalid fields

### Login
- **Endpoint:** `/api/auth/login/`
- **Method:** `POST`
- **Request payload:** `username`, `password`
- **Response structure:** `access`, `refresh`
- **Error handling:** 401 for invalid credentials

### Blog Create
- **Endpoint:** `/api/blogs/`
- **Method:** `POST`
- **Request payload:** `title`, `content`, `is_published`
- **Response structure:** blog object with slug and timestamps
- **Error handling:** 400 validation errors, 401 for unauthenticated

## Setup
1. `pip install django djangorestframework djangorestframework-simplejwt pillow django-cors-headers`
2. `python manage.py makemigrations`
3. `python manage.py migrate`
4. `python manage.py runserver`

## Change Tracking
- **What changed:** full backend architecture for auth/blogs/notifications plus social features.
- **Why changed:** to support requested complete blog platform workflows.
- **Impacted modules:** `accounts`, `blogs`, `notifications`, `config`.

## Additional APIs (Social + Discover)
- `GET /api/blogs/?search=<q>&sort=ranking|latest`
- `POST /api/blogs/{slug}/comments/`
- `GET /api/blogs/{slug}/comments/`
- `POST /api/blogs/{slug}/like-toggle/`
- `GET /api/blogs/analytics/`
- `GET /api/auth/users/?search=<q>`
- `GET /api/auth/follows/`
- `POST /api/auth/follows/create/`
- `GET /api/auth/messages/?with_user=<id>`
- `POST /api/auth/messages/`
