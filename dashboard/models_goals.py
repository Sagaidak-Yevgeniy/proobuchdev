from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, date

from users.models import CustomUser


class StudentGoal(models.Model):
    """Модель для целей студента"""
    
    GOAL_TYPE_CHOICES = [
        ('course', 'Прохождение курса'),
        ('exam', 'Подготовка к экзамену'),
        ('skill', 'Изучение навыка'),
        ('project', 'Выполнение проекта'),
        ('custom', 'Другое'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', 'Высокий'),
        ('medium', 'Средний'),
        ('low', 'Низкий'),
    ]
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='goals',
        verbose_name=_('Пользователь')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_('Название')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    goal_type = models.CharField(
        max_length=20,
        choices=GOAL_TYPE_CHOICES,
        default='custom',
        verbose_name=_('Тип цели')
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=_('Приоритет')
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Срок выполнения')
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_goals',
        verbose_name=_('Курс')
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name=_('Выполнена')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата выполнения')
    )
    progress = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_('Прогресс')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Создана')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Обновлена')
    )
    
    class Meta:
        verbose_name = _('Цель студента')
        verbose_name_plural = _('Цели студентов')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.user.username})"
    
    def save(self, *args, **kwargs):
        """Переопределяем метод сохранения для обновления прогресса и даты выполнения"""
        # Если цель отмечена как выполненная, но дата выполнения не установлена
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
            self.progress = 100
        
        # Если цель отмечена как невыполненная, сбрасываем дату выполнения
        if not self.is_completed and self.completed_at:
            self.completed_at = None
        
        # Если есть шаги, считаем прогресс на основе выполненных шагов
        if not self.is_completed and self.pk:  # Только для существующих объектов
            steps_count = self.steps.count()
            if steps_count > 0:
                completed_steps = self.steps.filter(is_completed=True).count()
                self.progress = int((completed_steps / steps_count) * 100)
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Проверяет, просрочена ли цель"""
        if not self.due_date or self.is_completed:
            return False
        return self.due_date < date.today()
    
    @property
    def days_left(self):
        """Возвращает количество дней до срока выполнения"""
        if not self.due_date:
            return None
        delta = self.due_date - date.today()
        return delta.days


class GoalStep(models.Model):
    """Модель для шагов к достижению цели"""
    
    goal = models.ForeignKey(
        StudentGoal,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name=_('Цель')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_('Название')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    order = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_('Порядок')
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name=_('Выполнен')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата выполнения')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Создан')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Обновлен')
    )
    
    class Meta:
        verbose_name = _('Шаг к цели')
        verbose_name_plural = _('Шаги к целям')
        ordering = ['goal', 'order']
    
    def __str__(self):
        return f"{self.title} ({self.goal.title})"
    
    def save(self, *args, **kwargs):
        """Переопределяем метод сохранения для обновления даты выполнения и прогресса цели"""
        # Если шаг отмечен как выполненный, но дата выполнения не установлена
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        
        # Если шаг отмечен как невыполненный, сбрасываем дату выполнения
        if not self.is_completed and self.completed_at:
            self.completed_at = None
        
        super().save(*args, **kwargs)
        
        # Обновляем прогресс цели
        self.goal.save()