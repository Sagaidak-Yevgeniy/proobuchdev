from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.urls import reverse

class Notification(models.Model):
    """Модель уведомления"""
    
    TYPE_CHOICES = [
        ('info', _('Информация')),
        ('success', _('Успех')),
        ('warning', _('Предупреждение')),
        ('error', _('Ошибка')),
        ('course', _('Курс')),
        ('lesson', _('Урок')),
        ('assignment', _('Задание')),
        ('message', _('Сообщение')),
        ('achievement', _('Достижение')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Пользователь')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_('Заголовок')
    )
    message = models.TextField(
        verbose_name=_('Сообщение')
    )
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='info',
        verbose_name=_('Тип уведомления')
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Прочитано')
    )
    is_high_priority = models.BooleanField(
        default=False,
        verbose_name=_('Высокий приоритет')
    )
    url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('URL')
    )
    
    # Связь с любой моделью через ContentType (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('Тип контента')
    )
    object_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('ID объекта')
    )
    content_object = GenericForeignKey(
        'content_type',
        'object_id'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Создано')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Обновлено')
    )
    
    class Meta:
        verbose_name = _('Уведомление')
        verbose_name_plural = _('Уведомления')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Отмечает уведомление как прочитанное"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read', 'updated_at'])
        return True


class NotificationSettings(models.Model):
    """Настройки уведомлений пользователя"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings',
        verbose_name=_('Пользователь')
    )
    
    # Общие настройки
    receive_all = models.BooleanField(
        default=True,
        verbose_name=_('Получать все уведомления'),
        help_text=_('Если отключено, вы не будете получать никаких уведомлений')
    )
    notify_only_high_priority = models.BooleanField(
        default=False,
        verbose_name=_('Получать только важные уведомления'),
        help_text=_('Получать уведомления только с высоким приоритетом')
    )
    
    # Настройки по типам
    receive_achievement = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления о достижениях'),
        help_text=_('Получать уведомления о новых достижениях и наградах')
    )
    receive_course = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления о курсах'),
        help_text=_('Получать уведомления об обновлениях в курсах')
    )
    receive_lesson = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления об уроках'),
        help_text=_('Получать уведомления о новых уроках')
    )
    receive_assignment = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления о заданиях'),
        help_text=_('Получать уведомления о заданиях и их проверке')
    )
    receive_message = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления о сообщениях'),
        help_text=_('Получать уведомления о новых сообщениях')
    )
    
    # Настройки email
    email_notifications = models.BooleanField(
        default=False,
        verbose_name=_('Email-уведомления'),
        help_text=_('Дублировать уведомления на email')
    )
    email_digest = models.BooleanField(
        default=False,
        verbose_name=_('Еженедельная сводка на email'),
        help_text=_('Получать еженедельную сводку активности на email')
    )
    
    # Технические поля
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Создано')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Обновлено')
    )
    
    class Meta:
        verbose_name = _('Настройки уведомлений')
        verbose_name_plural = _('Настройки уведомлений')
        
    def __str__(self):
        return f"Настройки уведомлений - {self.user.username}"
    
    def can_receive_notification(self, notification_type=None, is_high_priority=False):
        """
        Проверяет, может ли пользователь получать уведомления определенного типа.
        
        Args:
            notification_type (str): Тип уведомления (например, 'course', 'lesson')
            is_high_priority (bool): Является ли уведомление высокоприоритетным
            
        Returns:
            bool: True, если пользователь может получать уведомления этого типа
        """
        # Если все уведомления отключены, то никакие не отправляются
        if not self.receive_all:
            return False
            
        # Если только высокоприоритетные, и это не высокоприоритетное
        if self.notify_only_high_priority and not is_high_priority:
            return False
            
        # Проверка по типу уведомления
        if notification_type:
            if notification_type == 'achievement' and not self.receive_achievement:
                return False
            elif notification_type == 'course' and not self.receive_course:
                return False
            elif notification_type == 'lesson' and not self.receive_lesson:
                return False
            elif notification_type == 'assignment' and not self.receive_assignment:
                return False
            elif notification_type == 'message' and not self.receive_message:
                return False
                
        return True