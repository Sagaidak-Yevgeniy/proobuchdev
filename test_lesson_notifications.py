#!/usr/bin/env python
"""
Скрипт для тестирования отправки уведомлений о новых и обновленных уроках
"""

import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_platform.settings')
django.setup()

from courses.models import Course, Enrollment
from lessons.models import Lesson
from users.models import CustomUser
from notifications.models import Notification
from django.utils import timezone

# Функция для создания тестового урока
def create_test_lesson(course, title, description, is_published=False):
    # Определяем порядковый номер для нового урока
    max_order = Lesson.objects.filter(course=course).aggregate(django.db.models.Max('order'))['order__max'] or 0
    
    # Создаем новый урок
    lesson = Lesson(
        course=course,
        title=title,
        description=description,
        order=max_order + 1,
        is_published=is_published
    )
    lesson.save()
    print(f"Создан новый урок: {lesson.title} (опубликован: {lesson.is_published})")
    return lesson

# Функция для обновления урока
def update_lesson(lesson, title=None, description=None, is_published=None):
    if title:
        lesson.title = title
    if description:
        lesson.description = description
    if is_published is not None:
        lesson.is_published = is_published
    
    lesson.save()
    print(f"Обновлен урок: {lesson.title} (опубликован: {lesson.is_published})")
    return lesson

# Функция для вывода уведомлений для пользователя
def print_user_notifications(user, notification_type=None):
    query = Notification.objects.filter(user=user).order_by('-created_at')
    if notification_type:
        query = query.filter(notification_type=notification_type)
    
    notifications = query[:10]  # Последние 10 уведомлений
    
    print(f"\nПоследние уведомления пользователя {user.username}:")
    if notifications.exists():
        for n in notifications:
            print(f"- {n.title}: {n.message} (создано: {n.created_at})")
    else:
        print("Уведомлений нет")

# Выполняем тестирование
def run_test():
    # Находим опубликованный курс
    course = Course.objects.filter(is_published=True).first()
    if not course:
        print("Нет опубликованных курсов. Тестирование невозможно.")
        return
    
    print(f"Тестируем на курсе: {course.title}")
    
    # Находим пользователя, записанного на курс
    enrollment = Enrollment.objects.filter(course=course).first()
    if not enrollment:
        print("Нет пользователей, записанных на курс. Тестирование невозможно.")
        return
    
    user = enrollment.user
    print(f"Тестируем для пользователя: {user.username}")
    
    # Проверяем текущие уведомления
    print_user_notifications(user, 'lesson')
    
    # 1. Создаем новый урок (неопубликованный)
    lesson1 = create_test_lesson(
        course, 
        f"Тестовый урок 1 - {timezone.now().strftime('%H:%M:%S')}", 
        "Это тестовый урок для проверки уведомлений",
        is_published=False
    )
    
    # Ждем, чтобы уведомление успело создаться
    time.sleep(1)
    
    # Проверяем, появилось ли уведомление о новом уроке
    print_user_notifications(user, 'lesson')
    
    # 2. Создаем новый урок (опубликованный)
    lesson2 = create_test_lesson(
        course, 
        f"Тестовый урок 2 - {timezone.now().strftime('%H:%M:%S')}", 
        "Это опубликованный тестовый урок для проверки уведомлений",
        is_published=True
    )
    
    # Ждем, чтобы уведомление успело создаться
    time.sleep(1)
    
    # Проверяем, появилось ли уведомление о новом уроке
    print_user_notifications(user, 'lesson')
    
    # 3. Обновляем существующий урок: меняем название
    update_lesson(
        lesson1, 
        title=f"Обновленный урок 1 - {timezone.now().strftime('%H:%M:%S')}"
    )
    
    # Ждем, чтобы уведомление успело создаться
    time.sleep(1)
    
    # Проверяем, появилось ли уведомление об обновлении
    print_user_notifications(user, 'lesson')
    
    # 4. Публикуем урок, который ранее не был опубликован
    update_lesson(lesson1, is_published=True)
    
    # Ждем, чтобы уведомление успело создаться
    time.sleep(1)
    
    # Проверяем, появилось ли уведомление о публикации
    print_user_notifications(user, 'lesson')
    
    print("\nТестирование завершено!")

if __name__ == "__main__":
    run_test()