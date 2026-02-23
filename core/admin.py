from django.contrib import admin
from .models import Post, IngestJob


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['wp_post_id', 'title', 'status', 'modified_gmt', 'last_ingested_at']
    list_filter = ['status', 'last_ingested_at']
    search_fields = ['title', 'slug', 'wp_post_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(IngestJob)
class IngestJobAdmin(admin.ModelAdmin):
    list_display = ['celery_task_id', 'status', 'started_at', 'finished_at', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['celery_task_id']
    readonly_fields = ['created_at']
