from django.urls import path
from . import views

urlpatterns = [
    path('health', views.health, name='health'),
    path('v1/ingest/run', views.run_ingest, name='run_ingest'),
    path('v1/ingest/jobs/<str:job_id>', views.job_status, name='job_status'),
    path('v1/posts', views.list_posts, name='list_posts'),
    path('v1/chat', views.chat, name='chat'),
]
