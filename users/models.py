from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    """Расширенная модель пользователя"""
    
    email = models.EmailField(_('email address'), unique=True)
    
    def __str__(self):
        return self.username
    
    def get_absolute_url(self):
        return reverse('profile', kwargs={'username': self.username})

class Profile(models.Model):
    """Модель профиля пользователя"""
    
    STUDENT = 'student'
    TEACHER = 'teacher'
    ADMIN = 'admin'
    
    ROLES = [
        (STUDENT, 'Ученик'),
        (TEACHER, 'Преподаватель'),
        (ADMIN, 'Администратор'),
    ]
    
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLES,
        default=STUDENT,
        verbose_name='Роль'
    )
    bio = models.TextField(
        blank=True,
        verbose_name='О себе'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Фотография профиля'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
        
    def __str__(self):
        return f'Профиль пользователя {self.user.username}'
    
    def is_teacher(self):
        """Проверяет, является ли пользователь преподавателем или администратором"""
        return self.role in [self.TEACHER, self.ADMIN]
    
    def is_admin(self):
        """Проверяет, является ли пользователь администратором"""
        return self.role == self.ADMIN


class UserInterface(models.Model):
    """Модель для хранения настроек интерфейса пользователя"""
    
    THEME_LIGHT = 'light'
    THEME_DARK = 'dark'
    THEME_AUTO = 'auto'
    
    THEME_CHOICES = [
        (THEME_LIGHT, 'Светлая тема'),
        (THEME_DARK, 'Темная тема'),
        (THEME_AUTO, 'Системная настройка'),
    ]
    
    FONT_SMALL = 'small'
    FONT_MEDIUM = 'medium'
    FONT_LARGE = 'large'
    
    FONT_SIZE_CHOICES = [
        (FONT_SMALL, 'Мелкий шрифт'),
        (FONT_MEDIUM, 'Средний шрифт'),
        (FONT_LARGE, 'Крупный шрифт'),
    ]
    
    LAYOUT_DEFAULT = 'default'
    LAYOUT_COMPACT = 'compact'
    LAYOUT_WIDE = 'wide'
    
    LAYOUT_CHOICES = [
        (LAYOUT_DEFAULT, 'Стандартный макет'),
        (LAYOUT_COMPACT, 'Компактный макет'),
        (LAYOUT_WIDE, 'Широкий макет'),
    ]
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='interface',
        verbose_name='Пользователь'
    )
    
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default=THEME_LIGHT,
        verbose_name='Тема оформления'
    )
    
    font_size = models.CharField(
        max_length=10,
        choices=FONT_SIZE_CHOICES,
        default=FONT_MEDIUM,
        verbose_name='Размер шрифта'
    )
    
    layout = models.CharField(
        max_length=10,
        choices=LAYOUT_CHOICES,
        default=LAYOUT_DEFAULT,
        verbose_name='Макет интерфейса'
    )
    
    enable_animations = models.BooleanField(
        default=True,
        verbose_name='Включить анимации'
    )
    
    high_contrast = models.BooleanField(
        default=False,
        verbose_name='Высокий контраст'
    )
    
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Последнее обновление'
    )
    
    class Meta:
        verbose_name = 'Настройки интерфейса'
        verbose_name_plural = 'Настройки интерфейса'
    
    def __str__(self):
        return f'Настройки интерфейса пользователя {self.user.username}'
