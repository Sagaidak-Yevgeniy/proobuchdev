from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('settings/', views.notification_settings, name='notification_settings'),
    path('count/', views.notification_count, name='count'),
    path('read/<int:notification_id>/', views.mark_notification_read, name='mark_as_read'),
    path('read-all/', views.mark_all_read, name='mark_all_read'),
    path('delete/<int:notification_id>/', views.delete_notification, name='delete'),
    path('list/', views.notification_list, name='list'),
]