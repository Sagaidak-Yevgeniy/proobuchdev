from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from users.models import CustomUser
from courses.models import Course


class StudentGoal(models.Model):
    """Модель для образовательных целей студентов"""
    
    TYPE_CHOICES = [
        ('course_completion', 'Завершение курса'),
        ('certificate', 'Получение сертификата'),
        ('skill', 'Приобретение навыка'),
        ('career', 'Карьерная цель'),
        ('custom', 'Пользовательская цель'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]
    
    title = models.CharField(
        max_length=255,
        verbose_name=_('Название')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='goals',
        verbose_name=_('Пользователь')
    )
    goal_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='custom',
        verbose_name=_('Тип цели')
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=_('Приоритет')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Срок выполнения')
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
        verbose_name=_('Прогресс выполнения'),
        help_text=_('Процент выполнения от 0 до 100')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='goals',
        verbose_name=_('Связанный курс')
    )
    
    class Meta:
        verbose_name = _('Цель студента')
        verbose_name_plural = _('Цели студентов')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Обновляет дату выполнения при изменении статуса цели"""
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed and self.completed_at:
            self.completed_at = None
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Проверяет, просрочена ли цель"""
        if not self.due_date or self.is_completed:
            return False
        return timezone.now().date() > self.due_date
    
    @property
    def days_left(self):
        """Возвращает количество дней до дедлайна"""
        if not self.due_date or self.is_completed:
            return None
        delta = self.due_date - timezone.now().date()
        return delta.days


class GoalStep(models.Model):
    """Модель для шагов выполнения цели"""
    
    goal = models.ForeignKey(
        StudentGoal,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name=_('Цель')
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Название')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    order = models.PositiveSmallIntegerField(
        default=0,
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
    
    class Meta:
        verbose_name = _('Шаг цели')
        verbose_name_plural = _('Шаги целей')
        ordering = ['goal', 'order']
    
    def __str__(self):
        return f"{self.goal.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        """Обновляет дату выполнения при изменении статуса шага"""
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed and self.completed_at:
            self.completed_at = None
        super().save(*args, **kwargs)
        
        # Обновляем прогресс цели
        self.update_goal_progress()
    
    def update_goal_progress(self):
        """Обновляет прогресс выполнения цели на основе выполненных шагов"""
        goal = self.goal
        total_steps = goal.steps.count()
        if total_steps > 0:
            completed_steps = goal.steps.filter(is_completed=True).count()
            goal.progress = int((completed_steps / total_steps) * 100)
            if goal.progress == 100 and not goal.is_completed:
                goal.is_completed = True
            goal.save(update_fields=['progress', 'is_completed'])