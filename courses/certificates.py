import os
import io
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa
from PIL import Image, ImageDraw, ImageFont
from .models import CourseCompletion
# TODO: Раскомментировать эту строку, как только будет создана соответствующая модель в модуле olympiads
# from olympiads.models import OlympiadParticipation


def create_certificate_from_template(user, template, context_data, certificate_type='course'):
    """
    Создает сертификат на основе шаблона
    
    Args:
        user: Пользователь, получающий сертификат
        template: Шаблон сертификата (CertificateTemplate)
        context_data: Данные для отображения на сертификате
        certificate_type: Тип сертификата ('course', 'olympiad', 'achievement')
    
    Returns:
        Объект Certificate
    """
    from .models_certificates import Certificate
    
    # Создаем новый сертификат
    certificate = Certificate(
        user=user,
        certificate_type=certificate_type,
        template_used=template,
        title=context_data.get('title', 'Сертификат'),
        description=context_data.get('description', ''),
        earned_points=context_data.get('earned_points', 0),
        max_points=context_data.get('max_points', 100),
        completion_percentage=context_data.get('completion_percentage', 0),
    )
    
    # Устанавливаем связь с соответствующей сущностью
    if certificate_type == 'course' and 'course' in context_data:
        certificate.course = context_data['course']
    elif certificate_type == 'olympiad' and 'olympiad' in context_data:
        certificate.olympiad = context_data['olympiad']
    elif certificate_type == 'achievement' and 'achievement' in context_data:
        certificate.achievement = context_data['achievement']
    
    # Устанавливаем срок действия (если нужно)
    if 'valid_days' in context_data and context_data['valid_days'] > 0:
        certificate.expiry_date = timezone.now() + timedelta(days=context_data['valid_days'])
    
    # Сохраняем сертификат перед генерацией PDF
    certificate.save()
    
    # Генерируем PDF
    generate_certificate_pdf(certificate)
    
    return certificate


def generate_certificate_pdf(certificate):
    """
    Генерирует PDF-файл сертификата
    
    Args:
        certificate: Объект сертификата
    """
    # Получаем HTML шаблон для сертификата
    template = get_template('certificates/certificate.html')
    
    # Готовим контекст для шаблона
    context = {
        'certificate': certificate,
        'user': certificate.user,
        'date': certificate.issued_date.strftime('%d.%m.%Y'),
        'certificate_id': certificate.certificate_id,
        'verification_url': certificate.get_verification_url(),
    }
    
    # Добавляем данные в зависимости от типа сертификата
    if certificate.certificate_type == 'course' and certificate.course:
        # Для курса
        completion = CourseCompletion.objects.filter(
            user=certificate.user, 
            course=certificate.course
        ).first()
        
        context.update({
            'course': certificate.course,
            'completion': completion,
            'content_title': certificate.course.title,
            'earned_points': certificate.earned_points,
            'max_points': certificate.max_points,
            'percentage': certificate.completion_percentage,
        })
    
    elif certificate.certificate_type == 'olympiad' and certificate.olympiad:
        # Для олимпиады
        # TODO: Раскомментировать, когда будет создана модель OlympiadParticipation
        # participation = OlympiadParticipation.objects.filter(
        #     user=certificate.user, 
        #     olympiad=certificate.olympiad
        # ).first()
        
        context.update({
            'olympiad': certificate.olympiad,
            # 'participation': participation,
            'content_title': certificate.olympiad.title,
            'earned_points': certificate.earned_points,
            'max_points': certificate.max_points,
            'percentage': certificate.completion_percentage,
        })
    
    # Для шаблона также добавляем CSS и другие настройки
    context.update({
        'STATIC_URL': settings.STATIC_URL,
        'MEDIA_URL': settings.MEDIA_URL,
    })
    
    # Рендерим HTML
    html = template.render(context)
    
    # Создаем PDF из HTML
    result = io.BytesIO()
    pdf = pisa.CreatePDF(
        src=io.StringIO(html),
        dest=result,
        encoding='utf-8'
    )
    
    if not pdf.err:
        # Сохраняем PDF в поле модели
        filename = f'certificate-{certificate.certificate_id}.pdf'
        from django.core.files.base import ContentFile
        certificate.pdf_file.save(filename, ContentFile(result.getvalue()), save=True)
    
    result.close()


def generate_course_certificate(user, course):
    """
    Генерирует сертификат о прохождении курса
    
    Args:
        user: Пользователь, получающий сертификат
        course: Объект курса
    
    Returns:
        Объект Certificate или None в случае ошибки
    """
    # Проверяем возможность выдачи сертификата
    if not course.can_generate_certificate(user):
        return None
    
    # Получаем данные о завершении курса
    completion = CourseCompletion.objects.filter(user=user, course=course).first()
    if not completion:
        return None
    
    # Получаем шаблон сертификата
    template = course.certificate_template
    if not template:
        # Если у курса нет шаблона, берем дефолтный для курсов
        from .models_certificates import CertificateTemplate
        template = CertificateTemplate.objects.filter(
            template_type='course', 
            is_active=True
        ).first()
    
    if not template:
        return None
    
    # Данные для отображения на сертификате
    context_data = {
        'course': course,
        'title': f'Сертификат о прохождении курса "{course.title}"',
        'description': course.description,
        'earned_points': completion.earned_points,
        'max_points': completion.max_points,
        'completion_percentage': completion.percentage,
        'valid_days': 365 * 5,  # Сертификат действителен 5 лет
    }
    
    # Создаем сертификат
    certificate = create_certificate_from_template(
        user=user,
        template=template,
        context_data=context_data,
        certificate_type='course'
    )
    
    # Обновляем статус в записи о завершении курса
    completion.certificate_generated = True
    completion.save(update_fields=['certificate_generated'])
    
    return certificate


def generate_olympiad_certificate(user, olympiad):
    """
    Генерирует сертификат об участии в олимпиаде
    
    Args:
        user: Пользователь, получающий сертификат
        olympiad: Объект олимпиады
    
    Returns:
        Объект Certificate или None в случае ошибки
    """
    # TODO: Раскомментировать, когда будут созданы соответствующие модели
    # from olympiads.models import OlympiadParticipation, ProblemSubmission
    
    # Проверяем участие в олимпиаде - пока это заглушка
    # TODO: Раскомментировать, когда будет создана модель OlympiadParticipation
    # participation = OlympiadParticipation.objects.filter(
    #     user=user, 
    #     olympiad=olympiad,
    #     is_completed=True
    # ).first()
    # 
    # if not participation:
    #     return None
    
    # Для тестирования - считаем, что участие есть
    participation = True
    
    # Получаем шаблон сертификата
    template = olympiad.certificate_template
    if not template:
        # Если у олимпиады нет шаблона, берем дефолтный для олимпиад
        from .models_certificates import CertificateTemplate
        template = CertificateTemplate.objects.filter(
            template_type='olympiad', 
            is_active=True
        ).first()
    
    if not template:
        return None
    
    # Подсчет баллов - пока заглушка
    # TODO: Раскомментировать, когда будет создана модель ProblemSubmission
    # earned_points = ProblemSubmission.objects.filter(
    #     user=user,
    #     problem__olympiad=olympiad,
    #     status='approved'
    # ).aggregate(models.Sum('points'))['points__sum'] or 0
    
    # Для тестирования
    earned_points = 85
    
    # Максимально возможные баллы - пока заглушка
    # TODO: Раскомментировать, когда будет создана модель Problem
    # from olympiads.models import Problem
    # max_points = Problem.objects.filter(
    #     olympiad=olympiad
    # ).aggregate(models.Sum('max_points'))['max_points__sum'] or 0
    
    # Для тестирования
    max_points = 100
    
    if max_points > 0:
        percentage = (earned_points / max_points) * 100
    else:
        percentage = 0
    
    # Данные для отображения на сертификате
    context_data = {
        'olympiad': olympiad,
        'title': f'Сертификат участника олимпиады "{olympiad.title}"',
        'description': olympiad.description,
        'earned_points': earned_points,
        'max_points': max_points,
        'completion_percentage': percentage,
        'valid_days': 365 * 5,  # Сертификат действителен 5 лет
    }
    
    # Создаем сертификат
    certificate = create_certificate_from_template(
        user=user,
        template=template,
        context_data=context_data,
        certificate_type='olympiad'
    )
    
    # Обновляем статус в записи об участии в олимпиаде
    # TODO: Раскомментировать, когда будет создана модель OlympiadParticipation
    # participation.certificate_generated = True
    # participation.save(update_fields=['certificate_generated'])
    
    return certificate