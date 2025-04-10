from django.urls import path
from .certificate_views import (
    my_certificates,
    view_certificate,
    download_certificate_pdf,
    view_certificate_pdf,
    verify_certificate,
    api_verify_certificate,
    generate_course_certificate_view,
    generate_olympiad_certificate_view,
)

urlpatterns = [
    # Просмотр сертификатов пользователя
    path('', my_certificates, name='my_certificates'),
    
    # Детальный просмотр и скачивание сертификата
    path('<uuid:certificate_id>/', view_certificate, name='view_certificate'),
    path('<uuid:certificate_id>/download/', download_certificate_pdf, name='download_certificate_pdf'),
    path('<uuid:certificate_id>/pdf/', view_certificate_pdf, name='view_certificate_pdf'),
    
    # Проверка подлинности сертификата
    path('verify/', verify_certificate, name='verify_certificate_form'),
    path('verify/<uuid:certificate_id>/', verify_certificate, name='verify_certificate'),
    path('api/verify/', api_verify_certificate, name='api_verify_certificate'),
    
    # Генерация сертификатов
    path('<int:course_id>/generate-certificate/', generate_course_certificate_view, name='generate_course_certificate'),
    path('olympiads/<int:olympiad_id>/generate-certificate/', generate_olympiad_certificate_view, name='generate_olympiad_certificate'),
]