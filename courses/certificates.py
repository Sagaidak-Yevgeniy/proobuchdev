import uuid
import os
from io import BytesIO
from django.conf import settings
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa
from PIL import Image, ImageDraw, ImageFont
from .models import Course, CourseEnrollment, CourseCompletion
from olympiads.models import Olympiad, OlympiadParticipation


def generate_certificate_id():
    """
    Генерирует уникальный ID сертификата
    """
    return str(uuid.uuid4()).upper()[:16]


def render_to_pdf(template_src, context_dict={}):
    """
    Преобразует HTML-шаблон в PDF-файл
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None


def generate_certificate_image(user, course=None, olympiad=None, points=0, max_points=0, completion_date=None):
    """
    Генерирует изображение сертификата с данными пользователя, курса/олимпиады и результатами
    """
    # Загружаем шаблон сертификата
    template_path = os.path.join(settings.STATIC_ROOT, 'images', 'certificate_template.png')
    if not os.path.exists(template_path):
        template_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'certificate_template.png')
    
    try:
        img = Image.open(template_path)
    except FileNotFoundError:
        # Если шаблон не найден, создаем базовое изображение
        img = Image.new('RGB', (1200, 850), color=(255, 255, 255))
        # Добавляем рамку
        draw = ImageDraw.Draw(img)
        draw.rectangle([(20, 20), (1180, 830)], outline=(0, 112, 192), width=5)
    
    draw = ImageDraw.Draw(img)
    
    # Определяем путь к шрифтам
    font_path = os.path.join(settings.STATIC_ROOT, 'fonts', 'Roboto-Regular.ttf')
    if not os.path.exists(font_path):
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Roboto-Regular.ttf')
    
    try:
        # Пытаемся загрузить шрифт
        title_font = ImageFont.truetype(font_path, 48)
        header_font = ImageFont.truetype(font_path, 36)
        normal_font = ImageFont.truetype(font_path, 24)
    except (IOError, OSError):
        # Если шрифт не найден, используем стандартный
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
    
    # Добавляем логотип
    logo_path = os.path.join(settings.STATIC_ROOT, 'images', 'logo.png')
    if not os.path.exists(logo_path):
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    
    try:
        logo = Image.open(logo_path)
        logo = logo.resize((150, 150))
        img.paste(logo, (525, 50), logo if logo.mode == 'RGBA' else None)
    except (FileNotFoundError, IOError):
        # Если логотип не найден, пропускаем
        pass
    
    # Заголовок сертификата
    draw.text((600, 230), "СЕРТИФИКАТ", fill=(0, 0, 0), font=title_font, anchor="mm")
    
    # Номер сертификата
    certificate_id = generate_certificate_id()
    draw.text((600, 290), f"№ {certificate_id}", fill=(100, 100, 100), font=normal_font, anchor="mm")
    
    # Имя пользователя
    full_name = user.get_full_name() or user.username
    draw.text((600, 350), f"Настоящим удостоверяется, что", fill=(0, 0, 0), font=normal_font, anchor="mm")
    draw.text((600, 400), full_name.upper(), fill=(0, 0, 0), font=header_font, anchor="mm")
    
    # Информация о курсе или олимпиаде
    if course:
        draw.text((600, 460), "успешно завершил(а) курс:", fill=(0, 0, 0), font=normal_font, anchor="mm")
        draw.text((600, 510), course.title.upper(), fill=(0, 112, 192), font=header_font, anchor="mm")
        entity_name = "курса"
    elif olympiad:
        draw.text((600, 460), "успешно участвовал(а) в олимпиаде:", fill=(0, 0, 0), font=normal_font, anchor="mm")
        draw.text((600, 510), olympiad.title.upper(), fill=(0, 112, 192), font=header_font, anchor="mm")
        entity_name = "олимпиады"
    else:
        draw.text((600, 460), "успешно выполнил(а) задания", fill=(0, 0, 0), font=normal_font, anchor="mm")
        entity_name = "программы"
    
    # Результаты
    percentage = int(points / max_points * 100) if max_points > 0 else 0
    draw.text((600, 570), f"Результат: {points} из {max_points} баллов ({percentage}%)", fill=(0, 0, 0), font=normal_font, anchor="mm")
    
    # Дата завершения
    completion_date = completion_date or timezone.now()
    date_str = completion_date.strftime("%d.%m.%Y")
    draw.text((600, 630), f"Дата завершения {entity_name}: {date_str}", fill=(0, 0, 0), font=normal_font, anchor="mm")
    
    # Подпись
    draw.text((300, 730), "Подпись:", fill=(0, 0, 0), font=normal_font, anchor="mm")
    # Линия для подписи
    draw.line([(370, 730), (570, 730)], fill=(0, 0, 0), width=2)
    
    # QR-код или проверочная информация
    draw.text((900, 730), f"Для проверки подлинности сертификата", fill=(100, 100, 100), font=ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default(), anchor="mm")
    draw.text((900, 750), f"посетите сайт и введите номер: {certificate_id}", fill=(100, 100, 100), font=ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default(), anchor="mm")
    
    # Сохраняем изображение в буфер
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer, certificate_id


def create_course_certificate(user, course_enrollment):
    """
    Создает сертификат о завершении курса
    
    Args:
        user (CustomUser): Пользователь, которому выдается сертификат
        course_enrollment (CourseEnrollment): Запись о зачислении на курс
    
    Returns:
        tuple: (img_buffer, certificate_id) - буфер с изображением сертификата и его ID
    """
    course = course_enrollment.course
    
    # Получаем информацию о прогрессе и баллах
    from courses.models import LessonCompletion, AssignmentSubmission
    
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
        user=user,
        assignment__lesson__course=course,
        status='approved'
    ).count()
    
    # Сколько баллов набрал пользователь
    earned_points = sum(
        submission.points
        for submission in AssignmentSubmission.objects.filter(
            user=user,
            assignment__lesson__course=course,
            status='approved'
        )
    )
    
    # Дата завершения курса
    completion_date = CourseCompletion.objects.filter(
        user=user, course=course
    ).first().completion_date if CourseCompletion.objects.filter(
        user=user, course=course
    ).exists() else timezone.now()
    
    # Генерируем изображение сертификата
    return generate_certificate_image(
        user=user,
        course=course,
        points=earned_points,
        max_points=max_points,
        completion_date=completion_date
    )


def create_olympiad_certificate(user, olympiad_participation):
    """
    Создает сертификат участника олимпиады
    
    Args:
        user (CustomUser): Пользователь, которому выдается сертификат
        olympiad_participation (OlympiadParticipation): Запись об участии в олимпиаде
    
    Returns:
        tuple: (img_buffer, certificate_id) - буфер с изображением сертификата и его ID
    """
    olympiad = olympiad_participation.olympiad
    
    # Получаем информацию о прогрессе и баллах
    from olympiads.models import ProblemSubmission
    
    # Какой максимальный балл за олимпиаду
    max_points = sum(problem.max_points for problem in olympiad.problems.all())
    
    # Сколько баллов набрал пользователь
    earned_points = sum(
        submission.points
        for submission in ProblemSubmission.objects.filter(
            user=user,
            problem__olympiad=olympiad,
            status='approved'
        )
    )
    
    # Дата завершения олимпиады
    completion_date = olympiad_participation.last_submission_time or olympiad.end_date or timezone.now()
    
    # Генерируем изображение сертификата
    return generate_certificate_image(
        user=user,
        olympiad=olympiad,
        points=earned_points,
        max_points=max_points,
        completion_date=completion_date
    )