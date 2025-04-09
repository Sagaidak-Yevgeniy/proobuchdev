from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('<int:pk>/solve/', views.assignment_solve, name='assignment_solve'),
    path('<int:pk>/edit/', views.assignment_edit, name='assignment_edit'),
    path('submission/<int:pk>/', views.submission_detail, name='submission_detail'),
    path('test-case/create/<int:assignment_id>/', views.test_case_create, name='test_case_create'),
    path('test-case/<int:pk>/edit/', views.test_case_edit, name='test_case_edit'),
    path('test-case/<int:pk>/delete/', views.test_case_delete, name='test_case_delete'),
]
