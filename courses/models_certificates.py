from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
import uuid
import os
import base64
import io
import qrcode
from django.core.files.base import ContentFile

class CertificateTemplate(models.Model):
    """Шаблон сертификата"""
    
    TEMPLATE_TYPES = [
        ('course', 'Курс'),
        ('olympiad', 'Олимпиада'),
        ('achievement', 'Достижение'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name='Название шаблона'
    )
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPES,
        default='course',
        verbose_name='Тип шаблона'
    )
    background_image = models.ImageField(
        upload_to='certificate_templates/',
        verbose_name='Фоновое изображение',
        help_text='Рекомендуемый размер: 1200x850px'
    )
    logo_image = models.ImageField(
        upload_to='certificate_templates/logos/',
        null=True,
        blank=True,
        verbose_name='Логотип',
        help_text='Логотип, который будет размещен на сертификате'
    )
    title_text = models.CharField(
        max_length=200,
        default='СЕРТИФИКАТ',
        verbose_name='Заголовок сертификата'
    )
    subtitle_text = models.CharField(
        max_length=200,
        default='о прохождении курса',
        verbose_name='Подзаголовок сертификата'
    )
    footer_text = models.TextField(
        default='© Образовательная платформа, 2025',
        verbose_name='Текст в нижней части сертификата'
    )
    title_font_size = models.PositiveIntegerField(
        default=48,
        verbose_name='Размер шрифта заголовка'
    )
    text_font_size = models.PositiveIntegerField(
        default=24,
        verbose_name='Размер шрифта текста'
    )
    recipient_name_font_size = models.PositiveIntegerField(
        default=36,
        verbose_name='Размер шрифта имени получателя'
    )
    text_color = models.CharField(
        max_length=20,
        default='#000000',
        verbose_name='Цвет текста'
    )
    title_color = models.CharField(
        max_length=20,
        default='#1a1a1a',
        verbose_name='Цвет заголовка'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    
    class Meta:
        verbose_name = 'Шаблон сертификата'
        verbose_name_plural = 'Шаблоны сертификатов'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class Certificate(models.Model):
    """Модель сертификата, выданного пользователю"""
    
    CERTIFICATE_TYPES = [
        ('course', 'Курс'),
        ('olympiad', 'Олимпиада'),
        ('achievement', 'Достижение'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Действителен'),
        ('revoked', 'Отозван'),
        ('expired', 'Истёк'),
    ]
    
    # Идентификаторы
    certificate_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Уникальный ID сертификата'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Пользователь'
    )
    
    # Основная информация
    certificate_type = models.CharField(
        max_length=20,
        choices=CERTIFICATE_TYPES,
        default='course',
        verbose_name='Тип сертификата'
    )
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='certificates',
        verbose_name='Курс'
    )
    olympiad = models.ForeignKey(
        'olympiads.Olympiad',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='certificates',
        verbose_name='Олимпиада'
    )
    achievement = models.ForeignKey(
        'gamification.Achievement',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='certificates',
        verbose_name='Достижение'
    )
    
    # Метаданные
    title = models.CharField(
        max_length=255,
        verbose_name='Название сертификата'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    issued_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата выдачи'
    )
    expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Срок действия'
    )
    
    # Оценка и статистика
    earned_points = models.PositiveIntegerField(
        default=0,
        verbose_name='Набранные баллы'
    )
    max_points = models.PositiveIntegerField(
        default=100,
        verbose_name='Максимальные баллы'
    )
    completion_percentage = models.FloatField(
        default=0,
        verbose_name='Процент выполнения'
    )
    
    # Статус
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Статус'
    )
    
    # Файлы и изображения
    pdf_file = models.FileField(
        upload_to='certificates/pdf/',
        null=True,
        blank=True,
        verbose_name='PDF файл сертификата'
    )
    qr_code = models.ImageField(
        upload_to='certificates/qrcodes/',
        null=True,
        blank=True,
        verbose_name='QR-код сертификата'
    )
    template_used = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='issued_certificates',
        verbose_name='Использованный шаблон'
    )
    
    class Meta:
        verbose_name = 'Сертификат'
        verbose_name_plural = 'Сертификаты'
        ordering = ['-issued_date']
    
    def __str__(self):
        return f"Сертификат {self.certificate_id} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Если сертификат создается, генерируем ему QR-код
        if not self.qr_code:
            self.generate_qr_code()
        
        super().save(*args, **kwargs)
    
    def get_entity_name(self):
        """Возвращает название сущности, за которую выдан сертификат"""
        if self.certificate_type == 'course' and self.course:
            return self.course.title
        elif self.certificate_type == 'olympiad' and self.olympiad:
            return self.olympiad.title
        elif self.certificate_type == 'achievement' and self.achievement:
            return self.achievement.name
        return "Неизвестно"
    
    def get_absolute_url(self):
        """Получить URL для просмотра сертификата"""
        return reverse('view_certificate', kwargs={'certificate_id': self.certificate_id})
    
    def get_verification_url(self):
        """Получить URL для проверки подлинности сертификата"""
        base_url = settings.BASE_URL or 'http://localhost:8000'
        return f"{base_url}{reverse('verify_certificate', kwargs={'certificate_id': self.certificate_id})}"
    
    def generate_qr_code(self):
        """Генерирует QR-код для сертификата"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Добавляем URL для проверки подлинности в QR-код
        qr.add_data(self.get_verification_url())
        qr.make(fit=True)
        
        # Создаем изображение QR-кода
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Сохраняем QR-код в память
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Сохраняем как поле изображения
        filename = f'certificate-qr-{self.certificate_id}.png'
        self.qr_code.save(filename, ContentFile(buffer.read()), save=False)
        buffer.close()