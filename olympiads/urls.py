from django.urls import path
from . import views

app_name = 'olympiads'

urlpatterns = [
    path('', views.olympiad_list, name='olympiad_list'),
    path('<int:olympiad_id>/', views.olympiad_detail, name='olympiad_detail'),
    path('<int:olympiad_id>/register/', views.olympiad_register, name='olympiad_register'),
    path('<int:olympiad_id>/tasks/', views.olympiad_tasks, name='olympiad_tasks'),
    path('<int:olympiad_id>/tasks/<int:task_id>/', views.olympiad_task_detail, name='olympiad_task_detail'),
    path('<int:olympiad_id>/tasks/<int:task_id>/submit/', views.olympiad_task_submit, name='olympiad_task_submit'),
    path('<int:olympiad_id>/results/', views.olympiad_results, name='olympiad_results'),
    path('<int:olympiad_id>/certificate/', views.olympiad_certificate, name='olympiad_certificate'),
    
    # Управление олимпиадами (для преподавателей и администраторов)
    path('manage/', views.olympiad_manage_list, name='olympiad_manage_list'),
    path('manage/create/', views.olympiad_create, name='olympiad_create'),
    path('manage/<int:olympiad_id>/edit/', views.olympiad_edit, name='olympiad_edit'),
    path('manage/<int:olympiad_id>/publish/', views.olympiad_publish, name='olympiad_publish'),
    path('manage/<int:olympiad_id>/tasks/create/', views.olympiad_task_create, name='olympiad_task_create'),
    path('manage/<int:olympiad_id>/tasks/<int:task_id>/edit/', views.olympiad_task_edit, name='olympiad_task_edit'),
    path('manage/<int:olympiad_id>/participants/', views.olympiad_participants, name='olympiad_participants'),
    path('manage/<int:olympiad_id>/invitations/', views.olympiad_invitations, name='olympiad_invitations'),
]