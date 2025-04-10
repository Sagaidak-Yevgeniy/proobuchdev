from django.urls import path
from . import views

app_name = 'olympiads'

urlpatterns = [
    # Общедоступные маршруты
    path('', views.olympiad_list, name='olympiad_list'),
    path('<int:olympiad_id>/', views.olympiad_detail, name='olympiad_detail'),
    path('<int:olympiad_id>/register/', views.olympiad_register, name='olympiad_register'),
    
    # Маршруты для участников олимпиад
    path('<int:olympiad_id>/tasks/', views.olympiad_tasks, name='olympiad_tasks'),
    path('<int:olympiad_id>/tasks/<int:task_id>/', views.olympiad_task_detail, name='olympiad_task_detail'),
    path('<int:olympiad_id>/tasks/<int:task_id>/submit/', views.olympiad_task_submit, name='olympiad_task_submit'),
    path('<int:olympiad_id>/finish/', views.olympiad_finish, name='olympiad_finish'),
    path('<int:olympiad_id>/results/', views.olympiad_results, name='olympiad_results'),
    path('<int:olympiad_id>/certificate/', views.olympiad_certificate, name='olympiad_certificate'),
    path('<int:olympiad_id>/leaderboard/', views.olympiad_leaderboard, name='olympiad_leaderboard'),
    
    # API для обновления прогресса
    path('<int:olympiad_id>/update_progress/', views.olympiad_update_progress, name='olympiad_update_progress'),
    
    # Управление олимпиадами (для преподавателей и администраторов)
    path('manage/', views.olympiad_manage_list, name='olympiad_manage_list'),
    path('manage/create/', views.olympiad_create, name='olympiad_create'),
    path('manage/<int:olympiad_id>/edit/', views.olympiad_edit, name='olympiad_edit'),
    path('manage/<int:olympiad_id>/publish/', views.olympiad_publish, name='olympiad_publish'),
    path('manage/<int:olympiad_id>/complete/', views.olympiad_complete, name='olympiad_complete'),
    path('manage/<int:olympiad_id>/archive/', views.olympiad_archive, name='olympiad_archive'),
    path('manage/<int:olympiad_id>/tasks/create/', views.olympiad_task_create, name='olympiad_task_create'),
    path('manage/<int:olympiad_id>/tasks/<int:task_id>/edit/', views.olympiad_task_edit, name='olympiad_task_edit'),
    path('manage/<int:olympiad_id>/tasks/<int:task_id>/delete/', views.olympiad_task_delete, name='olympiad_task_delete'),
    path('manage/<int:olympiad_id>/participants/', views.olympiad_participants, name='olympiad_participants'),
    path('manage/<int:olympiad_id>/invitations/', views.olympiad_invitations, name='olympiad_invitations'),
    path('manage/<int:olympiad_id>/statistics/', views.olympiad_statistics, name='olympiad_statistics'),
]