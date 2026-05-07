from django.contrib import admin
from .models import BlogMedia, BlogPost, Comment, ShareLink

admin.site.register(BlogPost)
admin.site.register(BlogMedia)
admin.site.register(ShareLink)
admin.site.register(Comment)
