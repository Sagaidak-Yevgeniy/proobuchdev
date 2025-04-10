import os
import uuid
from io import BytesIO
from datetime import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, FileResponse, JsonResponse
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from xhtml2pdf import pisa

from .models import Course, CourseEnrollment, CourseCompletion
from olympiads.models import Olympiad, OlympiadParticipation
from users.models import CustomUser
from .models_certificates import Certificate, CertificateTemplate


def render_to_pdf(template_src, context_dict={}):
    """
    Преобразует HTML-шаблон в PDF-файл
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    
    # В контексте передаем MEDIA_URL для правильного отображения изображений
    context_dict['MEDIA_URL'] = settings.MEDIA_URL
    
    pdf = pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")), 
        result,
        encoding='utf-8',
        link_callback=fetch_resources
    )
    
    if not pdf.err:
        return result.getvalue()
    return None


def fetch_resources(uri, rel):
    """
    Функция для загрузки внешних ресурсов в PDF (изображения и т.д.)
    """
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    else:
        path = uri
    
    return path


@login_required
def my_certificates(request):
    """
    Отображает список всех сертификатов пользователя
    """
    certificates = Certificate.objects.filter(user=request.user).order_by('-issued_date')
    
    return render(request, 'certificates/my_certificates.html', {
        'certificates': certificates,
        'title': 'Мои сертификаты'
    })


@login_required
def view_certificate(request, certificate_id):
    """
    Отображает сертификат для просмотра
    """
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    
    # Проверяем, имеет ли пользователь доступ к этому сертификату
    if certificate.user != request.user and not request.user.is_staff:
        return redirect('my_certificates')
    
    return render(request, 'certificates/view_certificate.html', {
        'certificate': certificate,
        'title': f'Сертификат {certificate.certificate_id}'
    })


@login_required
def download_certificate_pdf(request, certificate_id):
    """
    Скачивает сертификат в формате PDF
    """
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    
    # Проверяем, имеет ли пользователь доступ к этому сертификату
    if certificate.user != request.user and not request.user.is_staff:
        return redirect('my_certificates')
    
    # Если файл уже существует, возвращаем его
    if certificate.certificate_file and os.path.exists(certificate.certificate_file.path):
        return FileResponse(
            open(certificate.certificate_file.path, 'rb'),
            as_attachment=True,
            filename=f'certificate_{certificate.certificate_id}.pdf'
        )
    
    # Иначе генерируем PDF
    # Получаем шаблон сертификата
    template = CertificateTemplate.objects.filter(
        certificate_type=certificate.certificate_type,
        is_active=True
    ).first()
    
    if not template:
        # Если нет активного шаблона, используем дефолтный
        template = CertificateTemplate.objects.filter(is_active=True).first()
    
    if not template:
        return HttpResponse("Шаблон сертификата не найден", status=404)
    
    # Создаем контекст для шаблона
    context = {
        'certificate': certificate,
        'user': certificate.user,
        'template': template,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    
    # Генерируем PDF
    pdf = render_to_pdf('certificates/certificate.html', context)
    
    if not pdf:
        return HttpResponse("Ошибка при создании PDF", status=500)
    
    # Сохраняем PDF в файл
    filename = f'certificate_{certificate.certificate_id}.pdf'
    certificate.certificate_file.save(filename, ContentFile(pdf))
    
    # Возвращаем PDF для скачивания
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def view_certificate_pdf(request, certificate_id):
    """
    Просмотр сертификата в формате PDF в браузере
    """
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    
    # Проверяем, имеет ли пользователь доступ к этому сертификату
    if certificate.user != request.user and not request.user.is_staff:
        return redirect('my_certificates')
    
    # Если файл уже существует, возвращаем его
    if certificate.certificate_file and os.path.exists(certificate.certificate_file.path):
        return FileResponse(
            open(certificate.certificate_file.path, 'rb'),
            content_type='application/pdf'
        )
    
    # Иначе генерируем PDF
    # Получаем шаблон сертификата
    template = CertificateTemplate.objects.filter(
        certificate_type=certificate.certificate_type,
        is_active=True
    ).first()
    
    if not template:
        # Если нет активного шаблона, используем дефолтный
        template = CertificateTemplate.objects.filter(is_active=True).first()
    
    if not template:
        return HttpResponse("Шаблон сертификата не найден", status=404)
    
    # Создаем контекст для шаблона
    context = {
        'certificate': certificate,
        'user': certificate.user,
        'template': template,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    
    # Генерируем PDF
    pdf = render_to_pdf('certificates/certificate.html', context)
    
    if not pdf:
        return HttpResponse("Ошибка при создании PDF", status=500)
    
    # Сохраняем PDF в файл
    filename = f'certificate_{certificate.certificate_id}.pdf'
    certificate.certificate_file.save(filename, ContentFile(pdf))
    
    # Возвращаем PDF для просмотра
    return HttpResponse(pdf, content_type='application/pdf')


def verify_certificate(request, certificate_id=None):
    """
    Проверяет подлинность сертификата
    """
    certificate = None
    error = None
    success = False
    
    if certificate_id:
        try:
            certificate = Certificate.objects.get(certificate_id=certificate_id)
            success = certificate.is_valid()
            
            if not success:
                if certificate.status == 'revoked':
                    error = "Этот сертификат был отозван."
                elif certificate.status == 'expired':
                    error = "Срок действия этого сертификата истек."
                else:
                    error = "Этот сертификат недействителен."
        except Certificate.DoesNotExist:
            error = "Сертификат с указанным номером не найден."
    
    if request.method == 'POST' and not certificate_id:
        certificate_id = request.POST.get('certificate_id', '').strip()
        return redirect('verify_certificate', certificate_id=certificate_id)
    
    return render(request, 'certificates/verify.html', {
        'certificate': certificate,
        'error': error,
        'success': success,
        'certificate_id': certificate_id,
        'title': 'Проверка сертификата'
    })


@login_required
def generate_course_certificate(request, course_id):
    """
    Генерирует сертификат о завершении курса
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Проверяем, записан ли пользователь на курс
    enrollment = get_object_or_404(CourseEnrollment, user=request.user, course=course)
    
    # Проверяем, завершил ли пользователь курс
    completion = CourseCompletion.objects.filter(user=request.user, course=course).first()
    
    if not completion:
        return HttpResponse("Вы еще не завершили этот курс.", status=403)
    
    # Проверяем, существует ли уже сертификат для этого курса
    existing_certificate = Certificate.objects.filter(
        user=request.user,
        course=course,
        certificate_type='course'
    ).first()
    
    if existing_certificate:
        return redirect('view_certificate', certificate_id=existing_certificate.certificate_id)
    
    # Получаем информацию о прогрессе и баллах
    from .models import LessonCompletion, AssignmentSubmission
    
    # Сколько всего заданий в курсе
    total_assignments = sum(lesson.assignments.count() for lesson in course.lessons.all())
    
    # Какой максимальный балл за курс
    max_points = sum(
        assignment.max_points
        for lesson in course.lessons.all()
        for assignment in lesson.assignments.all()
    )
    
    # Сколько заданий выполнил пользователь
    completed_assignments = AssignmentSubmission.objects.filter(
        user=request.user,
        assignment__lesson__course=course,
        status='approved'
    ).count()
    
    # Сколько баллов набрал пользователь
    earned_points = sum(
        submission.points
        for submission in AssignmentSubmission.objects.filter(
            user=request.user,
            assignment__lesson__course=course,
            status='approved'
        )
    )
    
    # Проверяем, достаточно ли баллов для сертификата
    if earned_points < course.min_points_for_certificate:
        return HttpResponse(
            f"Недостаточно баллов для получения сертификата. Необходимо набрать минимум {course.min_points_for_certificate} баллов.", 
            status=403
        )
    
    # Создаем сертификат
    certificate = Certificate.objects.create(
        user=request.user,
        certificate_type='course',
        course=course,
        title=f"Сертификат о завершении курса '{course.title}'",
        description=f"Этот сертификат подтверждает, что {request.user.get_full_name() or request.user.username} успешно завершил(а) курс '{course.title}'.",
        earned_points=earned_points,
        max_points=max_points,
        completion_percentage=int(earned_points / max_points * 100) if max_points > 0 else 0,
        issued_date=timezone.now(),
    )
    
    # Генерируем QR-код при сохранении
    certificate.save()
    
    # Перенаправляем на страницу просмотра сертификата
    return redirect('view_certificate', certificate_id=certificate.certificate_id)


@login_required
def generate_olympiad_certificate(request, olympiad_id):
    """
    Генерирует сертификат участника олимпиады
    """
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем, участвовал ли пользователь в олимпиаде
    participation = get_object_or_404(OlympiadParticipation, user=request.user, olympiad=olympiad)
    
    # Проверяем, закончилась ли олимпиада
    if olympiad.end_date and olympiad.end_date > timezone.now():
        return HttpResponse("Олимпиада еще не завершена.", status=403)
    
    # Проверяем, существует ли уже сертификат для этой олимпиады
    existing_certificate = Certificate.objects.filter(
        user=request.user,
        olympiad=olympiad,
        certificate_type='olympiad'
    ).first()
    
    if existing_certificate:
        return redirect('view_certificate', certificate_id=existing_certificate.certificate_id)
    
    # Получаем информацию о прогрессе и баллах
    from olympiads.models import ProblemSubmission
    
    # Какой максимальный балл за олимпиаду
    max_points = sum(problem.max_points for problem in olympiad.problems.all())
    
    # Сколько баллов набрал пользователь
    earned_points = sum(
        submission.points
        for submission in ProblemSubmission.objects.filter(
            user=request.user,
            problem__olympiad=olympiad,
            status='approved'
        )
    )
    
    # Проверяем, достаточно ли баллов для сертификата
    if earned_points < olympiad.min_points_for_certificate:
        return HttpResponse(
            f"Недостаточно баллов для получения сертификата. Необходимо набрать минимум {olympiad.min_points_for_certificate} баллов.", 
            status=403
        )
    
    # Создаем сертификат
    certificate = Certificate.objects.create(
        user=request.user,
        certificate_type='olympiad',
        olympiad=olympiad,
        title=f"Сертификат участника олимпиады '{olympiad.title}'",
        description=f"Этот сертификат подтверждает, что {request.user.get_full_name() or request.user.username} успешно участвовал(а) в олимпиаде '{olympiad.title}'.",
        earned_points=earned_points,
        max_points=max_points,
        completion_percentage=int(earned_points / max_points * 100) if max_points > 0 else 0,
        issued_date=timezone.now(),
    )
    
    # Генерируем QR-код при сохранении
    certificate.save()
    
    # Перенаправляем на страницу просмотра сертификата
    return redirect('view_certificate', certificate_id=certificate.certificate_id)


@csrf_exempt
def api_verify_certificate(request):
    """
    API для проверки подлинности сертификата
    """
    certificate_id = request.GET.get('id', '')
    
    if not certificate_id:
        return JsonResponse({
            'success': False,
            'error': 'Не указан ID сертификата'
        })
    
    try:
        certificate = Certificate.objects.get(certificate_id=certificate_id)
        
        return JsonResponse({
            'success': True,
            'valid': certificate.is_valid(),
            'status': certificate.status,
            'certificate_id': certificate.certificate_id,
            'type': certificate.get_certificate_type_display(),
            'title': certificate.title,
            'issued_to': certificate.user.get_full_name() or certificate.user.username,
            'issued_date': certificate.issued_date.strftime('%d.%m.%Y'),
            'entity_name': certificate.get_entity_name(),
            'points': {
                'earned': certificate.earned_points,
                'max': certificate.max_points,
                'percentage': certificate.completion_percentage
            }
        })
    except Certificate.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Сертификат с указанным номером не найден'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })