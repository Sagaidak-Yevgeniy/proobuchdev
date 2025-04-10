from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('create/', views.course_create, name='course_create'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    
    # Включаем пути для сертификатов
    # Важно расположить ДО маршрутов с параметрами <slug:slug>
    path('certificates/', include('courses.urls_certificates')),
    
    # Маршруты с параметрами
    path('<slug:slug>/', views.course_detail, name='course_detail'),
    path('<slug:slug>/edit/', views.course_edit, name='course_edit'),
    path('<slug:slug>/edit-content/', views.course_edit_content, name='course_edit_content'),
    path('<slug:slug>/delete/', views.course_delete, name='course_delete'),
    path('<slug:slug>/enroll/', views.course_enroll, name='course_enroll'),
]
