from django.db import models
from django.utils.translation import gettext as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.urls import reverse


class Notification(models.Model):
    """Модель для уведомлений пользователей"""
    
    NOTIFICATION_TYPES = [
        ('info', _('Информация')),
        ('success', _('Успех')),
        ('warning', _('Предупреждение')),
        ('error', _('Ошибка')),
        ('achievement', _('Достижение')),
        ('course', _('Курс')),
        ('lesson', _('Урок')),
        ('assignment', _('Задание')),
        ('message', _('Сообщение')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Пользователь')
    )
    title = models.CharField(max_length=100, verbose_name=_('Заголовок'))
    message = models.TextField(verbose_name=_('Сообщение'))
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='info',
        verbose_name=_('Тип уведомления')
    )
    is_read = models.BooleanField(default=False, verbose_name=_('Прочитано'))
    is_high_priority = models.BooleanField(default=False, verbose_name=_('Высокий приоритет'))
    url = models.CharField(max_length=200, blank=True, null=True, verbose_name=_('URL'))
    
    # Поля для связи с любым объектом (GenericForeignKey)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('Тип контента')
    )
    object_id = models.PositiveIntegerField(blank=True, null=True, verbose_name=_('ID объекта'))
    content_object = GenericForeignKey('content_type', 'object_id')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Создано'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Обновлено'))
    
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
    
    def get_absolute_url(self):
        """Возвращает URL для просмотра уведомления или связанного объекта"""
        if self.url:
            return self.url
        return reverse('notifications:notification_list')


class NotificationSettings(models.Model):
    """Модель для настроек уведомлений пользователя"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings',
        verbose_name=_('Пользователь')
    )
    
    # Общие настройки
    receive_all = models.BooleanField(default=True, verbose_name=_('Получать все уведомления'))
    notify_only_high_priority = models.BooleanField(
        default=False,
        verbose_name=_('Получать только важные уведомления')
    )
    
    # Типы уведомлений
    receive_achievement = models.BooleanField(default=True, verbose_name=_('Уведомления о достижениях'))
    receive_course = models.BooleanField(default=True, verbose_name=_('Уведомления о курсах'))
    receive_lesson = models.BooleanField(default=True, verbose_name=_('Уведомления об уроках'))
    receive_assignment = models.BooleanField(default=True, verbose_name=_('Уведомления о заданиях'))
    receive_message = models.BooleanField(default=True, verbose_name=_('Уведомления о сообщениях'))
    
    # Email уведомления
    email_notifications = models.BooleanField(default=True, verbose_name=_('Email-уведомления'))
    email_digest = models.BooleanField(
        default=False,
        verbose_name=_('Получать дайджест вместо отдельных писем')
    )
    
    # Push уведомления
    push_notifications = models.BooleanField(default=False, verbose_name=_('Push-уведомления'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Создано'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Обновлено'))
    
    class Meta:
        verbose_name = _('Настройки уведомлений')
        verbose_name_plural = _('Настройки уведомлений')
    
    def __str__(self):
        return f"Настройки уведомлений - {self.user.username}"
    
    def should_receive(self, notification_type, is_high_priority=False):
        """Проверяет, должен ли пользователь получать уведомление данного типа"""
        if not self.receive_all:
            return False
            
        if self.notify_only_high_priority and not is_high_priority:
            return False
            
        if notification_type == 'achievement':
            return self.receive_achievement
        elif notification_type == 'course':
            return self.receive_course
        elif notification_type == 'lesson':
            return self.receive_lesson
        elif notification_type == 'assignment':
            return self.receive_assignment
        elif notification_type == 'message':
            return self.receive_message
            
        # Для остальных типов (info, success, warning, error) всегда True
        return True