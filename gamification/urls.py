from django.urls import path
from . import views

urlpatterns = [
    path('achievements/', views.achievement_list, name='achievement_list'),
    path('achievement/<int:pk>/', views.achievement_detail, name='achievement_detail'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('badges/', views.badge_list, name='badge_list'),
    path('profile/<int:user_id>/gamification/', views.user_gamification_profile, name='user_gamification_profile'),
]