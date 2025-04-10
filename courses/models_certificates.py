import os
import io
import uuid
import qrcode
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from django.core.files.base import ContentFile

User = get_user_model()


class CertificateTemplate(models.Model):
    """Модель шаблона сертификата"""
    
    TEMPLATE_TYPE_CHOICES = [
        ('course', 'Курс'),
        ('olympiad', 'Олимпиада'),
        ('achievement', 'Достижение'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Название шаблона')
    template_type = models.CharField(
        max_length=20, 
        choices=TEMPLATE_TYPE_CHOICES,
        default='course',
        verbose_name='Тип шаблона'
    )
    
    # Настройки дизайна
    background_image = models.ImageField(
        upload_to='certificate_templates/backgrounds/',
        blank=True,
        null=True,
        verbose_name='Фоновое изображение'
    )
    logo_image = models.ImageField(
        upload_to='certificate_templates/logos/',
        blank=True,
        null=True,
        verbose_name='Логотип'
    )
    
    # Цвета и шрифты
    title_color = models.CharField(
        max_length=20, 
        default='#1a1a1a',
        verbose_name='Цвет заголовка'
    )
    text_color = models.CharField(
        max_length=20, 
        default='#333333',
        verbose_name='Цвет текста'
    )
    
    # Размеры шрифтов
    title_font_size = models.PositiveSmallIntegerField(
        default=48,
        verbose_name='Размер шрифта заголовка'
    )
    text_font_size = models.PositiveSmallIntegerField(
        default=24,
        verbose_name='Размер шрифта текста'
    )
    recipient_name_font_size = models.PositiveSmallIntegerField(
        default=36,
        verbose_name='Размер шрифта имени получателя'
    )
    
    # Тексты
    title_text = models.CharField(
        max_length=100, 
        default='СЕРТИФИКАТ',
        verbose_name='Текст заголовка'
    )
    subtitle_text = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name='Текст подзаголовка'
    )
    footer_text = models.CharField(
        max_length=200, 
        default='© Образовательная платформа, 2025',
        verbose_name='Текст футера'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    
    # Мета-информация
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлен'
    )
    
    class Meta:
        verbose_name = 'Шаблон сертификата'
        verbose_name_plural = 'Шаблоны сертификатов'
        ordering = ['name']
    
    def __str__(self):
        return f'{self.name} ({self.get_template_type_display()})'


class Certificate(models.Model):
    """Модель сертификата"""
    
    CERTIFICATE_TYPE_CHOICES = [
        ('course', 'Курс'),
        ('olympiad', 'Олимпиада'),
        ('achievement', 'Достижение'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Действителен'),
        ('revoked', 'Отозван'),
        ('expired', 'Истек'),
    ]
    
    # Основная информация
    certificate_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID сертификата'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Пользователь'
    )
    
    certificate_type = models.CharField(
        max_length=20,
        choices=CERTIFICATE_TYPE_CHOICES,
        default='course',
        verbose_name='Тип сертификата'
    )
    
    # Связи с сущностями
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates',
        verbose_name='Курс'
    )
    
    olympiad = models.ForeignKey(
        'olympiads.Olympiad',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates',
        verbose_name='Олимпиада'
    )
    
    achievement = models.ForeignKey(
        'gamification.Achievement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates',
        verbose_name='Достижение'
    )
    
    # Информация о сертификате
    title = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    
    template_used = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='certificates',
        verbose_name='Использованный шаблон'
    )
    
    # Статус и даты
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Статус'
    )
    
    issued_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата выдачи'
    )
    
    expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата истечения'
    )
    
    # Результаты
    earned_points = models.PositiveIntegerField(
        default=0,
        verbose_name='Набрано баллов'
    )
    
    max_points = models.PositiveIntegerField(
        default=100,
        verbose_name='Максимум баллов'
    )
    
    completion_percentage = models.FloatField(
        default=0,
        verbose_name='Процент выполнения'
    )
    
    # Файлы
    pdf_file = models.FileField(
        upload_to='certificates/pdf/',
        null=True,
        blank=True,
        verbose_name='PDF-файл'
    )
    
    qr_code = models.ImageField(
        upload_to='certificates/qr_codes/',
        null=True,
        blank=True,
        verbose_name='QR-код'
    )
    
    # Мета-информация
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлен'
    )
    
    class Meta:
        verbose_name = 'Сертификат'
        verbose_name_plural = 'Сертификаты'
        ordering = ['-issued_date']
    
    def __str__(self):
        return f'{self.title} - {self.user.username} ({self.certificate_id})'
    
    def save(self, *args, **kwargs):
        """Переопределяем метод сохранения для генерации QR-кода"""
        if not self.qr_code:
            self.generate_qr_code()
        
        # Проверка статуса по дате истечения
        if self.expiry_date and self.expiry_date < timezone.now():
            self.status = 'expired'
        
        super().save(*args, **kwargs)
    
    def get_entity_name(self):
        """Возвращает название связанной сущности"""
        if self.certificate_type == 'course' and self.course:
            return self.course.title
        elif self.certificate_type == 'olympiad' and self.olympiad:
            return self.olympiad.title
        elif self.certificate_type == 'achievement' and self.achievement:
            return self.achievement.name
        return "Неизвестно"
    
    def get_verification_url(self):
        """Возвращает URL для проверки подлинности сертификата"""
        return settings.BASE_URL + reverse('verify_certificate', args=[self.certificate_id])
    
    def generate_qr_code(self):
        """Генерирует QR-код для сертификата"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Добавляем URL для проверки в QR-код
        verification_url = settings.BASE_URL + reverse('verify_certificate', args=[self.certificate_id])
        qr.add_data(verification_url)
        qr.make(fit=True)
        
        # Создаем изображение QR-кода
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Конвертируем в байты для сохранения
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Сохраняем в поле модели
        filename = f'qr_certificate_{self.certificate_id}.png'
        self.qr_code.save(filename, ContentFile(buffer.read()), save=False)
        buffer.close()