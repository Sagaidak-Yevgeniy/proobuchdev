from django.urls import path

from . import views
from . import api
from . import api_events
from . import api_goals

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
    
    # Страницы мероприятий и целей
    path('events/', views.events_list, name='events'),
    path('goals/', views.goals_list, name='goals'),
    
    # API для основного функционала дашборда
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
    
    # API для управления мероприятиями
    path('api/events/', api_events.get_events, name='api_events'),
    path('api/events/<int:event_id>/', api_events.get_event_details, name='api_event_details'),
    path('api/events/create/', api_events.create_event, name='api_create_event'),
    path('api/events/<int:event_id>/update/', api_events.update_event, name='api_update_event'),
    path('api/events/<int:event_id>/delete/', api_events.delete_event, name='api_delete_event'),
    path('api/events/<int:event_id>/register/', api_events.register_for_event, name='api_register_for_event'),
    path('api/events/<int:event_id>/cancel/', api_events.cancel_registration, name='api_cancel_registration'),
    path('api/events/<int:event_id>/feedback/', api_events.send_event_feedback, name='api_send_event_feedback'),
    path('api/events/<int:event_id>/participant/<int:user_id>/', api_events.update_participant_status, name='api_update_participant_status'),
    
    # API для управления целями студентов
    path('api/student-goals/', api_goals.get_student_goals, name='api_student_goals'),
    path('api/student-goals/<int:goal_id>/', api_goals.get_goal_details, name='api_goal_details'),
    path('api/student-goals/create/', api_goals.create_goal, name='api_create_goal'),
    path('api/student-goals/<int:goal_id>/update/', api_goals.update_goal, name='api_update_goal'),
    path('api/student-goals/<int:goal_id>/delete/', api_goals.delete_goal, name='api_delete_goal'),
    path('api/student-goals/<int:goal_id>/toggle/', api_goals.toggle_goal, name='api_toggle_student_goal'),
    path('api/student-goals/<int:goal_id>/steps/create/', api_goals.create_goal_step, name='api_create_goal_step'),
    path('api/student-goals/<int:goal_id>/steps/<int:step_id>/update/', api_goals.update_goal_step, name='api_update_goal_step'),
    path('api/student-goals/<int:goal_id>/steps/<int:step_id>/delete/', api_goals.delete_goal_step, name='api_delete_goal_step'),
    path('api/student-goals/<int:goal_id>/steps/<int:step_id>/toggle/', api_goals.toggle_goal_step, name='api_toggle_goal_step'),
]