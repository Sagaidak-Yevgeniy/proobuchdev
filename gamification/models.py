from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser


class Achievement(models.Model):
    """Модель достижения"""
    
    TYPE_CHOICES = [
        ('course', 'Курс'),
        ('lesson', 'Урок'),
        ('assignment', 'Задание'),
        ('code', 'Код'),
        ('forum', 'Форум'),
        ('activity', 'Активность'),
        ('special', 'Особое'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Простое'),
        ('medium', 'Среднее'),
        ('hard', 'Сложное'),
        ('expert', 'Экспертное'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    icon = models.ImageField(upload_to='achievements/', blank=True, verbose_name='Иконка')
    points = models.PositiveIntegerField(default=10, verbose_name='Очки')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='activity', verbose_name='Тип')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='easy', verbose_name='Сложность')
    is_hidden = models.BooleanField(default=False, verbose_name='Скрытое достижение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'
        ordering = ['type', 'difficulty', 'name']
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """Модель полученного пользователем достижения"""
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='achievements',
        verbose_name='Пользователь'
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name='Достижение'
    )
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата получения')
    
    class Meta:
        verbose_name = 'Достижение пользователя'
        verbose_name_plural = 'Достижения пользователей'
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class Badge(models.Model):
    """Модель значка"""
    
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    icon = models.ImageField(upload_to='badges/', blank=True, verbose_name='Иконка')
    required_points = models.PositiveIntegerField(default=100, verbose_name='Требуемые очки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Значок'
        verbose_name_plural = 'Значки'
        ordering = ['required_points', 'name']
    
    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """Модель полученного пользователем значка"""
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name='Пользователь'
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name='Значок'
    )
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата получения')
    
    class Meta:
        verbose_name = 'Значок пользователя'
        verbose_name_plural = 'Значки пользователей'
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class PointsHistory(models.Model):
    """История начисления очков"""
    
    ACTION_CHOICES = [
        ('achievement', 'Достижение'),
        ('assignment', 'Выполнение задания'),
        ('streak', 'Streak бонус'),
        ('login', 'Вход на платформу'),
        ('forum', 'Активность на форуме'),
        ('help', 'Помощь другим пользователям'),
        ('admin', 'Административное действие'),
        ('other', 'Другое'),
    ]
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='points_history',
        verbose_name='Пользователь'
    )
    points = models.IntegerField(verbose_name='Очки')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='other', verbose_name='Действие')
    description = models.CharField(max_length=255, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    
    class Meta:
        verbose_name = 'История очков'
        verbose_name_plural = 'История очков'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.points} - {self.get_action_display()}"