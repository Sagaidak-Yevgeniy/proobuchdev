from django.urls import path
from . import views

urlpatterns = [
    # Общие страницы 
    path('', views.olympiad_list, name='olympiad_list'),
    path('olympiad/<slug:slug>/', views.olympiad_detail, name='olympiad_detail'),
    path('olympiad/<slug:slug>/register/', views.olympiad_register, name='olympiad_register'),
    path('olympiad/<slug:slug>/problem/<int:pk>/', views.problem_detail, name='problem_detail'),
    path('olympiad/<slug:olympiad_slug>/problem/<int:problem_id>/submit/', 
         views.submit_solution, name='submit_solution'),
    path('olympiad/<slug:slug>/submissions/', views.submission_list, name='submission_list'),
    path('olympiad/<slug:olympiad_slug>/submission/<int:submission_id>/', 
         views.submission_detail, name='submission_detail'),
    path('olympiad/<slug:slug>/leaderboard/', views.olympiad_leaderboard, name='olympiad_leaderboard'),
    
    # Административные страницы
    path('create/', views.olympiad_create, name='olympiad_create'),
    path('olympiad/<slug:slug>/edit/', views.olympiad_edit, name='olympiad_edit'),
    path('olympiad/<slug:slug>/delete/', views.olympiad_delete, name='olympiad_delete'),
    path('olympiad/<slug:slug>/publish/', views.olympiad_publish, name='olympiad_publish'),
    path('olympiad/<slug:olympiad_slug>/problem/create/', 
         views.problem_create, name='problem_create'),
    path('olympiad/<slug:olympiad_slug>/problem/<int:pk>/edit/', 
         views.problem_edit, name='problem_edit'),
    path('olympiad/<slug:olympiad_slug>/problem/<int:pk>/delete/', 
         views.problem_delete, name='problem_delete'),
    path('olympiad/<slug:olympiad_slug>/problem/<int:problem_pk>/testcase/create/', 
         views.testcase_create, name='testcase_create'),
    path('olympiad/<slug:olympiad_slug>/problem/<int:problem_pk>/testcase/<int:pk>/edit/', 
         views.testcase_edit, name='testcase_edit'),
    path('olympiad/<slug:olympiad_slug>/problem/<int:problem_pk>/testcase/<int:pk>/delete/', 
         views.testcase_delete, name='testcase_delete'),
]