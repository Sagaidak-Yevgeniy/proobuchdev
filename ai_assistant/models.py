from django.db import models
from django.utils import timezone
from users.models import CustomUser
from courses.models import Course
from lessons.models import Lesson
from assignments.models import Assignment


class ChatSession(models.Model):
    """Модель сессии чата с AI-ассистентом"""
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
        verbose_name='Пользователь'
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_sessions',
        verbose_name='Курс'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_sessions',
        verbose_name='Урок'
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_sessions',
        verbose_name='Задание'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлена')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    
    class Meta:
        verbose_name = 'Сессия чата'
        verbose_name_plural = 'Сессии чата'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def get_context_dict(self):
        """Возвращает контекст сессии в виде словаря для использования в AI-запросах"""
        context = {}
        
        if self.course:
            context['course_title'] = self.course.title
            context['course_description'] = self.course.description
        
        if self.lesson:
            context['lesson_title'] = self.lesson.title
            context['lesson_content'] = self.lesson.get_content_text()
        
        if self.assignment:
            context['assignment'] = self.assignment.task_description
            context['initial_code'] = self.assignment.initial_code
        
        return context


class ChatMessage(models.Model):
    """Модель сообщения в чате с AI-ассистентом"""
    
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('assistant', 'Ассистент'),
        ('system', 'Система'),
    ]
    
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Сессия'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name='Роль'
    )
    content = models.TextField(verbose_name='Содержание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    
    class Meta:
        verbose_name = 'Сообщение чата'
        verbose_name_plural = 'Сообщения чата'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}..."


class CodeSnippet(models.Model):
    """Модель сниппета кода, используемого в беседе с ассистентом"""
    
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('csharp', 'C#'),
        ('cpp', 'C++'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
        ('go', 'Go'),
        ('swift', 'Swift'),
        ('kotlin', 'Kotlin'),
        ('sql', 'SQL'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('other', 'Другой'),
    ]
    
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='code_snippets',
        verbose_name='Сообщение'
    )
    code = models.TextField(verbose_name='Код')
    language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        default='python',
        verbose_name='Язык'
    )
    line_start = models.PositiveIntegerField(default=1, verbose_name='Начальная строка')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    
    class Meta:
        verbose_name = 'Сниппет кода'
        verbose_name_plural = 'Сниппеты кода'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Код на {self.get_language_display()} в сообщении {self.message.id}"


class AIFeedback(models.Model):
    """Модель обратной связи от пользователя о работе AI-ассистента"""
    
    RATING_CHOICES = [
        (1, '1 - Очень плохо'),
        (2, '2 - Плохо'),
        (3, '3 - Удовлетворительно'),
        (4, '4 - Хорошо'),
        (5, '5 - Отлично'),
    ]
    
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='feedback',
        verbose_name='Сообщение'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='ai_feedback',
        verbose_name='Пользователь'
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name='Оценка'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    
    class Meta:
        verbose_name = 'Обратная связь'
        verbose_name_plural = 'Обратная связь'
        ordering = ['-created_at']
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"Оценка {self.rating} от {self.user.username}"