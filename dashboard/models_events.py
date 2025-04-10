from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime

from users.models import CustomUser


class Event(models.Model):
    """Модель для мероприятий"""
    
    EVENT_TYPE_CHOICES = [
        ('webinar', 'Вебинар'),
        ('lecture', 'Лекция'),
        ('seminar', 'Семинар'),
        ('consultation', 'Консультация'),
        ('deadline', 'Дедлайн'),
        ('other', 'Другое'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name=_('Название')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        default='other',
        verbose_name=_('Тип мероприятия')
    )
    start_time = models.DateTimeField(
        verbose_name=_('Время начала')
    )
    end_time = models.DateTimeField(
        verbose_name=_('Время окончания')
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Место проведения')
    )
    url = models.URLField(
        blank=True,
        verbose_name=_('Ссылка')
    )
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='created_events',
        verbose_name=_('Организатор')
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
        verbose_name=_('Курс')
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=_('Публичное')
    )
    max_participants = models.PositiveIntegerField(
        default=0,  # 0 - без ограничений
        verbose_name=_('Максимальное количество участников')
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
        verbose_name = _('Мероприятие')
        verbose_name_plural = _('Мероприятия')
        ordering = ['start_time']
    
    def __str__(self):
        return self.title
    
    @property
    def participants_count(self):
        """Возвращает количество участников мероприятия"""
        return self.participants.count()
    
    @property
    def is_full(self):
        """Проверяет, заполнено ли мероприятие до максимума"""
        if self.max_participants <= 0:
            return False
        return self.participants_count >= self.max_participants
    
    @property
    def is_past(self):
        """Проверяет, прошло ли мероприятие"""
        return self.end_time < timezone.now()
    
    @property
    def is_ongoing(self):
        """Проверяет, идет ли мероприятие в данный момент"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time
    
    @property
    def is_upcoming(self):
        """Проверяет, предстоит ли мероприятие"""
        return self.start_time > timezone.now()


class EventParticipant(models.Model):
    """Модель для участников мероприятий"""
    
    STATUS_CHOICES = [
        ('registered', 'Зарегистрирован'),
        ('confirmed', 'Подтвержден'),
        ('attended', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
        ('canceled', 'Отменен'),
    ]
    
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name=_('Мероприятие')
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='event_participations',
        verbose_name=_('Пользователь')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='registered',
        verbose_name=_('Статус')
    )
    registered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата регистрации')
    )
    attended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата посещения')
    )
    feedback = models.TextField(
        blank=True,
        verbose_name=_('Отзыв')
    )
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Оценка')
    )
    
    class Meta:
        verbose_name = _('Участник мероприятия')
        verbose_name_plural = _('Участники мероприятий')
        unique_together = ['event', 'user']
        ordering = ['registered_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title}"