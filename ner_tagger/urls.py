from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='user_login'),
    path('upload/', views.upload_csv, name='upload_csv'),
    path('logout/', views.user_logout, name='user_logout'),
    path('view_uploaded_files/', views.view_uploaded_files, name='view_uploaded_files'),
    path('view_sentences/<int:file_id>/', views.view_sentences, name='view_sentences'),
    path('user-names/', views.user_names_action, name='user_names_action'),
    path('view-tags/', views.view_tags, name='view_tags'),
]