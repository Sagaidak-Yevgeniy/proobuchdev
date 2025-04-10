import os
import io
import uuid
import json
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, FileResponse
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from xhtml2pdf import pisa

from .models import CourseCompletion
# TODO: Раскомментировать эту строку, как только будет создана соответствующая модель в модуле olympiads
# from olympiads.models import OlympiadParticipation
from .models_certificates import Certificate, CertificateTemplate
from .certificates import generate_course_certificate, generate_olympiad_certificate


@login_required
def my_certificates(request):
    """Просмотр всех сертификатов пользователя"""
    certificates = Certificate.objects.filter(user=request.user).order_by('-issued_date')
    
    # Группируем сертификаты по типам
    course_certificates = certificates.filter(certificate_type='course')
    olympiad_certificates = certificates.filter(certificate_type='olympiad')
    achievement_certificates = certificates.filter(certificate_type='achievement')
    
    context = {
        'certificates': certificates,
        'course_certificates': course_certificates,
        'olympiad_certificates': olympiad_certificates,
        'achievement_certificates': achievement_certificates,
    }
    
    return render(request, 'certificates/my_certificates.html', context)


def view_certificate(request, certificate_id):
    """Просмотр конкретного сертификата"""
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    
    # Определяем, принадлежит ли сертификат текущему пользователю
    is_owner = request.user.is_authenticated and certificate.user == request.user
    
    context = {
        'certificate': certificate,
        'is_owner': is_owner,
        'verification_url': certificate.get_verification_url(),
    }
    
    return render(request, 'certificates/view_certificate.html', context)


@login_required
def download_certificate_pdf(request, certificate_id):
    """Скачивание PDF-файла сертификата"""
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    
    # Проверяем, принадлежит ли сертификат пользователю
    if certificate.user != request.user and not request.user.is_staff:
        return HttpResponse('Доступ запрещен', status=403)
    
    # Если PDF еще не сгенерирован, создаем его
    if not certificate.pdf_file:
        from .certificates import generate_certificate_pdf
        generate_certificate_pdf(certificate)
    
    # Если файл не существует, возвращаем ошибку
    if not certificate.pdf_file or not os.path.exists(certificate.pdf_file.path):
        return HttpResponse('Файл не найден', status=404)
    
    # Определяем имя файла для скачивания
    filename = f'certificate_{certificate.certificate_id}.pdf'
    
    # Возвращаем файл для скачивания
    response = FileResponse(open(certificate.pdf_file.path, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def view_certificate_pdf(request, certificate_id):
    """Просмотр PDF-файла сертификата в браузере"""
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    
    # Если PDF еще не сгенерирован, создаем его
    if not certificate.pdf_file:
        from .certificates import generate_certificate_pdf
        generate_certificate_pdf(certificate)
    
    # Если файл не существует, возвращаем ошибку
    if not certificate.pdf_file or not os.path.exists(certificate.pdf_file.path):
        return HttpResponse('Файл не найден', status=404)
    
    # Возвращаем файл для просмотра в браузере
    response = FileResponse(open(certificate.pdf_file.path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="certificate.pdf"'
    return response


def verify_certificate(request, certificate_id=None):
    """Проверка подлинности сертификата"""
    certificate = None
    error = None
    success = False
    
    if certificate_id:
        try:
            certificate = Certificate.objects.get(certificate_id=certificate_id)
            success = True
        except Certificate.DoesNotExist:
            error = "Сертификат с указанным ID не найден."
    
    elif request.method == 'POST':
        certificate_id = request.POST.get('certificate_id', '')
        if certificate_id:
            try:
                certificate = Certificate.objects.get(certificate_id=certificate_id)
                success = True
            except Certificate.DoesNotExist:
                error = "Сертификат с указанным ID не найден."
        else:
            error = "Введите ID сертификата."
    
    context = {
        'certificate': certificate,
        'certificate_id': certificate_id,
        'error': error,
        'success': success,
    }
    
    return render(request, 'certificates/verify.html', context)


@csrf_exempt
def api_verify_certificate(request):
    """API для проверки подлинности сертификата"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            certificate_id = data.get('certificate_id')
            
            if not certificate_id:
                return JsonResponse({'success': False, 'error': 'Не указан ID сертификата'})
            
            try:
                certificate = Certificate.objects.get(certificate_id=certificate_id)
                
                # Формируем данные о сертификате
                certificate_data = {
                    'certificate_id': str(certificate.certificate_id),
                    'user': certificate.user.get_full_name() or certificate.user.username,
                    'title': certificate.title,
                    'type': certificate.get_certificate_type_display(),
                    'entity_name': certificate.get_entity_name(),
                    'issued_date': certificate.issued_date.strftime('%d.%m.%Y'),
                    'expiry_date': certificate.expiry_date.strftime('%d.%m.%Y') if certificate.expiry_date else None,
                    'status': certificate.get_status_display(),
                    'earned_points': certificate.earned_points,
                    'max_points': certificate.max_points,
                    'completion_percentage': certificate.completion_percentage,
                }
                
                return JsonResponse({
                    'success': True,
                    'certificate': certificate_data
                })
            
            except Certificate.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Сертификат с указанным ID не найден'})
        
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Неверный формат JSON'})
    
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})


@login_required
def generate_course_certificate_view(request, course_id):
    """Генерация сертификата о прохождении курса"""
    from .models import Course
    
    course = get_object_or_404(Course, id=course_id)
    
    # Проверяем, может ли пользователь получить сертификат
    if not course.can_generate_certificate(request.user):
        return render(request, 'certificates/error.html', {
            'error': 'Вы не можете получить сертификат для этого курса. Убедитесь, что курс завершен и набрано достаточное количество баллов.'
        })
    
    # Проверяем, есть ли уже сертификат
    existing_certificate = Certificate.objects.filter(
        user=request.user,
        course=course,
        certificate_type='course'
    ).first()
    
    if existing_certificate:
        return redirect('view_certificate', certificate_id=existing_certificate.certificate_id)
    
    # Генерируем сертификат
    certificate = generate_course_certificate(request.user, course)
    
    if certificate:
        return redirect('view_certificate', certificate_id=certificate.certificate_id)
    else:
        return render(request, 'certificates/error.html', {
            'error': 'Не удалось сгенерировать сертификат. Пожалуйста, обратитесь к администратору.'
        })


@login_required
def generate_olympiad_certificate_view(request, olympiad_id):
    """Генерация сертификата об участии в олимпиаде"""
    from olympiads.models import Olympiad
    
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем участие пользователя в олимпиаде
    # TODO: Раскомментировать, когда будет создана модель OlympiadParticipation
    # participation = OlympiadParticipation.objects.filter(
    #     user=request.user,
    #     olympiad=olympiad,
    #     is_completed=True
    # ).exists()
    
    # Для тестирования - считаем, что участие есть
    participation = True
    
    if not participation:
        return render(request, 'certificates/error.html', {
            'error': 'Вы не можете получить сертификат, поскольку не завершили участие в этой олимпиаде.'
        })
    
    # Проверяем, есть ли уже сертификат
    existing_certificate = Certificate.objects.filter(
        user=request.user,
        olympiad=olympiad,
        certificate_type='olympiad'
    ).first()
    
    if existing_certificate:
        return redirect('view_certificate', certificate_id=existing_certificate.certificate_id)
    
    # Генерируем сертификат
    certificate = generate_olympiad_certificate(request.user, olympiad)
    
    if certificate:
        return redirect('view_certificate', certificate_id=certificate.certificate_id)
    else:
        return render(request, 'certificates/error.html', {
            'error': 'Не удалось сгенерировать сертификат. Пожалуйста, обратитесь к администратору.'
        })