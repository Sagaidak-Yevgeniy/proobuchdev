from django.db import models
from users.models import CustomUser
from lessons.models import LessonContent
from django.urls import reverse

class Assignment(models.Model):
    """Модель задания"""
    
    lesson_content = models.OneToOneField(
        LessonContent,
        on_delete=models.CASCADE,
        related_name='assignment',
        verbose_name='Содержимое урока'
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    task_description = models.TextField(blank=True, verbose_name='Описание задания')
    initial_code = models.TextField(blank=True, verbose_name='Начальный код')
    is_public = models.BooleanField(default=True, verbose_name='Публичное задание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('assignment_detail', kwargs={'pk': self.pk})
    
    def get_submission_count(self):
        """Возвращает количество отправленных решений для этого задания"""
        return self.submissions.count()
    
    def get_success_rate(self):
        """Возвращает процент успешных решений"""
        total = self.submissions.count()
        if total == 0:
            return 0
        
        successful = self.submissions.filter(status='passed').count()
        return round((successful / total) * 100, 1)

class TestCase(models.Model):
    """Модель тестового случая для задания"""
    
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='test_cases',
        verbose_name='Задание'
    )
    input_data = models.TextField(blank=True, verbose_name='Входные данные')
    expected_output = models.TextField(verbose_name='Ожидаемый результат')
    is_hidden = models.BooleanField(default=False, verbose_name='Скрытый тест')
    
    class Meta:
        verbose_name = 'Тестовый случай'
        verbose_name_plural = 'Тестовые случаи'
    
    def __str__(self):
        return f'Тест для {self.assignment.title}'

class AssignmentSubmission(models.Model):
    """Модель отправки решения задания"""
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает проверки'),
        ('checking', 'Проверяется'),
        ('passed', 'Успешно'),
        ('failed', 'Неуспешно'),
        ('error', 'Ошибка')
    ]
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Пользователь'
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Задание'
    )
    code = models.TextField(verbose_name='Код решения')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    score = models.FloatField(default=0, verbose_name='Оценка')
    feedback = models.TextField(blank=True, verbose_name='Обратная связь')
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')
    
    class Meta:
        verbose_name = 'Отправленное решение'
        verbose_name_plural = 'Отправленные решения'
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.assignment.title}'
    
    def get_absolute_url(self):
        return reverse('submission_detail', kwargs={'pk': self.pk})
    
    def is_passed(self):
        return self.status == 'passed'
