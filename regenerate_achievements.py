#!/usr/bin/env python
"""
Скрипт для пересчета и выдачи достижений пользователям на основе
их текущих активностей и прогресса.
"""

import os
import django
import sys

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_platform.settings')
django.setup()

from django.db.models import Count
from users.models import CustomUser
from lessons.models import LessonCompletion, Lesson
from courses.models import Enrollment, Course
from gamification.models import Achievement, UserAchievement, Badge, UserBadge


def clear_achievements(user=None):
    """Очищает все достижения пользователя или всех пользователей."""
    if user:
        UserAchievement.objects.filter(user=user).delete()
        print(f"Достижения пользователя {user.username} удалены.")
    else:
        UserAchievement.objects.all().delete()
        print("Достижения всех пользователей удалены.")


def check_lesson_achievements(user):
    """Проверяет и выдает достижения за завершенные уроки."""
    # Подсчитываем завершенные уроки
    completed_lessons = LessonCompletion.objects.filter(user=user, completed=True)
    completed_count = completed_lessons.count()
    
    # Проверяем первый урок
    if completed_count >= 1:
        achievement = Achievement.objects.filter(name__iexact='Первый урок').first()
        if achievement:
            achievement_created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )[1]
            if achievement_created:
                print(f"Выдано достижение '{achievement.name}' пользователю {user.username}")
    
    # Проверяем, сколько уроков завершено в каждом курсе
    for course in Course.objects.all():
        completed_in_course = completed_lessons.filter(lesson__course=course).count()
        total_in_course = Lesson.objects.filter(course=course).count()
        
        if completed_in_course >= 5:
            achievement = Achievement.objects.filter(name__iexact='Настойчивый ученик').first()
            if achievement:
                achievement_created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )[1]
                if achievement_created:
                    print(f"Выдано достижение '{achievement.name}' пользователю {user.username}")
        
        if completed_in_course >= 10:
            achievement = Achievement.objects.filter(name__iexact='Эксперт по урокам').first()
            if achievement:
                achievement_created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )[1]
                if achievement_created:
                    print(f"Выдано достижение '{achievement.name}' пользователю {user.username}")
        
        # Проверяем завершение всего курса
        if total_in_course > 0 and completed_in_course == total_in_course:
            achievement = Achievement.objects.filter(name__iexact='Мастер курсов').first()
            if achievement:
                achievement_created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )[1]
                if achievement_created:
                    print(f"Выдано достижение '{achievement.name}' пользователю {user.username}")


def check_course_achievements(user):
    """Проверяет и выдает достижения за записанные курсы."""
    # Подсчитываем, на сколько курсов записан пользователь
    enrollment_count = Enrollment.objects.filter(user=user).count()
    
    # Проверяем первую запись на курс
    if enrollment_count >= 1:
        achievement = Achievement.objects.filter(name__iexact='Первый курс').first()
        if achievement:
            achievement_created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )[1]
            if achievement_created:
                print(f"Выдано достижение '{achievement.name}' пользователю {user.username}")
    
    # Проверяем запись на 3 и более курсов
    if enrollment_count >= 3:
        achievement = Achievement.objects.filter(name__iexact='Исследователь').first()
        if achievement:
            achievement_created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )[1]
            if achievement_created:
                print(f"Выдано достижение '{achievement.name}' пользователю {user.username}")


def regenerate_achievements(username=None):
    """Пересчитывает достижения для пользователя или всех пользователей."""
    users = [CustomUser.objects.get(username=username)] if username else CustomUser.objects.all()
    
    for user in users:
        print(f"\nПересчет достижений для пользователя {user.username}...")
        
        # Очищаем предыдущие достижения
        clear_achievements(user)
        
        # Проверяем достижения за завершенные уроки
        check_lesson_achievements(user)
        
        # Проверяем достижения за курсы
        check_course_achievements(user)
        
        print(f"Пересчет достижений для {user.username} завершен.\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        username = sys.argv[1]
        print(f"Запуск пересчета достижений для пользователя {username}")
        regenerate_achievements(username)
    else:
        print("Запуск пересчета достижений для всех пользователей")
        regenerate_achievements()
    
    print("Пересчет достижений успешно завершен!")