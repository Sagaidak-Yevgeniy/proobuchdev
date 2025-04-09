from django.db import models
from django.utils.translation import gettext as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.urls import reverse
import uuid


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
        ('system', _('Системное')),
        ('deadline', _('Дедлайн')),
    ]
    
    IMPORTANCE_LEVELS = [
        ('low', _('Низкая')),
        ('normal', _('Нормальная')),
        ('high', _('Высокая')),
        ('critical', _('Критическая')),
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
    importance = models.CharField(
        max_length=10,
        choices=IMPORTANCE_LEVELS,
        default='normal',
        verbose_name=_('Важность')
    )
    is_read = models.BooleanField(default=False, verbose_name=_('Прочитано'))
    is_high_priority = models.BooleanField(default=False, verbose_name=_('Высокий приоритет'))
    url = models.CharField(max_length=200, blank=True, null=True, verbose_name=_('URL'))
    icon = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Иконка'))
    extra_data = models.JSONField(blank=True, null=True, verbose_name=_('Дополнительные данные'))
    
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


class DeviceToken(models.Model):
    """Модель для хранения токенов устройств для push-уведомлений"""
    
    DEVICE_TYPES = [
        ('android', _('Android')),
        ('ios', _('iOS')),
        ('web', _('Web Browser')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_tokens',
        verbose_name=_('Пользователь')
    )
    token = models.CharField(max_length=255, verbose_name=_('Токен устройства'))
    device_type = models.CharField(
        max_length=10, 
        choices=DEVICE_TYPES,
        verbose_name=_('Тип устройства')
    )
    device_name = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name=_('Название устройства')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Активно'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Зарегистрировано'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Обновлено'))
    
    class Meta:
        verbose_name = _('Токен устройства')
        verbose_name_plural = _('Токены устройств')
        unique_together = ('user', 'token')
    
    def __str__(self):
        return f"{self.user.username} - {self.device_name or self.device_type}"


class NotificationChannel(models.Model):
    """Модель для настройки каналов уведомлений"""
    
    CHANNEL_TYPES = [
        ('web', _('Веб-уведомления')),
        ('email', _('Email')),
        ('push', _('Push-уведомления')),
        ('telegram', _('Telegram')),
    ]
    
    name = models.CharField(max_length=100, verbose_name=_('Название канала'))
    channel_type = models.CharField(
        max_length=20, 
        choices=CHANNEL_TYPES,
        verbose_name=_('Тип канала')
    )
    description = models.TextField(blank=True, null=True, verbose_name=_('Описание'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активен'))
    
    class Meta:
        verbose_name = _('Канал уведомлений')
        verbose_name_plural = _('Каналы уведомлений')
    
    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"


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
    receive_system = models.BooleanField(default=True, verbose_name=_('Системные уведомления'))
    receive_deadline = models.BooleanField(default=True, verbose_name=_('Уведомления о дедлайнах'))
    
    # Email уведомления
    email_notifications = models.BooleanField(default=True, verbose_name=_('Email-уведомления'))
    email_digest = models.BooleanField(
        default=False,
        verbose_name=_('Получать дайджест вместо отдельных писем')
    )
    
    # Push уведомления
    push_notifications = models.BooleanField(default=True, verbose_name=_('Push-уведомления'))
    quiet_hours_enabled = models.BooleanField(
        default=False, 
        verbose_name=_('Включить тихие часы')
    )
    quiet_hours_start = models.TimeField(
        default='22:00', 
        verbose_name=_('Начало тихих часов')
    )
    quiet_hours_end = models.TimeField(
        default='08:00', 
        verbose_name=_('Конец тихих часов')
    )
    
    # Настройка каналов
    preferred_channels = models.ManyToManyField(
        NotificationChannel,
        verbose_name=_('Предпочитаемые каналы'),
        related_name='user_settings',
        blank=True,
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Создано'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Обновлено'))
    
    class Meta:
        verbose_name = _('Настройки уведомлений')
        verbose_name_plural = _('Настройки уведомлений')
    
    def __str__(self):
        return f"Настройки уведомлений - {self.user.username}"
    
    def should_receive(self, notification_type, importance='normal'):
        """Проверяет, должен ли пользователь получать уведомление данного типа
        
        Args:
            notification_type (str): Тип уведомления
            importance (str): Важность уведомления (low, normal, high, critical)
            
        Returns:
            bool: True если пользователь должен получить уведомление, иначе False
        """
        if not self.receive_all:
            return False
            
        # Проверка на важность уведомления
        if self.notify_only_high_priority and importance not in ('high', 'critical'):
            return False
            
        # Проверка на тип уведомления
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
        elif notification_type == 'system':
            return self.receive_system
        elif notification_type == 'deadline':
            return self.receive_deadline
            
        # Для остальных типов (info, success, warning, error) всегда True
        return True
        
    def get_active_channels(self):
        """Возвращает список активных каналов для отправки уведомлений"""
        if not self.preferred_channels.exists():
            # Если нет выбранных каналов, возвращаем список доступных каналов
            channels = ['web']  # По умолчанию всегда используем веб
            
            if self.email_notifications:
                channels.append('email')
                
            if self.push_notifications:
                channels.append('push')
                
            return channels
        else:
            # Возвращаем список активных каналов из выбранных предпочтений
            return list(self.preferred_channels.filter(is_active=True)
                        .values_list('channel_type', flat=True))
                
    def is_quiet_hours_now(self):
        """Проверяет, попадает ли текущее время в тихие часы"""
        if not self.quiet_hours_enabled:
            return False
            
        from django.utils import timezone
        now = timezone.localtime()
        current_time = now.time()
        
        # Конвертируем строковые значения в объекты time, если нужно
        start_time = self.quiet_hours_start
        end_time = self.quiet_hours_end
        
        if isinstance(start_time, str):
            hours, minutes = map(int, start_time.split(':'))
            start_time = timezone.datetime.time(hours, minutes)
            
        if isinstance(end_time, str):
            hours, minutes = map(int, end_time.split(':'))
            end_time = timezone.datetime.time(hours, minutes)
        
        # Проверяем, находится ли текущее время в диапазоне тихих часов
        if start_time < end_time:
            # Простой случай: начало и конец в один день
            return start_time <= current_time <= end_time
        else:
            # Сложный случай: начало в один день, конец в следующий
            return current_time >= start_time or current_time <= end_time