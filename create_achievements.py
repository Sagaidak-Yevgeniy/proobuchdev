#!/usr/bin/env python
"""
Скрипт для создания достижений и значков в системе геймификации.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_platform.settings')
django.setup()

from gamification.models import Achievement, Badge

# Добавляем достижения, связанные с курсами и уроками
achievements_data = [
    # Достижения для курсов
    {
        'name': 'Первый курс',
        'description': 'Записаться на первый курс',
        'points': 10,
        'type': 'course',
        'difficulty': 'easy',
        'is_hidden': False
    },
    {
        'name': 'Исследователь',
        'description': 'Записаться на 3 разных курса',
        'points': 20,
        'type': 'course',
        'difficulty': 'medium',
        'is_hidden': False
    },
    {
        'name': 'Мастер курсов',
        'description': 'Полностью пройти курс от начала до конца',
        'points': 50,
        'type': 'course',
        'difficulty': 'hard',
        'is_hidden': False
    },
    
    # Достижения для уроков
    {
        'name': 'Первый урок',
        'description': 'Завершить первый урок',
        'points': 5,
        'type': 'lesson',
        'difficulty': 'easy',
        'is_hidden': False
    },
    {
        'name': 'Настойчивый ученик',
        'description': 'Завершить 5 уроков в одном курсе',
        'points': 15,
        'type': 'lesson',
        'difficulty': 'medium',
        'is_hidden': False
    },
    {
        'name': 'Эксперт по урокам',
        'description': 'Завершить 10 уроков в одном курсе',
        'points': 30,
        'type': 'lesson',
        'difficulty': 'hard',
        'is_hidden': False
    },
    
    # Достижения для активности
    {
        'name': 'Ежедневная учеба',
        'description': 'Заходить на платформу 5 дней подряд',
        'points': 15,
        'type': 'activity',
        'difficulty': 'medium',
        'is_hidden': False
    },
    {
        'name': 'Ночной учебный марафон',
        'description': 'Учиться после 23:00',
        'points': 10,
        'type': 'activity',
        'difficulty': 'easy',
        'is_hidden': True
    }
]

# Добавляем значки для геймификации
badges_data = [
    {
        'name': 'Новичок',
        'description': 'Набрать 20 очков',
        'required_points': 20
    },
    {
        'name': 'Ученик',
        'description': 'Набрать 50 очков',
        'required_points': 50
    },
    {
        'name': 'Студент',
        'description': 'Набрать 100 очков',
        'required_points': 100
    },
    {
        'name': 'Бакалавр',
        'description': 'Набрать 200 очков',
        'required_points': 200
    },
    {
        'name': 'Магистр',
        'description': 'Набрать 500 очков',
        'required_points': 500
    },
    {
        'name': 'Профессор',
        'description': 'Набрать 1000 очков',
        'required_points': 1000
    }
]

# Создаем достижения
print("Создаем достижения:")
for data in achievements_data:
    achievement, created = Achievement.objects.get_or_create(
        name=data['name'],
        defaults=data
    )
    if created:
        print(f"+ Создано: {achievement.name}")
    else:
        # Обновляем существующие достижения, если нужно
        for key, value in data.items():
            setattr(achievement, key, value)
        achievement.save()
        print(f"~ Обновлено: {achievement.name}")

# Создаем значки
print("\nСоздаем значки:")
for data in badges_data:
    badge, created = Badge.objects.get_or_create(
        name=data['name'],
        defaults=data
    )
    if created:
        print(f"+ Создано: {badge.name} (необходимо {badge.required_points} очков)")
    else:
        # Обновляем существующие значки, если нужно
        for key, value in data.items():
            setattr(badge, key, value)
        badge.save()
        print(f"~ Обновлено: {badge.name} (необходимо {badge.required_points} очков)")

print("\nГотово! Создано и обновлено достижений: {} | Создано и обновлено значков: {}".format(
    len(achievements_data), len(badges_data)
))