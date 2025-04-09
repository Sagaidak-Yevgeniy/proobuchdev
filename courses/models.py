from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from users.models import CustomUser
from django.utils.translation import gettext_lazy as _

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
        if self.progress >= 100:
            self.is_completed = True
        self.save()
