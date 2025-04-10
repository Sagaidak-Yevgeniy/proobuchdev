from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
import uuid
import qrcode
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile


class Certificate(models.Model):
    """Модель сертификата"""
    
    TYPE_CHOICES = [
        ('course', 'Курс'),
        ('olympiad', 'Олимпиада'),
        ('achievement', 'Достижение'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('revoked', 'Отозван'),
        ('expired', 'Истёк'),
    ]
    
    # Уникальный идентификатор сертификата
    certificate_id = models.CharField(
        max_length=36, 
        unique=True, 
        default=uuid.uuid4, 
        editable=False,
        verbose_name='ID сертификата'
    )
    
    # Владелец сертификата
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Пользователь'
    )
    
    # Тип сертификата
    certificate_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='course',
        verbose_name='Тип сертификата'
    )
    
    # Статус сертификата
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Статус сертификата'
    )
    
    # Связь с курсом (может быть NULL если сертификат за олимпиаду или достижение)
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates',
        verbose_name='Курс'
    )
    
    # Связь с олимпиадой (может быть NULL если сертификат за курс или достижение)
    olympiad = models.ForeignKey(
        'olympiads.Olympiad',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates',
        verbose_name='Олимпиада'
    )
    
    # Связь с достижением (может быть NULL если сертификат за курс или олимпиаду)
    achievement = models.ForeignKey(
        'gamification.Achievement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates',
        verbose_name='Достижение'
    )
    
    # Название сертификата
    title = models.CharField(
        max_length=255,
        verbose_name='Название сертификата'
    )
    
    # Описание сертификата
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    
    # Набранные баллы
    earned_points = models.PositiveIntegerField(
        default=0,
        verbose_name='Набранные баллы'
    )
    
    # Максимальные баллы
    max_points = models.PositiveIntegerField(
        default=0,
        verbose_name='Максимальные баллы'
    )
    
    # Процент выполнения
    completion_percentage = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Процент выполнения'
    )
    
    # Дата выдачи сертификата
    issued_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата выдачи'
    )
    
    # Дата истечения сертификата (если применимо)
    expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата истечения'
    )
    
    # Файл сертификата (генерируемый)
    certificate_file = models.FileField(
        upload_to='certificates/',
        null=True,
        blank=True,
        verbose_name='Файл сертификата'
    )
    
    # QR-код для проверки
    qr_code = models.ImageField(
        upload_to='certificates/qr_codes/',
        null=True,
        blank=True,
        verbose_name='QR-код'
    )
    
    # Поля для аудита
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Сертификат'
        verbose_name_plural = 'Сертификаты'
        ordering = ['-issued_date']
    
    def __str__(self):
        return f"Сертификат {self.certificate_id}: {self.title} ({self.get_certificate_type_display()})"
    
    def save(self, *args, **kwargs):
        """При сохранении генерируем QR-код для проверки сертификата"""
        if not self.qr_code:
            # Создаём URL для проверки сертификата
            verification_url = settings.BASE_URL + reverse('verify_certificate', args=[self.certificate_id])
            
            # Генерируем QR-код
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)
            
            # Создаём изображение QR-кода
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Преобразуем в файл для сохранения
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Сохраняем QR-код как изображение
            self.qr_code.save(
                f'qr_certificate_{self.certificate_id}.png',
                ContentFile(buffer.read()),
                save=False
            )
            
        # Вычисляем процент выполнения
        if self.max_points > 0:
            self.completion_percentage = int((self.earned_points / self.max_points) * 100)
        
        super().save(*args, **kwargs)
        
    def get_verification_url(self):
        """Возвращает URL для проверки сертификата"""
        return settings.BASE_URL + reverse('verify_certificate', args=[self.certificate_id])
    
    def is_valid(self):
        """Проверяет, действителен ли сертификат"""
        return (
            self.status == 'active' and 
            (self.expiry_date is None or self.expiry_date > timezone.now())
        )
    
    def get_entity_name(self):
        """Возвращает название сущности, за которую выдан сертификат"""
        if self.certificate_type == 'course' and self.course:
            return self.course.title
        elif self.certificate_type == 'olympiad' and self.olympiad:
            return self.olympiad.title
        elif self.certificate_type == 'achievement' and self.achievement:
            return self.achievement.name
        return "Неизвестно"


class CertificateTemplate(models.Model):
    """Модель шаблона сертификата"""
    
    name = models.CharField(
        max_length=100,
        verbose_name='Название шаблона'
    )
    
    # Тип сертификата для которого используется шаблон
    certificate_type = models.CharField(
        max_length=20,
        choices=Certificate.TYPE_CHOICES,
        default='course',
        verbose_name='Тип сертификата'
    )
    
    # Фоновое изображение
    background_image = models.ImageField(
        upload_to='certificate_templates/',
        verbose_name='Фоновое изображение'
    )
    
    # HTML-шаблон для генерации PDF
    html_template = models.TextField(
        help_text='HTML-шаблон для генерации PDF',
        verbose_name='HTML-шаблон'
    )
    
    # Цвет заголовка
    title_color = models.CharField(
        max_length=20,
        default='#000000',
        verbose_name='Цвет заголовка'
    )
    
    # Цвет текста
    text_color = models.CharField(
        max_length=20,
        default='#000000',
        verbose_name='Цвет текста'
    )
    
    # Шрифт заголовка
    title_font = models.CharField(
        max_length=100,
        default='Roboto',
        verbose_name='Шрифт заголовка'
    )
    
    # Шрифт текста
    text_font = models.CharField(
        max_length=100,
        default='Roboto',
        verbose_name='Шрифт текста'
    )
    
    # Размер шрифта заголовка
    title_font_size = models.PositiveSmallIntegerField(
        default=48,
        verbose_name='Размер шрифта заголовка'
    )
    
    # Размер шрифта текста
    text_font_size = models.PositiveSmallIntegerField(
        default=24,
        verbose_name='Размер шрифта текста'
    )
    
    # Показывать ли логотип
    show_logo = models.BooleanField(
        default=True,
        verbose_name='Показывать логотип'
    )
    
    # Показывать ли QR-код
    show_qr_code = models.BooleanField(
        default=True,
        verbose_name='Показывать QR-код'
    )
    
    # Показывать ли подпись
    show_signature = models.BooleanField(
        default=True,
        verbose_name='Показывать подпись'
    )
    
    # Изображение подписи
    signature_image = models.ImageField(
        upload_to='certificate_signatures/',
        null=True,
        blank=True,
        verbose_name='Изображение подписи'
    )
    
    # Имя подписывающего
    signatory_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Имя подписывающего'
    )
    
    # Должность подписывающего
    signatory_position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Должность подписывающего'
    )
    
    # Активный шаблон
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активный'
    )
    
    # Поля для аудита
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Шаблон сертификата'
        verbose_name_plural = 'Шаблоны сертификатов'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_certificate_type_display()})"