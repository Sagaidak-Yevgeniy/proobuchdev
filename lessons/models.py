from django.db import models
from users.models import CustomUser
from courses.models import Course
from django.urls import reverse

class Lesson(models.Model):
    """Модель урока в курсе"""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Курс'
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    order = models.PositiveIntegerField(default=1, verbose_name='Порядок отображения')
    is_published = models.BooleanField(default=False, verbose_name='Опубликован')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f'{self.course.title} - {self.title}'
    
    def get_absolute_url(self):
        return reverse('lesson_detail', kwargs={'pk': self.pk})
    
    def get_next_lesson(self):
        """Возвращает следующий урок в курсе"""
        next_lessons = Lesson.objects.filter(
            course=self.course,
            order__gt=self.order
        ).order_by('order')
        
        return next_lessons.first() if next_lessons.exists() else None
    
    def get_previous_lesson(self):
        """Возвращает предыдущий урок в курсе"""
        prev_lessons = Lesson.objects.filter(
            course=self.course,
            order__lt=self.order
        ).order_by('-order')
        
        return prev_lessons.first() if prev_lessons.exists() else None

class LessonContent(models.Model):
    """Модель содержимого урока"""
    
    CONTENT_TYPES = [
        ('text', 'Текст'),
        ('code', 'Код'),
        ('video', 'Видео'),
        ('assignment', 'Задание'),
    ]
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='contents',
        verbose_name='Урок'
    )
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPES,
        verbose_name='Тип содержимого'
    )
    content = models.TextField(blank=True, verbose_name='Содержимое')
    video_url = models.URLField(blank=True, verbose_name='Ссылка на видео')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Содержимое урока'
        verbose_name_plural = 'Содержимое уроков'
        ordering = ['lesson', 'id']
    
    def __str__(self):
        return f'{self.lesson.title} - {self.get_content_type_display()}'
    
    def is_assignment(self):
        return self.content_type == 'assignment'

class LessonCompletion(models.Model):
    """Модель для отслеживания завершения уроков пользователями"""
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='completed_lessons',
        verbose_name='Пользователь'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='completions',
        verbose_name='Урок'
    )
    completed = models.BooleanField(default=False, verbose_name='Завершен')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата завершения')
    
    class Meta:
        verbose_name = 'Завершение урока'
        verbose_name_plural = 'Завершения уроков'
        unique_together = ['user', 'lesson']
    
    def __str__(self):
        status = 'завершен' if self.completed else 'не завершен'
        return f'{self.user.username} - {self.lesson.title} ({status})'
