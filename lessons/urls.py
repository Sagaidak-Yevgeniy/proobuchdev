from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('create/<int:course_id>/', views.lesson_create, name='lesson_create'),
    path('<int:pk>/edit/', views.lesson_edit, name='lesson_edit'),
    path('<int:pk>/delete/', views.lesson_delete, name='lesson_delete'),
    path('<int:pk>/complete/', views.lesson_complete, name='lesson_complete'),
    path('content/<int:pk>/', views.lesson_content_detail, name='lesson_content_detail'),
    path('content/create/<int:lesson_id>/', views.lesson_content_create, name='lesson_content_create'),
    path('content/<int:pk>/edit/', views.lesson_content_edit, name='lesson_content_edit'),
    path('content/<int:pk>/delete/', views.lesson_content_delete, name='lesson_content_delete'),
]
