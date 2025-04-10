from django.urls import path

from . import views
from . import api

app_name = 'dashboard'

urlpatterns = [
    # Основной маршрут дашборда
    path('', views.new_dashboard, name='index'),
    path('classic/', views.dashboard, name='classic'),  # Старый дашборд для обратной совместимости
    
    # Настройки и управление виджетами
    path('settings/', views.dashboard_settings, name='settings'),
    path('widgets/add/', views.add_widget, name='add_widget'),
    path('widgets/<int:widget_id>/', views.edit_widget, name='edit_widget'),
    path('widgets/<int:widget_id>/delete/', views.delete_widget, name='delete_widget'),
    path('widgets/<int:widget_id>/position/', views.update_widget_position, name='update_widget_position'),
    path('widgets/<int:widget_id>/size/', views.update_widget_size, name='update_widget_size'),
    path('widgets/<int:widget_id>/data/', views.get_widget_data, name='get_widget_data'),
    path('layout/save/', views.save_layout, name='save_layout'),
    
    # API для нового дашборда
    path('api/statistics/', api.get_statistics, name='api_statistics'),
    path('api/courses-progress/', api.get_courses_progress, name='api_courses_progress'),
    path('api/recent-activity/', api.get_recent_activity, name='api_recent_activity'),
    path('api/achievements/', api.get_achievements, name='api_achievements'),
    path('api/schedule/', api.get_schedule, name='api_schedule'),
    path('api/leaderboard/', api.get_leaderboard, name='api_leaderboard'),
    path('api/goals/', api.get_goals, name='api_goals'),
    path('api/goals/add/', api.add_goal, name='api_add_goal'),
    path('api/goals/<int:goal_id>/toggle/', api.toggle_goal, name='api_toggle_goal'),
    path('api/goals/<int:goal_id>/delete/', api.delete_goal, name='api_delete_goal'),
]