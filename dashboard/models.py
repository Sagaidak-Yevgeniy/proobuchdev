from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import CustomUser

# Импортируем модели из отдельных файлов
from .models_events import Event, EventParticipant
from .models_goals import StudentGoal, GoalStep


class Widget(models.Model):
    """Модель для виджетов дашборда"""

    TYPE_CHOICES = [
        ('courses_progress', 'Прогресс по курсам'),
        ('achievements', 'Достижения'),
        ('recent_activity', 'Недавняя активность'),
        ('statistics', 'Статистика'),
        ('leaderboard', 'Таблица лидеров'),
        ('upcoming_lessons', 'Предстоящие уроки'),
        ('goals', 'Цели обучения'),
        ('study_time', 'Время обучения'),
        ('calendar', 'Календарь'),
        ('notes', 'Заметки'),
    ]

    SIZE_CHOICES = [
        ('small', 'Маленький'),
        ('medium', 'Средний'),
        ('large', 'Большой'),
    ]

    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='widgets',
        verbose_name=_('Пользователь')
    )
    widget_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        verbose_name=_('Тип виджета')
    )
    title = models.CharField(
        max_length=100,
        verbose_name=_('Заголовок')
    )
    position_x = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_('Позиция X')
    )
    position_y = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_('Позиция Y')
    )
    size = models.CharField(
        max_length=10,
        choices=SIZE_CHOICES,
        default='medium',
        verbose_name=_('Размер')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен')
    )
    settings = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Настройки')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Создан')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Обновлен')
    )
    
    class Meta:
        verbose_name = _('Виджет')
        verbose_name_plural = _('Виджеты')
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"


class DashboardLayout(models.Model):
    """Модель для хранения макетов дашборда"""
    
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='dashboard_layout',
        verbose_name=_('Пользователь')
    )
    layout = models.JSONField(
        default=dict,
        verbose_name=_('Макет')
    )
    theme = models.CharField(
        max_length=30,
        default='light',
        verbose_name=_('Тема')
    )
    animation_speed = models.CharField(
        max_length=20,
        default='normal',
        verbose_name=_('Скорость анимации')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Обновлен')
    )
    
    class Meta:
        verbose_name = _('Макет дашборда')
        verbose_name_plural = _('Макеты дашборда')
    
    def __str__(self):
        return f"Макет дашборда пользователя {self.user.username}"


class WidgetDataCache(models.Model):
    """Модель для кэширования данных виджетов"""
    
    widget = models.OneToOneField(
        Widget,
        on_delete=models.CASCADE,
        related_name='data_cache',
        verbose_name=_('Виджет')
    )
    data = models.JSONField(
        verbose_name=_('Данные')
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Последнее обновление')
    )
    
    class Meta:
        verbose_name = _('Кэш данных виджета')
        verbose_name_plural = _('Кэши данных виджетов')
    
    def __str__(self):
        return f"Кэш для {self.widget}"