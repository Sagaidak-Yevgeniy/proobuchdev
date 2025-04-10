from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
from users.models import CustomUser
from django.utils.translation import gettext_lazy as _

# Импортируем модели из models_certificates.py для связи
from .models_certificates import Certificate, CertificateTemplate

class Category(models.Model):
    """Модель категории курсов"""
    
    name = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

class Course(models.Model):
    """Модель курса"""
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Начальный'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый'),
        ('expert', 'Экспертный'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(max_length=250, unique=True, verbose_name='Slug')
    description = models.TextField(verbose_name='Описание')
    author = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name='Автор'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='Категория'
    )
    cover_image = models.ImageField(
        upload_to='course_covers/',
        blank=True,
        null=True,
        verbose_name='Обложка курса'
    )
    is_published = models.BooleanField(default=False, verbose_name='Опубликован')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    # Поля для сертификатов
    enable_certificates = models.BooleanField(
        default=True, 
        verbose_name='Выдавать сертификаты'
    )
    min_points_for_certificate = models.PositiveIntegerField(
        default=70, 
        verbose_name='Минимальный балл для сертификата',
        help_text='Минимальное количество баллов, необходимое для получения сертификата'
    )
    certificate_template = models.ForeignKey(
        'CertificateTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='Шаблон сертификата'
    )
    
    # Дополнительные метаданные
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='beginner',
        verbose_name='Уровень сложности'
    )
    duration_hours = models.PositiveIntegerField(
        default=0, 
        verbose_name='Продолжительность (часы)',
        help_text='Оценочная продолжительность курса в часах'
    )
    tags = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Теги',
        help_text='Теги курса, разделенные запятыми'
    )
    
    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'slug': self.slug})
    
    def enrolled_students_count(self):
        return self.enrollments.count()
    
    def lessons_count(self):
        return self.lessons.count()
        
    def can_generate_certificate(self, user):
        """Проверяет, может ли пользователь получить сертификат"""
        if not self.enable_certificates:
            return False
            
        # Проверяем, записан ли пользователь на курс
        enrollment = self.enrollments.filter(user=user).first()
        if not enrollment:
            return False
            
        # Проверяем завершение курса
        completion = CourseCompletion.objects.filter(user=user, course=self).exists()
        if not completion:
            return False
            
        # Считаем баллы
        from assignments.models import AssignmentSubmission
        earned_points = AssignmentSubmission.objects.filter(
            user=user,
            assignment__lesson__course=self,
            status='approved'
        ).aggregate(models.Sum('points'))['points__sum'] or 0
        
        # Максимально возможные баллы
        from lessons.models import Assignment
        max_points = Assignment.objects.filter(
            lesson__course=self
        ).aggregate(models.Sum('max_points'))['max_points__sum'] or 0
        
        if max_points == 0:
            return False
            
        # Проверяем, набрал ли пользователь минимальный процент баллов
        percentage = (earned_points / max_points) * 100
        return percentage >= self.min_points_for_certificate

class Enrollment(models.Model):
    """Модель зачисления пользователя на курс"""
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Пользователь'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Курс'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата зачисления')
    is_completed = models.BooleanField(default=False, verbose_name='Завершен')
    progress = models.FloatField(default=0, verbose_name='Прогресс')
    
    class Meta:
        verbose_name = 'Зачисление'
        verbose_name_plural = 'Зачисления'
        unique_together = ('user', 'course')
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.course.title}'
    
    def update_progress(self):
        """Обновляет прогресс прохождения курса на основе выполненных заданий"""
        from lessons.models import LessonCompletion
        
        total_lessons = self.course.lessons.count()
        if total_lessons == 0:
            self.progress = 0
            return
        
        completed_lessons = LessonCompletion.objects.filter(
            user=self.user,
            lesson__course=self.course,
            completed=True
        ).count()
        
        self.progress = (completed_lessons / total_lessons) * 100
        
        # Если прогресс 100% и курс не был ранее отмечен как завершенный,
        # создаем запись о завершении курса
        if self.progress >= 100:
            self.is_completed = True
            # Создаем запись о завершении курса, если ее еще нет
            CourseCompletion.objects.get_or_create(
                user=self.user,
                course=self.course,
                defaults={'completion_date': timezone.now()}
            )
        self.save()


class CourseCompletion(models.Model):
    """Модель завершения курса пользователем"""
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='completed_courses',
        verbose_name='Пользователь'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='completions',
        verbose_name='Курс'
    )
    completion_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата завершения'
    )
    earned_points = models.PositiveIntegerField(
        default=0,
        verbose_name='Набранные баллы'
    )
    max_points = models.PositiveIntegerField(
        default=0,
        verbose_name='Максимальные баллы'
    )
    percentage = models.FloatField(
        default=0,
        verbose_name='Процент выполнения'
    )
    feedback = models.TextField(
        blank=True,
        verbose_name='Отзыв о курсе'
    )
    rating = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Оценка курса (0-5)',
        help_text='Оценка курса пользователем от 0 до 5'
    )
    certificate_generated = models.BooleanField(
        default=False,
        verbose_name='Сертификат выдан'
    )
    
    class Meta:
        verbose_name = 'Завершение курса'
        verbose_name_plural = 'Завершения курсов'
        unique_together = ('user', 'course')
        ordering = ['-completion_date']
    
    def __str__(self):
        return f'{self.user.username} завершил курс {self.course.title}'
    
    def save(self, *args, **kwargs):
        # Обновляем баллы при сохранении
        self.update_points()
        super().save(*args, **kwargs)
    
    def update_points(self):
        """Обновляет информацию о баллах за курс"""
        from assignments.models import AssignmentSubmission
        
        # Подсчет набранных баллов
        earned_points = AssignmentSubmission.objects.filter(
            user=self.user,
            assignment__lesson__course=self.course,
            status='approved'
        ).aggregate(models.Sum('points'))['points__sum'] or 0
        
        # Подсчет максимально возможных баллов
        from lessons.models import Assignment
        max_points = Assignment.objects.filter(
            lesson__course=self.course
        ).aggregate(models.Sum('max_points'))['max_points__sum'] or 0
        
        self.earned_points = earned_points
        self.max_points = max_points
        
        if max_points > 0:
            self.percentage = (earned_points / max_points) * 100
        else:
            self.percentage = 0
