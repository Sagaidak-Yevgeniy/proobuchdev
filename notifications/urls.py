from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Основные URL для уведомлений
    path('', views.notification_list, name='notification_list'),
    path('settings/', views.notification_settings, name='notification_settings'),
    
    # API для уведомлений
    path('count/', views.notification_count, name='notification_count'),
    path('list/', views.notification_list, name='notification_list_api'),
    
    # Действия над уведомлениями
    path('read/<int:notification_id>/', views.mark_notification_as_read, name='mark_as_read'),
    path('read-all/', views.mark_all_as_read, name='mark_all_as_read'),
    path('delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
]