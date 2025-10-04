from django.urls import path
from . import views

urlpatterns = [
  path('health/', views.health),
  path('auth/login', views.auth_login),
  path('auth/register', views.auth_register),
  path('auth/anon', views.auth_anon),
  path('moods', views.moods_root),
  path('moods/summary', views.moods_summary),
  path('moods/add', views.moods_add),
  path('assessment/submit', views.assessment_submit),
  path('assessment/last', views.assessment_last),
  path('chat', views.chat),
  path('chat/history', views.chat_history),
]


