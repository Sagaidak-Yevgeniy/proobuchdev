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
    path('certificates/', my_certificates, name='my_certificates'),
    
    # Детальный просмотр и скачивание сертификата
    path('certificates/<uuid:certificate_id>/', view_certificate, name='view_certificate'),
    path('certificates/<uuid:certificate_id>/download/', download_certificate_pdf, name='download_certificate_pdf'),
    path('certificates/<uuid:certificate_id>/pdf/', view_certificate_pdf, name='view_certificate_pdf'),
    
    # Проверка подлинности сертификата
    path('certificates/verify/', verify_certificate, name='verify_certificate_form'),
    path('certificates/verify/<uuid:certificate_id>/', verify_certificate, name='verify_certificate'),
    path('certificates/api/verify/', api_verify_certificate, name='api_verify_certificate'),
    
    # Генерация сертификатов
    path('<int:course_id>/generate-certificate/', generate_course_certificate_view, name='generate_course_certificate'),
    path('olympiads/<int:olympiad_id>/generate-certificate/', generate_olympiad_certificate_view, name='generate_olympiad_certificate'),
]