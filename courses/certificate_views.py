import os
import uuid
import json
from datetime import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from xhtml2pdf import pisa

from .models_certificates import Certificate, CertificateTemplate
from .certificates import generate_course_certificate, generate_olympiad_certificate


@login_required
def my_certificates(request):
    """Просмотр всех сертификатов пользователя"""
    certificates = Certificate.objects.filter(user=request.user).order_by('-issued_date')
    
    context = {
        'certificates': certificates,
    }
    
    return render(request, 'certificates/my_certificates.html', context)


@login_required
def view_certificate(request, certificate_id):
    """Просмотр конкретного сертификата"""
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    
    # Проверяем доступ пользователя к сертификату
    if certificate.user != request.user and not request.user.is_staff:
        return render(request, 'certificates/error.html', {
            'error': 'У вас нет доступа к этому сертификату.',
            'title': 'Ошибка доступа'
        })
    
    # Формируем URL для проверки подлинности
    verification_url = request.build_absolute_uri(
        reverse('verify_certificate', args=[certificate.certificate_id])
    )
    
    context = {
        'certificate': certificate,
        'verification_url': verification_url,
    }
    
    return render(request, 'certificates/view_certificate.html', context)


@login_required
def download_certificate_pdf(request, certificate_id):
    """Скачивание PDF-файла сертификата"""
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    
    # Проверяем доступ пользователя к сертификату
    if certificate.user != request.user and not request.user.is_staff:
        return render(request, 'certificates/error.html', {
            'error': 'У вас нет доступа к скачиванию этого сертификата.',
            'title': 'Ошибка доступа'
        })
    
    # Проверяем наличие PDF
    if not certificate.pdf_file:
        return render(request, 'certificates/error.html', {
            'error': 'PDF-файл для этого сертификата не сгенерирован.',
            'title': 'Файл не найден'
        })
    
    # Формируем имя файла
    filename = f'certificate-{certificate.certificate_id}.pdf'
    
    # Отправляем файл
    response = HttpResponse(certificate.pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def view_certificate_pdf(request, certificate_id):
    """Просмотр PDF-файла сертификата в браузере"""
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    
    # Если это предпросмотр для карточки, то доступ есть только у владельца
    # В остальных случаях PDF можно просматривать публично (например, по ссылке верификации)
    if 'preview' in request.GET and certificate.user != request.user and not request.user.is_staff:
        return HttpResponse('Доступ запрещен', status=403)
    
    # Проверяем наличие PDF
    if not certificate.pdf_file:
        return HttpResponse('PDF-файл не найден', status=404)
    
    # Отправляем файл для просмотра в браузере
    response = HttpResponse(certificate.pdf_file, content_type='application/pdf')
    
    # Если это предпросмотр, то просто отправляем первую страницу как изображение
    if 'preview' in request.GET:
        response['Content-Disposition'] = 'inline; filename="preview.pdf"'
    else:
        response['Content-Disposition'] = 'inline; filename="certificate.pdf"'
    
    return response


def verify_certificate(request, certificate_id=None):
    """Проверка подлинности сертификата"""
    # Если это POST-запрос формы
    if request.method == 'POST' and not certificate_id:
        try:
            certificate_id = request.POST.get('certificate_id')
            return redirect('verify_certificate', certificate_id=certificate_id)
        except (ValueError, TypeError):
            return render(request, 'certificates/verify.html', {
                'error': 'Неверный формат ID сертификата. Пожалуйста, проверьте и попробуйте снова.'
            })
    
    # Если это GET-запрос с ID сертификата
    if certificate_id:
        try:
            certificate = Certificate.objects.get(certificate_id=certificate_id)
            
            # Формируем URL для проверки подлинности
            verification_url = request.build_absolute_uri(
                reverse('verify_certificate', args=[certificate.certificate_id])
            )
            
            return render(request, 'certificates/verify.html', {
                'certificate': certificate,
                'certificate_id': certificate_id,
                'success': True,
                'verification_url': verification_url,
            })
        except Certificate.DoesNotExist:
            return render(request, 'certificates/verify.html', {
                'error': 'Сертификат с указанным ID не найден. Пожалуйста, проверьте правильность ID и попробуйте снова.',
                'certificate_id': certificate_id,
            })
    
    # Если это просто открытие страницы верификации
    return render(request, 'certificates/verify.html')


@csrf_exempt
def api_verify_certificate(request):
    """API для проверки подлинности сертификата"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    try:
        data = json.loads(request.body)
        certificate_id = data.get('certificate_id')
        
        if not certificate_id:
            return JsonResponse({'error': 'ID сертификата не указан'}, status=400)
        
        try:
            certificate = Certificate.objects.get(certificate_id=certificate_id)
            
            # Формируем данные о сертификате
            certificate_data = {
                'id': str(certificate.certificate_id),
                'title': certificate.title,
                'type': certificate.get_certificate_type_display(),
                'issued_to': certificate.user.get_full_name() or certificate.user.username,
                'issued_date': certificate.issued_date.strftime('%Y-%m-%d'),
                'status': certificate.status,
                'status_display': dict(Certificate.STATUS_CHOICES).get(certificate.status),
                'verification_url': request.build_absolute_uri(
                    reverse('verify_certificate', args=[certificate.certificate_id])
                ),
            }
            
            # Добавляем данные в зависимости от типа сертификата
            if certificate.certificate_type == 'course' and certificate.course:
                certificate_data.update({
                    'course_title': certificate.course.title,
                    'course_author': certificate.course.author.get_full_name() or certificate.course.author.username,
                })
            elif certificate.certificate_type == 'olympiad' and certificate.olympiad:
                certificate_data.update({
                    'olympiad_title': certificate.olympiad.title,
                    'olympiad_organizer': certificate.olympiad.organizer.get_full_name() or certificate.olympiad.organizer.username,
                })
            
            return JsonResponse({
                'success': True,
                'certificate': certificate_data
            })
        
        except Certificate.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Сертификат не найден'
            }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def generate_course_certificate_view(request, course_id):
    """Генерация сертификата о прохождении курса"""
    from .models import Course
    
    course = get_object_or_404(Course, id=course_id)
    
    # Проверяем, может ли пользователь получить сертификат
    if not course.can_generate_certificate(request.user):
        return render(request, 'certificates/error.html', {
            'error': 'Вы не можете получить сертификат, так как не завершили курс или не выполнили все необходимые требования.',
            'title': 'Сертификат недоступен'
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
            'error': 'Не удалось сгенерировать сертификат. Пожалуйста, обратитесь к администратору.',
            'title': 'Ошибка генерации'
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
            'error': 'Вы не можете получить сертификат, поскольку не завершили участие в этой олимпиаде.',
            'title': 'Сертификат недоступен'
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
            'error': 'Не удалось сгенерировать сертификат. Пожалуйста, обратитесь к администратору.',
            'title': 'Ошибка генерации'
        })