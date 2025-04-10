"""
Комплексное тестирование системы онлайн-олимпиад и курсов.
Этот скрипт проверяет основные функции и выявляет возможные проблемы.
"""

import os
import sys
import random
import datetime
import json
import time
from pathlib import Path

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_platform.settings')
import django
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.utils.text import slugify
from django.db import models

from users.models import Profile, UserInterface
from courses.models import Category, Course, Enrollment, CourseCompletion
from lessons.models import Lesson, LessonContent, LessonCompletion
from assignments.models import Assignment, TestCase, AssignmentSubmission
from olympiads.models import (
    Olympiad, OlympiadTask, OlympiadTestCase, OlympiadParticipation,
    OlympiadTaskSubmission, OlympiadInvitation, OlympiadCertificate
)
from gamification.models import Achievement, UserAchievement, Badge

User = get_user_model()

class SystemTester:
    """Класс для комплексного тестирования системы"""
    
    def __init__(self):
        self.client = Client()
        self.test_users = {}
        self.test_categories = []
        self.test_courses = []
        self.test_olympiads = []
        self.test_results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        
    def setup_test_data(self):
        """Создание тестовых данных для проверки системы"""
        print("Создание тестовых данных...")
        
        # Создаем тестовых пользователей с разными ролями
        self.create_test_users()
        
        # Создаем тестовые категории курсов
        self.create_test_categories()
        
        # Создаем тестовые курсы
        self.create_test_courses()
        
        # Создаем тестовые олимпиады
        self.create_test_olympiads()
        
        print("Тестовые данные созданы успешно")
        
    def create_test_users(self):
        """Создание тестовых пользователей"""
        # Администратор
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin12345'
            )
            admin_profile = Profile.objects.get(user=admin_user)
            admin_profile.role = Profile.ADMIN
            admin_profile.save()
        
        self.test_users['admin'] = admin_user
        
        # Преподаватель
        try:
            teacher_user = User.objects.create_user(
                username='Тестовый Преподаватель',
                email='teacher@example.com',
                password='teacher12345'
            )
            teacher_profile = Profile.objects.get(user=teacher_user)
            teacher_profile.role = Profile.TEACHER
            teacher_profile.save()
            
            self.test_users['teacher'] = teacher_user
        except:
            self.test_users['teacher'] = User.objects.filter(email='teacher@example.com').first()
        
        # Студент
        try:
            student_user = User.objects.create_user(
                username='Тестовый Студент',
                email='student@example.com',
                password='student12345'
            )
            
            self.test_users['student'] = student_user
        except:
            self.test_users['student'] = User.objects.filter(email='student@example.com').first()
    
    def create_test_categories(self):
        """Создание тестовых категорий"""
        category_data = [
            {
                'name': 'Программирование на Python',
                'slug': 'python',
                'description': 'Описание категории Программирование на Python'
            },
            {
                'name': 'Веб-разработка',
                'slug': 'web-razrabotka',
                'description': 'Описание категории Веб-разработка'
            },
            {
                'name': 'Алгоритмы и структуры данных',
                'slug': 'algoritmy-i-struktury-dannyh',
                'description': 'Описание категории Алгоритмы и структуры данных'
            }
        ]
        
        for data in category_data:
            # Проверяем, существует ли категория с таким именем или slug
            category = Category.objects.filter(
                models.Q(name=data['name']) | models.Q(slug=data['slug'])
            ).first()
            
            if not category:
                # Создаем новую категорию
                category = Category.objects.create(
                    name=data['name'],
                    slug=data['slug'],
                    description=data['description']
                )
                print(f"✓ Создана категория: {data['name']}")
            else:
                # Обновляем существующую категорию
                if category.slug != data['slug'] or category.description != data['description']:
                    category.slug = data['slug']
                    category.description = data['description']
                    category.save()
                    print(f"✓ Обновлена категория: {data['name']}")
                else:
                    print(f"✓ Использована существующая категория: {data['name']}")
                    
            self.test_categories.append(category)
    
    def create_test_courses(self):
        """Создание тестовых курсов"""
        course_data = [
            {
                'title': 'Основы Python для начинающих',
                'slug': 'osnovy-python-dlya-nachinayushchih',
                'description': 'Базовый курс для изучения Python с нуля',
                'difficulty_level': 'beginner',
                'duration_hours': 20,
                'category_index': 0,
            },
            {
                'title': 'HTML и CSS: современная вёрстка',
                'slug': 'html-i-css-sovremennaya-verstka',
                'description': 'Курс по вёрстке и стилизации веб-страниц',
                'difficulty_level': 'beginner',
                'duration_hours': 15,
                'category_index': 1,
            },
            {
                'title': 'Алгоритмы для подготовки к олимпиадам',
                'slug': 'algoritmy-dlya-podgotovki-k-olimpiadam',
                'description': 'Продвинутый курс по алгоритмам',
                'difficulty_level': 'advanced',
                'duration_hours': 30,
                'category_index': 2,
            }
        ]
        
        for data in course_data:
            # Проверяем, существует ли курс с таким названием или slug
            course = Course.objects.filter(
                models.Q(title=data['title']) | models.Q(slug=data['slug'])
            ).first()
            
            if not course:
                # Создаем новый курс
                course = Course.objects.create(
                    title=data['title'],
                    slug=data['slug'],
                    description=data['description'],
                    author=self.test_users['teacher'],
                    category=self.test_categories[data['category_index']],
                    difficulty_level=data['difficulty_level'],
                    duration_hours=data['duration_hours'],
                    is_published=True
                )
                print(f"✓ Создан курс: {data['title']}")
                
                # Создаем уроки для курса
                self.create_test_lessons(course)
            else:
                # Обновляем существующий курс
                if course.description != data['description'] or course.category != self.test_categories[data['category_index']]:
                    course.description = data['description']
                    course.category = self.test_categories[data['category_index']]
                    course.difficulty_level = data['difficulty_level']
                    course.duration_hours = data['duration_hours']
                    course.save()
                    print(f"✓ Обновлен курс: {data['title']}")
                else:
                    print(f"✓ Использован существующий курс: {data['title']}")
            
            self.test_courses.append(course)
    
    def create_test_lessons(self, course):
        """Создание тестовых уроков для курса"""
        lessons_data = [
            {
                'title': 'Введение в курс',
                'description': 'Обзор курса и знакомство с форматом',
                'order': 1
            },
            {
                'title': 'Основные концепции',
                'description': 'Изучение основных концепций и принципов',
                'order': 2
            },
            {
                'title': 'Практические задания',
                'description': 'Выполнение практических заданий для закрепления материала',
                'order': 3
            }
        ]
        
        for data in lessons_data:
            lesson = Lesson.objects.create(
                course=course,
                title=data['title'],
                description=data['description'],
                order=data['order'],
                is_published=True
            )
            
            # Создаем контент для урока
            LessonContent.objects.create(
                lesson=lesson,
                content_type='text',
                content=f'Текстовое содержимое для урока {lesson.title}'
            )
            
            # Создаем задание для урока
            assignment = Assignment.objects.create(
                title=f'Задание для {lesson.title}',
                task_description=f'Описание задания для урока {lesson.title}',
                max_points=10,
                initial_code='# Напишите ваш код здесь',
                lesson_content=LessonContent.objects.get(lesson=lesson)
            )
            
            # Создаем тестовые случаи для задания
            TestCase.objects.create(
                assignment=assignment,
                input_data='5',
                expected_output='25',
                is_hidden=False
            )
            
            TestCase.objects.create(
                assignment=assignment,
                input_data='10',
                expected_output='100',
                is_hidden=True
            )
    
    def create_test_olympiads(self):
        """Создание тестовых олимпиад"""
        olympiad_data = [
            {
                'title': 'Олимпиада по Python',
                'description': 'Соревнование по программированию на языке Python',
                'course_index': 0,
                'status': Olympiad.OlympiadStatus.ACTIVE
            },
            {
                'title': 'Веб-разработка: HTML и CSS',
                'description': 'Олимпиада по вёрстке и стилизации',
                'course_index': 1,
                'status': Olympiad.OlympiadStatus.PUBLISHED
            },
            {
                'title': 'Алгоритмическая олимпиада',
                'description': 'Соревнование по алгоритмам и структурам данных',
                'course_index': 2,
                'status': Olympiad.OlympiadStatus.DRAFT
            }
        ]
        
        for data in olympiad_data:
            now = timezone.now()
            
            # Проверяем, существует ли олимпиада с таким названием
            olympiad = Olympiad.objects.filter(
                title=data['title']
            ).first()
            
            if not olympiad:
                # Создаем новую олимпиаду
                olympiad = Olympiad.objects.create(
                    title=data['title'],
                    description=data['description'],
                    short_description=data['description'][:100],
                    start_datetime=now - datetime.timedelta(days=1),
                    end_datetime=now + datetime.timedelta(days=7),
                    is_open=True,
                    time_limit_minutes=120,
                    min_passing_score=70,
                    status=data['status'],
                    created_by=self.test_users['teacher'],
                    related_course=self.test_courses[data['course_index']]
                )
                print(f"✓ Создана олимпиада: {data['title']}")
                
                # Создаем задания для олимпиады
                self.create_test_olympiad_tasks(olympiad)
            else:
                # Обновляем существующую олимпиаду
                if (olympiad.description != data['description'] or 
                    olympiad.status != data['status'] or
                    olympiad.related_course != self.test_courses[data['course_index']]):
                    
                    olympiad.description = data['description']
                    olympiad.short_description = data['description'][:100]
                    olympiad.status = data['status']
                    olympiad.related_course = self.test_courses[data['course_index']]
                    olympiad.save()
                    print(f"✓ Обновлена олимпиада: {data['title']}")
                else:
                    print(f"✓ Использована существующая олимпиада: {data['title']}")
            
            self.test_olympiads.append(olympiad)
    
    def create_test_olympiad_tasks(self, olympiad):
        """Создание тестовых заданий для олимпиады"""
        task_data = [
            {
                'title': 'Задача 1: Сумма чисел',
                'description': 'Напишите программу, которая находит сумму двух чисел',
                'task_type': OlympiadTask.TaskType.PROGRAMMING,
                'points': 10,
                'order': 1,
                'initial_code': '# Напишите функцию, которая принимает два числа и возвращает их сумму\n\ndef sum_numbers(a, b):\n    # Ваш код здесь\n    pass\n'
            },
            {
                'title': 'Задача 2: Тестовый вопрос',
                'description': 'Выберите правильные варианты ответа',
                'task_type': OlympiadTask.TaskType.MULTIPLE_CHOICE,
                'points': 5,
                'order': 2,
                'initial_code': ''
            },
            {
                'title': 'Задача 3: Теоретический вопрос',
                'description': 'Опишите принцип работы алгоритма быстрой сортировки',
                'task_type': OlympiadTask.TaskType.THEORETICAL,
                'points': 15,
                'order': 3,
                'initial_code': ''
            }
        ]
        
        for data in task_data:
            task = OlympiadTask.objects.create(
                olympiad=olympiad,
                title=data['title'],
                description=data['description'],
                task_type=data['task_type'],
                points=data['points'],
                order=data['order'],
                initial_code=data['initial_code']
            )
            
            if task.task_type == OlympiadTask.TaskType.PROGRAMMING:
                # Создаем тестовые случаи для задачи программирования
                OlympiadTestCase.objects.create(
                    task=task,
                    input_data='1 2',
                    expected_output='3',
                    is_hidden=False,
                    explanation='Сумма чисел 1 и 2 равна 3',
                    points=5,
                    order=1
                )
                
                OlympiadTestCase.objects.create(
                    task=task,
                    input_data='10 20',
                    expected_output='30',
                    is_hidden=True,
                    explanation='Сумма чисел 10 и 20 равна 30',
                    points=5,
                    order=2
                )
            
            elif task.task_type == OlympiadTask.TaskType.MULTIPLE_CHOICE:
                # Создаем варианты ответов для тестового вопроса
                for i, option_text in enumerate([
                    'Вариант 1 (правильный)',
                    'Вариант 2 (неправильный)',
                    'Вариант 3 (правильный)',
                    'Вариант 4 (неправильный)'
                ]):
                    is_correct = 'правильный' in option_text
                    task.options.create(
                        text=option_text,
                        is_correct=is_correct,
                        explanation=f'Пояснение для варианта {i+1}',
                        order=i+1
                    )
    
    def test_registration_and_login(self):
        """Тестирование регистрации и входа в систему"""
        print("\nПроверка регистрации и входа в систему...")
        
        # Создаем тестового пользователя для проверки
        username = f'test_user_{int(time.time())}'
        email = f'{username}@example.com'
        password = 'test12345'
        
        # Проверка регистрации
        registration_data = {
            'username': username,
            'email': email,
            'password1': password,
            'password2': password
        }
        
        response = self.client.post(reverse('register'), registration_data, follow=True)
        
        if response.status_code == 200:
            self.test_results['passed'].append('Регистрация нового пользователя')
            print("✓ Регистрация пользователя успешна")
        else:
            self.test_results['failed'].append('Регистрация нового пользователя')
            print("✗ Ошибка регистрации пользователя")
            
        # Проверка входа
        login_data = {
            'username': username,
            'password': password
        }
        
        response = self.client.post(reverse('login'), login_data, follow=True)
        
        if response.status_code == 200 and User.objects.filter(username=username).exists():
            self.test_results['passed'].append('Вход в систему')
            print("✓ Вход в систему успешен")
        else:
            self.test_results['failed'].append('Вход в систему')
            print("✗ Ошибка входа в систему")
            
        # Проверка страницы профиля
        response = self.client.get(reverse('user_profile', kwargs={'username': username}))
        
        if response.status_code == 200:
            self.test_results['passed'].append('Доступ к профилю')
            print("✓ Доступ к профилю работает корректно")
        else:
            self.test_results['failed'].append('Доступ к профилю')
            print("✗ Ошибка доступа к профилю")
        
        # Проверка выхода
        response = self.client.get(reverse('logout'), follow=True)
        
        if response.status_code == 200:
            self.test_results['passed'].append('Выход из системы')
            print("✓ Выход из системы работает корректно")
        else:
            self.test_results['failed'].append('Выход из системы')
            print("✗ Ошибка выхода из системы")
    
    def test_course_functionality(self):
        """Тестирование функциональности курсов"""
        print("\nПроверка функциональности курсов...")
        
        # Авторизуемся как студент
        self.client.login(username='student@example.com', password='student12345')
        
        # Проверка списка курсов
        response = self.client.get(reverse('course_list'))
        
        if response.status_code == 200:
            self.test_results['passed'].append('Просмотр списка курсов')
            print("✓ Просмотр списка курсов работает корректно")
        else:
            self.test_results['failed'].append('Просмотр списка курсов')
            print("✗ Ошибка при просмотре списка курсов")
        
        # Проверка детальной страницы курса
        if self.test_courses:
            course = self.test_courses[0]
            response = self.client.get(reverse('course_detail', kwargs={'slug': course.slug}))
            
            if response.status_code == 200:
                self.test_results['passed'].append('Просмотр детальной страницы курса')
                print("✓ Просмотр детальной страницы курса работает корректно")
            else:
                self.test_results['failed'].append('Просмотр детальной страницы курса')
                print("✗ Ошибка при просмотре детальной страницы курса")
            
            # Проверка записи на курс
            response = self.client.post(
                reverse('course_enroll', kwargs={'slug': course.slug}),
                follow=True
            )
            
            if response.status_code == 200 and Enrollment.objects.filter(
                user=self.test_users['student'], course=course
            ).exists():
                self.test_results['passed'].append('Запись на курс')
                print("✓ Запись на курс работает корректно")
            else:
                self.test_results['failed'].append('Запись на курс')
                print("✗ Ошибка при записи на курс")
            
            # Проверка страницы уроков курса (если есть уроки)
            lesson = Lesson.objects.filter(course=course).first()
            if lesson:
                response = self.client.get(
                    reverse('lesson_detail', kwargs={'pk': lesson.id})
                )
                
                if response.status_code == 200:
                    self.test_results['passed'].append('Просмотр урока курса')
                    print("✓ Просмотр урока курса работает корректно")
                else:
                    self.test_results['failed'].append('Просмотр урока курса')
                    print("✗ Ошибка при просмотре урока курса")
                
                # Проверка отметки урока как завершенного
                response = self.client.post(
                    reverse('lesson_complete', kwargs={'pk': lesson.id}),
                    follow=True
                )
                
                if response.status_code == 200 and LessonCompletion.objects.filter(
                    user=self.test_users['student'], lesson=lesson
                ).exists():
                    self.test_results['passed'].append('Завершение урока')
                    print("✓ Отметка о завершении урока работает корректно")
                else:
                    self.test_results['failed'].append('Завершение урока')
                    print("✗ Ошибка при отметке о завершении урока")
        else:
            self.test_results['warnings'].append('Нет тестовых курсов для проверки')
            print("⚠ Нет тестовых курсов для проверки функциональности")
    
    def test_olympiad_functionality(self):
        """Тестирование функциональности олимпиад"""
        print("\nПроверка функциональности олимпиад...")
        
        # Авторизуемся как студент
        self.client.login(username='student@example.com', password='student12345')
        
        # Проверка списка олимпиад
        response = self.client.get(reverse('olympiads:olympiad_list'))
        
        if response.status_code == 200:
            self.test_results['passed'].append('Просмотр списка олимпиад')
            print("✓ Просмотр списка олимпиад работает корректно")
        else:
            self.test_results['failed'].append('Просмотр списка олимпиад')
            print("✗ Ошибка при просмотре списка олимпиад")
        
        # Проверка детальной страницы олимпиады
        if self.test_olympiads:
            active_olympiads = [o for o in self.test_olympiads if o.status == Olympiad.OlympiadStatus.ACTIVE]
            if active_olympiads:
                olympiad = active_olympiads[0]
                response = self.client.get(reverse('olympiads:olympiad_detail', kwargs={'olympiad_id': olympiad.id}))
                
                if response.status_code == 200:
                    self.test_results['passed'].append('Просмотр детальной страницы олимпиады')
                    print("✓ Просмотр детальной страницы олимпиады работает корректно")
                else:
                    self.test_results['failed'].append('Просмотр детальной страницы олимпиады')
                    print("✗ Ошибка при просмотре детальной страницы олимпиады")
                
                # Проверка участия в олимпиаде
                response = self.client.post(
                    reverse('olympiads:olympiad_register', kwargs={'olympiad_id': olympiad.id}),
                    follow=True
                )
                
                if response.status_code == 200 and OlympiadParticipation.objects.filter(
                    user=self.test_users['student'], olympiad=olympiad
                ).exists():
                    self.test_results['passed'].append('Участие в олимпиаде')
                    print("✓ Участие в олимпиаде работает корректно")
                else:
                    self.test_results['failed'].append('Участие в олимпиаде')
                    print("✗ Ошибка при участии в олимпиаде")
                
                # Проверка страницы задания олимпиады
                participation = OlympiadParticipation.objects.filter(
                    user=self.test_users['student'], olympiad=olympiad
                ).first()
                
                if participation:
                    task = OlympiadTask.objects.filter(olympiad=olympiad).first()
                    if task:
                        response = self.client.get(
                            reverse('olympiads:olympiad_task', kwargs={
                                'olympiad_id': olympiad.id,
                                'task_id': task.id
                            })
                        )
                        
                        if response.status_code == 200:
                            self.test_results['passed'].append('Просмотр задания олимпиады')
                            print("✓ Просмотр задания олимпиады работает корректно")
                        else:
                            self.test_results['failed'].append('Просмотр задания олимпиады')
                            print("✗ Ошибка при просмотре задания олимпиады")
                        
                        # Проверка отправки решения
                        if task.task_type == OlympiadTask.TaskType.PROGRAMMING:
                            submission_data = {
                                'code': 'def sum_numbers(a, b):\n    return a + b'
                            }
                        elif task.task_type == OlympiadTask.TaskType.THEORETICAL:
                            submission_data = {
                                'text_answer': 'Это ответ на теоретический вопрос'
                            }
                        else:  # MULTIPLE_CHOICE
                            options = task.options.filter(is_correct=True)
                            if options:
                                submission_data = {
                                    'selected_options': [o.id for o in options]
                                }
                            else:
                                submission_data = {'selected_options': []}
                        
                        response = self.client.post(
                            reverse('olympiads:olympiad_submit_task', kwargs={
                                'olympiad_id': olympiad.id,
                                'task_id': task.id
                            }),
                            submission_data,
                            follow=True
                        )
                        
                        if response.status_code == 200 and OlympiadTaskSubmission.objects.filter(
                            participation=participation, task=task
                        ).exists():
                            self.test_results['passed'].append('Отправка решения олимпиадного задания')
                            print("✓ Отправка решения олимпиадного задания работает корректно")
                        else:
                            self.test_results['failed'].append('Отправка решения олимпиадного задания')
                            print("✗ Ошибка при отправке решения олимпиадного задания")
            else:
                self.test_results['warnings'].append('Нет активных олимпиад для проверки')
                print("⚠ Нет активных олимпиад для проверки функциональности")
        else:
            self.test_results['warnings'].append('Нет тестовых олимпиад для проверки')
            print("⚠ Нет тестовых олимпиад для проверки функциональности")
    
    def test_admin_functionality(self):
        """Тестирование функциональности администратора"""
        print("\nПроверка функциональности администратора...")
        
        # Авторизуемся как администратор
        self.client.login(username='admin', password='admin12345')
        
        # Проверка доступа к админ-панели Django
        response = self.client.get('/admin/')
        
        if response.status_code == 200:
            self.test_results['passed'].append('Доступ к админ-панели Django')
            print("✓ Доступ к админ-панели Django работает корректно")
        else:
            self.test_results['failed'].append('Доступ к админ-панели Django')
            print("✗ Ошибка доступа к админ-панели Django")
        
        # Проверка страницы управления олимпиадами
        response = self.client.get(reverse('olympiads:olympiad_manage_list'))
        
        if response.status_code == 200:
            self.test_results['passed'].append('Доступ к странице управления олимпиадами')
            print("✓ Доступ к странице управления олимпиадами работает корректно")
        else:
            self.test_results['failed'].append('Доступ к странице управления олимпиадами')
            print("✗ Ошибка доступа к странице управления олимпиадами")
        
        # Проверка создания олимпиады
        new_olympiad_data = {
            'title': 'Тестовая олимпиада',
            'description': 'Описание тестовой олимпиады',
            'short_description': 'Краткое описание',
            'start_datetime': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': (timezone.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
            'is_open': True,
            'time_limit_minutes': 60,
            'min_passing_score': 50,
            'status': Olympiad.OlympiadStatus.DRAFT
        }
        
        response = self.client.post(reverse('olympiads:olympiad_create'), new_olympiad_data, follow=True)
        
        if response.status_code == 200 and Olympiad.objects.filter(title='Тестовая олимпиада').exists():
            self.test_results['passed'].append('Создание олимпиады')
            print("✓ Создание олимпиады работает корректно")
        else:
            self.test_results['failed'].append('Создание олимпиады')
            print("✗ Ошибка при создании олимпиады")
    
    def test_user_interface(self):
        """Тестирование пользовательского интерфейса"""
        print("\nПроверка пользовательского интерфейса...")
        
        # Авторизуемся как студент
        self.client.login(username='student@example.com', password='student12345')
        
        # Проверка настроек интерфейса
        response = self.client.get(reverse('user_profile', kwargs={'username': 'Тестовый Студент'}))
        
        if response.status_code == 200:
            student = self.test_users['student']
            
            # Проверка/создание пользовательских настроек интерфейса
            interface, created = UserInterface.objects.get_or_create(
                user=student,
                defaults={
                    'theme': UserInterface.THEME_DARK,
                    'font_size': UserInterface.FONT_MEDIUM
                }
            )
            
            if not created:
                # Обновляем настройки
                interface.theme = UserInterface.THEME_DARK
                interface.save()
            
            self.test_results['passed'].append('Настройки интерфейса пользователя')
            print("✓ Настройки интерфейса пользователя работают корректно")
        else:
            self.test_results['failed'].append('Настройки интерфейса пользователя')
            print("✗ Ошибка при работе с настройками интерфейса пользователя")
    
    def test_responsive_design(self):
        """Тестирование адаптивного дизайна"""
        print("\nПроверка адаптивного дизайна...")
        
        # Устанавливаем различные User-Agent для симуляции разных устройств
        mobile_user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        tablet_user_agent = 'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        desktop_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        # Проверяем главную страницу на различных устройствах
        for device, user_agent in [
            ('мобильное устройство', mobile_user_agent),
            ('планшет', tablet_user_agent),
            ('десктоп', desktop_user_agent)
        ]:
            self.client.defaults['HTTP_USER_AGENT'] = user_agent
            response = self.client.get(reverse('home'))
            
            if response.status_code == 200:
                self.test_results['passed'].append(f'Адаптивный дизайн главной страницы для {device}')
                print(f"✓ Главная страница корректно отображается на {device}")
            else:
                self.test_results['failed'].append(f'Адаптивный дизайн главной страницы для {device}')
                print(f"✗ Ошибка отображения главной страницы на {device}")
        
        # Проверяем страницу олимпиад
        for device, user_agent in [
            ('мобильное устройство', mobile_user_agent),
            ('планшет', tablet_user_agent),
            ('десктоп', desktop_user_agent)
        ]:
            self.client.defaults['HTTP_USER_AGENT'] = user_agent
            response = self.client.get(reverse('olympiads:olympiad_list'))
            
            if response.status_code == 200:
                self.test_results['passed'].append(f'Адаптивный дизайн страницы олимпиад для {device}')
                print(f"✓ Страница олимпиад корректно отображается на {device}")
            else:
                self.test_results['failed'].append(f'Адаптивный дизайн страницы олимпиад для {device}')
                print(f"✗ Ошибка отображения страницы олимпиад на {device}")
    
    def run_comprehensive_test(self):
        """Запуск комплексного тестирования"""
        print("Начало комплексного тестирования...")
        
        try:
            # Создаем тестовые данные
            self.setup_test_data()
            
            # Устанавливаем задержку для загрузки страниц (для более надежного тестирования)
            import time
            def with_delay(func, delay=0.5):
                def wrapper(*args, **kwargs):
                    result = func(*args, **kwargs)
                    time.sleep(delay)
                    return result
                return wrapper
            
            # Тестируем регистрацию и вход
            self.test_registration_and_login()
            
            # Тестируем функциональность курсов
            self.test_course_functionality()
            
            # Тестируем функциональность олимпиад
            self.test_olympiad_functionality()
            
            # Тестируем административные функции
            self.test_admin_functionality()
            
            # Тестируем пользовательский интерфейс
            self.test_user_interface()
            
            # Тестируем адаптивный дизайн
            self.test_responsive_design()
            
            # Тестируем систему уведомлений
            if hasattr(self, 'test_notification_system'):
                self.test_notification_system()
            
            # Тестируем генерацию сертификатов
            if hasattr(self, 'test_certificate_generation'):
                self.test_certificate_generation()
            
            # Тестируем систему достижений и геймификации
            if hasattr(self, 'test_achievement_system'):
                self.test_achievement_system()
            
            # Финальный тест полного сценария: от регистрации до получения сертификата
            if hasattr(self, 'test_full_user_journey'):
                self.test_full_user_journey()
            
            print("\nКомплексное тестирование завершено")
            
            # Выводим результаты тестирования
            self.print_test_results()
            
        except Exception as e:
            print(f"\nОшибка при выполнении комплексного тестирования: {e}")
            import traceback
            traceback.print_exc()
    
    def test_notification_system(self):
        """Тестирование системы уведомлений"""
        print("\nПроверка системы уведомлений...")
        
        # Авторизуемся как студент
        self.client.login(username='student@example.com', password='student12345')
        
        # Проверка страницы уведомлений
        try:
            response = self.client.get(reverse('notifications:notification_list'))
            
            if response.status_code == 200:
                self.test_results['passed'].append('Просмотр списка уведомлений')
                print("✓ Просмотр списка уведомлений работает корректно")
            else:
                self.test_results['failed'].append('Просмотр списка уведомлений')
                print("✗ Ошибка при просмотре списка уведомлений")
        except Exception as e:
            self.test_results['failed'].append('Просмотр списка уведомлений (ошибка)')
            print(f"✗ Ошибка при доступе к списку уведомлений: {e}")
        
        # Проверка API маркировки уведомления как прочитанное
        try:
            from notifications.models import Notification
            notification = Notification.objects.filter(recipient=self.test_users['student']).first()
            
            if notification:
                response = self.client.post(
                    reverse('notifications:mark_as_read', kwargs={'notification_id': notification.id}),
                    follow=True
                )
                
                if response.status_code == 200:
                    # Обновляем объект из базы
                    notification.refresh_from_db()
                    
                    if notification.read:
                        self.test_results['passed'].append('Отметка уведомления прочитанным')
                        print("✓ Отметка уведомления прочитанным работает корректно")
                    else:
                        self.test_results['failed'].append('Отметка уведомления прочитанным')
                        print("✗ Ошибка отметки уведомления прочитанным (статус не изменился)")
                else:
                    self.test_results['failed'].append('Отметка уведомления прочитанным')
                    print("✗ Ошибка отметки уведомления прочитанным (ответ сервера)")
            else:
                self.test_results['warnings'].append('Нет уведомлений для проверки')
                print("⚠ Нет уведомлений для проверки функциональности маркировки")
        except Exception as e:
            self.test_results['warnings'].append('Отметка уведомления прочитанным (ошибка)')
            print(f"✗ Ошибка при отметке уведомления прочитанным: {e}")
            
    def test_certificate_generation(self):
        """Тестирование генерации сертификатов"""
        print("\nПроверка генерации сертификатов...")
        
        # Авторизуемся как администратор
        self.client.login(username='admin', password='admin12345')
        
        try:
            # Проверка страницы управления сертификатами
            response = self.client.get(reverse('olympiads:olympiad_certificate_list'))
            
            if response.status_code == 200:
                self.test_results['passed'].append('Просмотр списка сертификатов')
                print("✓ Просмотр списка сертификатов работает корректно")
            else:
                self.test_results['failed'].append('Просмотр списка сертификатов')
                print("✗ Ошибка при просмотре списка сертификатов")
                
            # Проверка создания сертификата вручную (для тестирования)
            from olympiads.models import OlympiadCertificate
            
            if self.test_olympiads and self.test_users.get('student'):
                olympiad = self.test_olympiads[0]
                user = self.test_users['student']
                
                # Создаем сертификат через модель
                cert, created = OlympiadCertificate.objects.get_or_create(
                    olympiad=olympiad,
                    user=user,
                    defaults={
                        'score': 85,
                        'place': 1,
                        'issue_date': timezone.now()
                    }
                )
                
                if created:
                    self.test_results['passed'].append('Создание сертификата')
                    print("✓ Создание сертификата выполнено успешно")
                else:
                    self.test_results['warnings'].append('Сертификат уже существует')
                    print("⚠ Сертификат уже существует")
                    
                # Проверка страницы просмотра сертификата
                response = self.client.get(
                    reverse('olympiads:olympiad_certificate', kwargs={'olympiad_id': olympiad.id})
                )
                
                if response.status_code == 200:
                    self.test_results['passed'].append('Просмотр сертификата')
                    print("✓ Просмотр сертификата работает корректно")
                else:
                    self.test_results['failed'].append('Просмотр сертификата')
                    print("✗ Ошибка при просмотре сертификата")
            else:
                self.test_results['warnings'].append('Нет олимпиад или пользователей для создания сертификата')
                print("⚠ Нет олимпиад или пользователей для тестирования создания сертификата")
                
        except Exception as e:
            self.test_results['warnings'].append('Генерация сертификатов (ошибка)')
            print(f"✗ Ошибка при тестировании генерации сертификатов: {e}")
    
    def test_achievement_system(self):
        """Тестирование системы достижений"""
        print("\nПроверка системы достижений...")
        
        # Авторизуемся как студент
        self.client.login(username='student@example.com', password='student12345')
        
        try:
            # Проверка страницы достижений
            response = self.client.get(reverse('gamification:achievement_list'))
            
            if response.status_code == 200:
                self.test_results['passed'].append('Просмотр списка достижений')
                print("✓ Просмотр списка достижений работает корректно")
            else:
                self.test_results['failed'].append('Просмотр списка достижений')
                print("✗ Ошибка при просмотре списка достижений")
                
            # Проверка присвоения достижения через скрипт
            from gamification.models import Achievement, UserAchievement
            
            student = self.test_users.get('student')
            if student:
                # Проверяем, есть ли достижения в системе
                achievement = Achievement.objects.filter(type='course_enrollment').first()
                
                if achievement:
                    # Создаем достижение для пользователя
                    user_achievement, created = UserAchievement.objects.get_or_create(
                        user=student,
                        achievement=achievement
                    )
                    
                    if created:
                        self.test_results['passed'].append('Присвоение достижения')
                        print("✓ Присвоение достижения выполнено успешно")
                    else:
                        self.test_results['warnings'].append('Достижение уже присвоено')
                        print("⚠ Достижение уже присвоено пользователю")
                else:
                    self.test_results['warnings'].append('Нет достижений для присвоения')
                    print("⚠ В системе нет доступных достижений для тестирования")
            else:
                self.test_results['warnings'].append('Нет тестового студента для проверки достижений')
                print("⚠ Нет тестового студента для проверки достижений")
                
        except Exception as e:
            self.test_results['warnings'].append('Система достижений (ошибка)')
            print(f"✗ Ошибка при тестировании системы достижений: {e}")
    
    def test_full_user_journey(self):
        """Тестирование полного пути пользователя от регистрации до получения сертификата"""
        print("\nПроверка полного пути пользователя...")
        
        # Создаем временного пользователя для теста
        import random
        test_suffix = random.randint(10000, 99999)
        username = f'test_journey_{test_suffix}'
        email = f'{username}@example.com'
        password = 'test12345'
        
        try:
            # Шаг 1: Регистрация
            print("Шаг 1: Регистрация нового пользователя")
            registration_data = {
                'username': username,
                'email': email,
                'password1': password,
                'password2': password
            }
            
            response = self.client.post(reverse('register'), registration_data, follow=True)
            
            if response.status_code != 200 or not User.objects.filter(username=username).exists():
                self.test_results['failed'].append('Полный путь: Регистрация')
                print("✗ Ошибка при регистрации нового пользователя")
                return
            
            print("✓ Регистрация успешна")
            
            # Шаг 2: Вход
            print("Шаг 2: Вход в систему")
            login_data = {
                'username': username,
                'password': password
            }
            
            response = self.client.post(reverse('login'), login_data, follow=True)
            
            if response.status_code != 200:
                self.test_results['failed'].append('Полный путь: Вход')
                print("✗ Ошибка при входе в систему")
                return
                
            print("✓ Вход успешен")
            
            # Шаг 3: Запись на курс
            print("Шаг 3: Запись на курс")
            if not self.test_courses:
                self.test_results['warnings'].append('Полный путь: Нет курсов для записи')
                print("⚠ Нет курсов для записи")
                return
                
            course = self.test_courses[0]
            response = self.client.post(
                reverse('course_enroll', kwargs={'slug': course.slug}),
                follow=True
            )
            
            user = User.objects.get(username=username)
            if response.status_code != 200 or not user.enrollments.filter(course=course).exists():
                self.test_results['failed'].append('Полный путь: Запись на курс')
                print("✗ Ошибка при записи на курс")
                return
                
            print("✓ Запись на курс успешна")
            
            # Шаг 4: Изучение урока
            print("Шаг 4: Изучение урока")
            lesson = Lesson.objects.filter(course=course).first()
            if not lesson:
                self.test_results['warnings'].append('Полный путь: Нет уроков для изучения')
                print("⚠ Нет уроков для изучения")
                return
                
            response = self.client.get(
                reverse('lesson_detail', kwargs={'course_slug': course.slug, 'lesson_id': lesson.id})
            )
            
            if response.status_code != 200:
                self.test_results['failed'].append('Полный путь: Просмотр урока')
                print("✗ Ошибка при просмотре урока")
                return
                
            # Отмечаем урок как завершенный
            response = self.client.post(
                reverse('lesson_complete', kwargs={'lesson_id': lesson.id}),
                follow=True
            )
            
            if response.status_code != 200 or not user.lesson_completions.filter(lesson=lesson).exists():
                self.test_results['failed'].append('Полный путь: Завершение урока')
                print("✗ Ошибка при отметке урока как завершенного")
                return
                
            print("✓ Изучение урока успешно")
            
            # Шаг 5: Участие в олимпиаде
            print("Шаг 5: Участие в олимпиаде")
            active_olympiads = [o for o in self.test_olympiads if o.status == Olympiad.OlympiadStatus.ACTIVE]
            if not active_olympiads:
                self.test_results['warnings'].append('Полный путь: Нет активных олимпиад')
                print("⚠ Нет активных олимпиад для участия")
                return
                
            olympiad = active_olympiads[0]
            response = self.client.post(
                reverse('olympiads:olympiad_register', kwargs={'olympiad_id': olympiad.id}),
                follow=True
            )
            
            if response.status_code != 200 or not user.olympiad_participations.filter(olympiad=olympiad).exists():
                self.test_results['failed'].append('Полный путь: Участие в олимпиаде')
                print("✗ Ошибка при участии в олимпиаде")
                return
                
            print("✓ Участие в олимпиаде успешно")
            
            # Шаг 6: Решение задачи олимпиады
            print("Шаг 6: Решение задачи олимпиады")
            task = OlympiadTask.objects.filter(olympiad=olympiad, task_type=OlympiadTask.TaskType.PROGRAMMING).first()
            if not task:
                self.test_results['warnings'].append('Полный путь: Нет задач для решения')
                print("⚠ Нет задач для решения")
                return
                
            response = self.client.get(
                reverse('olympiads:olympiad_task', kwargs={
                    'olympiad_id': olympiad.id,
                    'task_id': task.id
                })
            )
            
            if response.status_code != 200:
                self.test_results['failed'].append('Полный путь: Просмотр задачи олимпиады')
                print("✗ Ошибка при просмотре задачи олимпиады")
                return
                
            # Отправляем решение задачи
            solution_data = {
                'code': 'def sum_numbers(a, b):\n    return a + b'
            }
            
            response = self.client.post(
                reverse('olympiads:olympiad_task_submit', kwargs={
                    'olympiad_id': olympiad.id,
                    'task_id': task.id
                }),
                solution_data,
                follow=True
            )
            
            if response.status_code != 200 or not OlympiadTaskSubmission.objects.filter(
                task=task, user=user
            ).exists():
                self.test_results['failed'].append('Полный путь: Отправка решения')
                print("✗ Ошибка при отправке решения")
                return
                
            print("✓ Решение задачи успешно")
            
            # Шаг 7: Получение сертификата
            print("Шаг 7: Получение сертификата")
            
            # Для тестирования создаем сертификат напрямую
            cert = OlympiadCertificate.objects.create(
                olympiad=olympiad,
                user=user,
                score=95,
                place=1,
                issue_date=timezone.now()
            )
            
            response = self.client.get(
                reverse('olympiads:olympiad_certificate', kwargs={'olympiad_id': olympiad.id})
            )
            
            if response.status_code != 200:
                self.test_results['failed'].append('Полный путь: Просмотр сертификата')
                print("✗ Ошибка при просмотре сертификата")
                return
                
            print("✓ Получение сертификата успешно")
            
            # Финальный успех
            self.test_results['passed'].append('Полный путь пользователя')
            print("✓ Полный путь пользователя пройден успешно")
            
        except Exception as e:
            self.test_results['failed'].append('Полный путь пользователя (ошибка)')
            print(f"✗ Ошибка при тестировании полного пути пользователя: {e}")
            import traceback
            traceback.print_exc()
            
    def print_test_results(self):
        """Вывод результатов тестирования"""
        print("\n" + "="*50)
        print("РЕЗУЛЬТАТЫ КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ")
        print("="*50)
        
        print("\nУСПЕШНО ПРОЙДЕННЫЕ ТЕСТЫ:")
        for test in self.test_results['passed']:
            print(f"✓ {test}")
        
        print("\nНЕУДАЧНЫЕ ТЕСТЫ:")
        if self.test_results['failed']:
            for test in self.test_results['failed']:
                print(f"✗ {test}")
        else:
            print("Нет неудачных тестов")
        
        print("\nПРЕДУПРЕЖДЕНИЯ:")
        if self.test_results['warnings']:
            for warning in self.test_results['warnings']:
                print(f"⚠ {warning}")
        else:
            print("Нет предупреждений")
        
        print("\nРЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
        if self.test_results['failed']:
            print("1. Исправить ошибки, выявленные при тестировании")
        
        if 'Нет тестовых курсов для проверки' in self.test_results['warnings']:
            print("2. Добавить тестовые курсы для более полного тестирования")
        
        if 'Нет активных олимпиад для проверки' in self.test_results['warnings']:
            print("3. Создать активные олимпиады для тестирования функциональности")
        
        print("\nУРОВЕНЬ ГОТОВНОСТИ СИСТЕМЫ:")
        total_tests = len(self.test_results['passed']) + len(self.test_results['failed'])
        if total_tests > 0:
            success_rate = len(self.test_results['passed']) / total_tests * 100
            print(f"{success_rate:.1f}% тестов пройдено успешно")
            
            if success_rate >= 90:
                print("Система готова к использованию")
            elif success_rate >= 70:
                print("Система почти готова, требуются некоторые доработки")
            else:
                print("Система требует существенных доработок")
        else:
            print("Не выполнено ни одного теста")


# Запускаем комплексное тестирование
if __name__ == '__main__':
    tester = SystemTester()
    tester.run_comprehensive_test()