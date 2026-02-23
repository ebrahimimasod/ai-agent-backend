from rest_framework import serializers
from .models import Post, IngestJob


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['wp_post_id', 'slug', 'url', 'title', 'modified_gmt', 'status', 'last_ingested_at']


class IngestJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestJob
        fields = ['celery_task_id', 'status', 'message', 'started_at', 'finished_at', 'created_at']


class ChatRequestSerializer(serializers.Serializer):
    question = serializers.CharField(min_length=3, max_length=4000)
