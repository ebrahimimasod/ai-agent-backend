from django.db import models


class Post(models.Model):
    wp_post_id = models.IntegerField(unique=True, db_index=True)
    slug = models.CharField(max_length=255, null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    modified_gmt = models.CharField(max_length=64, null=True, blank=True)
    status = models.CharField(max_length=32, null=True, blank=True)
    last_ingested_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'posts'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Post {self.wp_post_id}: {self.title}"


class IngestJob(models.Model):
    celery_task_id = models.CharField(max_length=128, unique=True, db_index=True)
    status = models.CharField(max_length=32, default='queued')
    message = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ingest_jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Job {self.celery_task_id}: {self.status}"
