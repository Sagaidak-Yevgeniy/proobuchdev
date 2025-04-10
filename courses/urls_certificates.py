from django.urls import path
from .certificate_views import (
    my_certificates,
    view_certificate,
    download_certificate_pdf,
    view_certificate_pdf,
    verify_certificate,
    generate_course_certificate,
    generate_olympiad_certificate,
    api_verify_certificate
)

urlpatterns = [
    # Просмотр сертификатов
    path('certificates/', my_certificates, name='my_certificates'),
    path('certificates/<str:certificate_id>/', view_certificate, name='view_certificate'),
    path('certificates/<str:certificate_id>/download/', download_certificate_pdf, name='download_certificate_pdf'),
    path('certificates/<str:certificate_id>/pdf/', view_certificate_pdf, name='view_certificate_pdf'),
    
    # Проверка сертификатов
    path('verify/', verify_certificate, name='verify_certificate'),
    path('verify/<str:certificate_id>/', verify_certificate, name='verify_certificate'),
    path('api/verify/', api_verify_certificate, name='api_verify_certificate'),
    
    # Генерация сертификатов
    path('courses/<int:course_id>/generate-certificate/', generate_course_certificate, name='generate_course_certificate'),
    path('olympiads/<int:olympiad_id>/generate-certificate/', generate_olympiad_certificate, name='generate_olympiad_certificate'),
]