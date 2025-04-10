#!/usr/bin/env python
"""
Тестирование основных функций образовательной платформы через 
интерфейс командной строки. Этот скрипт проверяет различные аспекты 
системы без использования веб-интерфейса.
"""

import os
import sys
import django
import traceback
from collections import defaultdict
from datetime import datetime, timedelta

# Настраиваем окружение Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_platform.settings')
django.setup()

# Импортируем необходимые модули Django
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, F
from django.utils import timezone

# Импортируем модели проекта
from courses.models import Course, Category, Lesson, LessonContent, Enrollment, LessonCompletion
from olympiads.models import Olympiad, OlympiadTask, OlympiadParticipation, OlympiadTaskSubmission, OlympiadCertificate
from notifications.models import Notification
from gamification.models import Achievement, UserAchievement, Badge
from users.models import CustomUser

User = get_user_model()


class FunctionalTester:
    """Тестирование функциональности образовательной платформы через CLI"""
    
    def __init__(self):
        self.test_results = defaultdict(list)
        self.test_users = {}
        self.test_courses = []
        self.test_olympiads = []
        self.issues_found = []
        self.recommendations = []
    
    def setup_test_data(self):
        """Создание тестовых данных для проверки функциональности"""
        print("\nСоздание необходимых тестовых данных...")
        
        # Создаем тестовых пользователей, если их еще нет
        self._create_test_users()
        
        # Создаем тестовые категории, если их еще нет
        self._create_test_categories()
        
        # Создаем тестовые курсы, если их еще нет
        self._create_test_courses()
        
        # Создаем тестовые олимпиады, если их еще нет
        self._create_test_olympiads()
    
    def _create_test_users(self):
        """Создание тестовых пользователей"""
        print("Создание тестовых пользователей...")
        
        # Создаем администратора
        admin, created = User.objects.get_or_create(
            username='test_admin',
            defaults={
                'email': 'test_admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin12345')
            admin.save()
            print(f"✓ Создан администратор: {admin.username}")
        else:
            print(f"✓ Использован существующий администратор: {admin.username}")
        self.test_users['admin'] = admin
        
        # Создаем студента
        student, created = User.objects.get_or_create(
            username='test_student',
            defaults={
                'email': 'test_student@example.com',
                'is_staff': False,
                'is_superuser': False
            }
        )
        if created:
            student.set_password('student12345')
            student.save()
            print(f"✓ Создан студент: {student.username}")
        else:
            print(f"✓ Использован существующий студент: {student.username}")
        self.test_users['student'] = student
        
        # Создаем преподавателя
        teacher, created = User.objects.get_or_create(
            username='test_teacher',
            defaults={
                'email': 'test_teacher@example.com',
                'is_staff': True,
                'is_superuser': False,
                'is_teacher': True
            }
        )
        if created:
            teacher.set_password('teacher12345')
            teacher.save()
            print(f"✓ Создан преподаватель: {teacher.username}")
        else:
            print(f"✓ Использован существующий преподаватель: {teacher.username}")
        self.test_users['teacher'] = teacher
    
    def _create_test_categories(self):
        """Создание тестовых категорий"""
        print("Создание тестовых категорий...")
        
        categories = [
            {"name": "Программирование на Python", "slug": "python-programming"},
            {"name": "Веб-разработка", "slug": "web-development"},
            {"name": "Алгоритмы и структуры данных", "slug": "algorithms-and-data-structures"}
        ]
        
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                name=cat_data["name"],
                defaults={"slug": cat_data["slug"]}
            )
            if created:
                print(f"✓ Создана категория: {category.name}")
            else:
                print(f"✓ Использована существующая категория: {category.name}")
    
    def _create_test_courses(self):
        """Создание тестовых курсов"""
        print("Создание тестовых курсов...")
        
        # Получаем категории
        python_category = Category.objects.filter(name="Программирование на Python").first()
        
        courses_data = [
            {
                "title": "Тестовый курс по Python",
                "description": "Тестовый курс для проверки функциональности системы",
                "category": python_category,
                "author": self.test_users['teacher'],
                "is_published": True,
                "lessons": [
                    {"title": "Введение в Python", "order": 1},
                    {"title": "Основы синтаксиса", "order": 2},
                    {"title": "Работа с функциями", "order": 3}
                ]
            }
        ]
        
        for course_data in courses_data:
            # Создаем курс, если его еще нет
            slug = django.utils.text.slugify(course_data["title"])
            course, created = Course.objects.get_or_create(
                title=course_data["title"],
                defaults={
                    "description": course_data["description"],
                    "slug": slug,
                    "category": course_data["category"],
                    "author": course_data["author"],
                    "is_published": course_data["is_published"]
                }
            )
            
            if created:
                print(f"✓ Создан курс: {course.title}")
            else:
                print(f"✓ Использован существующий курс: {course.title}")
            
            self.test_courses.append(course)
            
            # Создаем уроки
            for lesson_data in course_data["lessons"]:
                lesson, created = Lesson.objects.get_or_create(
                    title=lesson_data["title"],
                    course=course,
                    defaults={
                        "order": lesson_data["order"],
                        "is_published": True
                    }
                )
                
                if created:
                    print(f"  ✓ Создан урок: {lesson.title}")
                    
                    # Создаем содержимое урока
                    content = LessonContent.objects.create(
                        lesson=lesson,
                        content_type=LessonContent.ContentType.TEXT,
                        text_content=f"Тестовое содержимое для урока {lesson.title}"
                    )
                else:
                    print(f"  ✓ Использован существующий урок: {lesson.title}")
    
    def _create_test_olympiads(self):
        """Создание тестовых олимпиад"""
        print("Создание тестовых олимпиад...")
        
        # Получаем категории
        python_category = Category.objects.filter(name="Программирование на Python").first()
        
        olympiads_data = [
            {
                "title": "Тестовая олимпиада по Python",
                "description": "Тестовая олимпиада для проверки функциональности системы",
                "category": python_category,
                "organizer": self.test_users['teacher'],
                "start_date": timezone.now() - timedelta(days=1),
                "end_date": timezone.now() + timedelta(days=7),
                "registration_deadline": timezone.now() + timedelta(days=3),
                "status": "active",
                "tasks": [
                    {
                        "title": "Простая задача на сложение",
                        "description": "Напишите функцию, которая складывает два числа",
                        "task_type": "programming",
                        "difficulty": "easy",
                        "max_score": 10
                    },
                    {
                        "title": "Тест по Python",
                        "description": "Выберите правильные варианты ответов",
                        "task_type": "test",
                        "difficulty": "medium",
                        "max_score": 20
                    }
                ]
            }
        ]
        
        for olympiad_data in olympiads_data:
            # Создаем олимпиаду, если ее еще нет
            olympiad, created = Olympiad.objects.get_or_create(
                title=olympiad_data["title"],
                defaults={
                    "description": olympiad_data["description"],
                    "category": olympiad_data["category"],
                    "organizer": olympiad_data["organizer"],
                    "start_date": olympiad_data["start_date"],
                    "end_date": olympiad_data["end_date"],
                    "registration_deadline": olympiad_data["registration_deadline"],
                    "status": Olympiad.OlympiadStatus.ACTIVE
                }
            )
            
            if created:
                print(f"✓ Создана олимпиада: {olympiad.title}")
            else:
                print(f"✓ Использована существующая олимпиада: {olympiad.title}")
            
            self.test_olympiads.append(olympiad)
            
            # Создаем задачи
            for task_data in olympiad_data["tasks"]:
                task_type = OlympiadTask.TaskType.PROGRAMMING if task_data["task_type"] == "programming" else OlympiadTask.TaskType.TEST
                difficulty = OlympiadTask.Difficulty.EASY if task_data["difficulty"] == "easy" else OlympiadTask.Difficulty.MEDIUM
                
                task, created = OlympiadTask.objects.get_or_create(
                    title=task_data["title"],
                    olympiad=olympiad,
                    defaults={
                        "description": task_data["description"],
                        "task_type": task_type,
                        "difficulty": difficulty,
                        "max_score": task_data["max_score"]
                    }
                )
                
                if created:
                    print(f"  ✓ Создана задача: {task.title}")
                else:
                    print(f"  ✓ Использована существующая задача: {task.title}")
    
    def test_registration_system(self):
        """Тестирование системы регистрации и авторизации"""
        print("\nПроверка системы регистрации и авторизации...")
        
        # Проверка создания нового пользователя
        username = f"test_user_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        email = f"{username}@example.com"
        password = "test12345"
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            print(f"✓ Создан новый пользователь: {username}")
            
            # Проверяем наличие пользователя в базе данных
            user_in_db = User.objects.filter(username=username).exists()
            if user_in_db:
                self.test_results["passed"].append("Создание пользователя")
                print("✓ Пользователь успешно сохранен в базе данных")
            else:
                self.test_results["failed"].append("Создание пользователя")
                print("✗ Ошибка: пользователь не сохранен в базе данных")
                self.issues_found.append("Проблема с созданием пользователей")
            
            # Проверяем обязательные поля профиля
            required_fields = ['username', 'email']
            missing_fields = []
            
            for field in required_fields:
                if not hasattr(user, field) or not getattr(user, field):
                    missing_fields.append(field)
            
            if missing_fields:
                self.test_results["failed"].append("Обязательные поля профиля")
                print(f"✗ Ошибка: отсутствуют обязательные поля: {', '.join(missing_fields)}")
                self.issues_found.append("Отсутствуют обязательные поля в профиле пользователя")
            else:
                self.test_results["passed"].append("Обязательные поля профиля")
                print("✓ Все обязательные поля профиля заполнены")
                
            # Удаляем тестового пользователя после проверки
            user.delete()
            print(f"✓ Пользователь {username} удален после тестирования")
            
        except Exception as e:
            self.test_results["failed"].append("Регистрация пользователя")
            print(f"✗ Ошибка при тестировании регистрации: {e}")
            self.issues_found.append("Проблема с системой регистрации")
    
    def test_course_system(self):
        """Тестирование системы курсов"""
        print("\nПроверка системы курсов...")
        
        if not self.test_courses:
            self.test_results["failed"].append("Наличие курсов для тестирования")
            print("✗ Ошибка: нет курсов для тестирования")
            self.issues_found.append("Отсутствуют курсы для проверки функциональности")
            return
        
        course = self.test_courses[0]
        student = self.test_users['student']
        
        try:
            # Проверка записи на курс
            enrollment, created = Enrollment.objects.get_or_create(
                user=student,
                course=course
            )
            
            if created:
                self.test_results["passed"].append("Запись на курс")
                print(f"✓ Студент {student.username} записан на курс {course.title}")
            else:
                self.test_results["passed"].append("Запись на курс (существующая)")
                print(f"✓ Студент {student.username} уже записан на курс {course.title}")
            
            # Проверка уроков курса
            lessons = Lesson.objects.filter(course=course)
            if lessons.exists():
                self.test_results["passed"].append("Наличие уроков")
                print(f"✓ Найдено {lessons.count()} уроков в курсе")
                
                # Проверка отметки урока как завершенного
                first_lesson = lessons.first()
                completion, created = LessonCompletion.objects.get_or_create(
                    user=student,
                    lesson=first_lesson
                )
                
                if created:
                    self.test_results["passed"].append("Отметка урока как завершенного")
                    print(f"✓ Урок {first_lesson.title} отмечен как завершенный")
                else:
                    self.test_results["passed"].append("Отметка урока как завершенного (существующая)")
                    print(f"✓ Урок {first_lesson.title} уже отмечен как завершенный")
                
                # Проверка содержимого урока
                lesson_contents = LessonContent.objects.filter(lesson=first_lesson)
                if lesson_contents.exists():
                    self.test_results["passed"].append("Наличие содержимого урока")
                    print(f"✓ Найдено {lesson_contents.count()} блоков содержимого в уроке")
                else:
                    self.test_results["failed"].append("Наличие содержимого урока")
                    print("✗ Ошибка: содержимое урока отсутствует")
                    self.issues_found.append("Уроки не имеют содержимого")
            else:
                self.test_results["failed"].append("Наличие уроков")
                print("✗ Ошибка: уроки отсутствуют в курсе")
                self.issues_found.append("Курсы не содержат уроков")
        
        except Exception as e:
            self.test_results["failed"].append("Система курсов")
            print(f"✗ Ошибка при тестировании системы курсов: {e}")
            self.issues_found.append("Проблема с системой курсов")
    
    def test_olympiad_system(self):
        """Тестирование системы олимпиад"""
        print("\nПроверка системы олимпиад...")
        
        if not self.test_olympiads:
            self.test_results["failed"].append("Наличие олимпиад для тестирования")
            print("✗ Ошибка: нет олимпиад для тестирования")
            self.issues_found.append("Отсутствуют олимпиады для проверки функциональности")
            return
        
        olympiad = self.test_olympiads[0]
        student = self.test_users['student']
        
        try:
            # Проверка регистрации на олимпиаду
            participation, created = OlympiadParticipation.objects.get_or_create(
                user=student,
                olympiad=olympiad
            )
            
            if created:
                self.test_results["passed"].append("Регистрация на олимпиаду")
                print(f"✓ Студент {student.username} зарегистрирован на олимпиаду {olympiad.title}")
            else:
                self.test_results["passed"].append("Регистрация на олимпиаду (существующая)")
                print(f"✓ Студент {student.username} уже зарегистрирован на олимпиаду {olympiad.title}")
            
            # Проверка заданий олимпиады
            tasks = OlympiadTask.objects.filter(olympiad=olympiad)
            if tasks.exists():
                self.test_results["passed"].append("Наличие заданий олимпиады")
                print(f"✓ Найдено {tasks.count()} заданий в олимпиаде")
                
                # Проверка отправки решения задачи
                programming_task = tasks.filter(task_type=OlympiadTask.TaskType.PROGRAMMING).first()
                if programming_task:
                    submission, created = OlympiadTaskSubmission.objects.get_or_create(
                        user=student,
                        task=programming_task,
                        defaults={
                            "code": "def solution(a, b):\n    return a + b",
                            "language": "python",
                            "status": "pending"
                        }
                    )
                    
                    if created:
                        self.test_results["passed"].append("Отправка решения задачи")
                        print(f"✓ Решение задачи {programming_task.title} отправлено")
                    else:
                        self.test_results["passed"].append("Отправка решения задачи (существующая)")
                        print(f"✓ Решение задачи {programming_task.title} уже отправлено")
                else:
                    self.test_results["warnings"].append("Наличие задач программирования")
                    print("⚠ Предупреждение: нет задач программирования для тестирования")
            else:
                self.test_results["failed"].append("Наличие заданий олимпиады")
                print("✗ Ошибка: задания отсутствуют в олимпиаде")
                self.issues_found.append("Олимпиады не содержат заданий")
            
            # Проверка создания сертификата
            certificate, created = OlympiadCertificate.objects.get_or_create(
                user=student,
                olympiad=olympiad,
                defaults={
                    "score": 85,
                    "place": 3,
                    "issue_date": timezone.now()
                }
            )
            
            if created:
                self.test_results["passed"].append("Создание сертификата")
                print(f"✓ Сертификат создан для участника {student.username}")
            else:
                self.test_results["passed"].append("Создание сертификата (существующий)")
                print(f"✓ Сертификат уже существует для участника {student.username}")
        
        except Exception as e:
            self.test_results["failed"].append("Система олимпиад")
            print(f"✗ Ошибка при тестировании системы олимпиад: {e}")
            self.issues_found.append("Проблема с системой олимпиад")
    
    def test_notification_system(self):
        """Тестирование системы уведомлений"""
        print("\nПроверка системы уведомлений...")
        
        student = self.test_users['student']
        
        try:
            # Создаем тестовое уведомление
            notification_title = f"Тестовое уведомление {timezone.now().strftime('%H:%M:%S')}"
            
            notification = Notification.objects.create(
                recipient=student,
                title=notification_title,
                message="Это тестовое уведомление для проверки системы",
                notification_type="info"
            )
            
            self.test_results["passed"].append("Создание уведомления")
            print(f"✓ Уведомление '{notification_title}' создано")
            
            # Проверяем, что уведомление создалось и его можно получить
            notification_in_db = Notification.objects.filter(
                recipient=student,
                title=notification_title
            ).exists()
            
            if notification_in_db:
                self.test_results["passed"].append("Получение уведомления")
                print("✓ Уведомление успешно сохранено в базе данных")
                
                # Отмечаем уведомление как прочитанное
                notification.read = True
                notification.save()
                
                self.test_results["passed"].append("Отметка уведомления прочитанным")
                print("✓ Уведомление отмечено как прочитанное")
            else:
                self.test_results["failed"].append("Получение уведомления")
                print("✗ Ошибка: уведомление не сохранено в базе данных")
                self.issues_found.append("Проблема с сохранением уведомлений")
        
        except Exception as e:
            self.test_results["failed"].append("Система уведомлений")
            print(f"✗ Ошибка при тестировании системы уведомлений: {e}")
            self.issues_found.append("Проблема с системой уведомлений")
    
    def test_achievement_system(self):
        """Тестирование системы достижений и геймификации"""
        print("\nПроверка системы достижений и геймификации...")
        
        student = self.test_users['student']
        
        try:
            # Поиск существующих достижений
            achievements = Achievement.objects.all()
            
            if achievements.exists():
                self.test_results["passed"].append("Наличие достижений в системе")
                print(f"✓ В системе найдено {achievements.count()} достижений")
                
                # Назначаем первое достижение пользователю
                achievement = achievements.first()
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=student,
                    achievement=achievement
                )
                
                if created:
                    self.test_results["passed"].append("Назначение достижения пользователю")
                    print(f"✓ Достижение '{achievement.title}' назначено пользователю {student.username}")
                else:
                    self.test_results["passed"].append("Назначение достижения пользователю (существующее)")
                    print(f"✓ Достижение '{achievement.title}' уже назначено пользователю {student.username}")
            else:
                # Создаем тестовое достижение
                achievement = Achievement.objects.create(
                    title="Тестовое достижение",
                    description="Тестовое достижение для проверки системы",
                    type="test",
                    points=10
                )
                
                self.test_results["passed"].append("Создание достижения")
                print(f"✓ Создано тестовое достижение: {achievement.title}")
                
                # Назначаем достижение пользователю
                user_achievement = UserAchievement.objects.create(
                    user=student,
                    achievement=achievement
                )
                
                self.test_results["passed"].append("Назначение достижения пользователю")
                print(f"✓ Достижение '{achievement.title}' назначено пользователю {student.username}")
        
        except Exception as e:
            self.test_results["failed"].append("Система достижений")
            print(f"✗ Ошибка при тестировании системы достижений: {e}")
            self.issues_found.append("Проблема с системой достижений")
    
    def check_missing_features(self):
        """Проверка отсутствующих или неполностью реализованных функций"""
        print("\nПроверка отсутствующих или неполностью реализованных функций...")
        
        # Проверка наличия и функциональности модулей
        modules_to_check = [
            {"app": "courses", "model": "Course", "name": "Курсы"},
            {"app": "lessons", "model": "Lesson", "name": "Уроки"},
            {"app": "olympiads", "model": "Olympiad", "name": "Олимпиады"},
            {"app": "notifications", "model": "Notification", "name": "Уведомления"},
            {"app": "gamification", "model": "Achievement", "name": "Геймификация"},
            {"app": "users", "model": "CustomUser", "name": "Пользователи"}
        ]
        
        for module in modules_to_check:
            try:
                # Импортируем модель
                model_class = None
                if module["app"] == "courses":
                    from courses.models import Course
                    model_class = Course
                elif module["app"] == "lessons":
                    from courses.models import Lesson
                    model_class = Lesson
                elif module["app"] == "olympiads":
                    from olympiads.models import Olympiad
                    model_class = Olympiad
                elif module["app"] == "notifications":
                    from notifications.models import Notification
                    model_class = Notification
                elif module["app"] == "gamification":
                    from gamification.models import Achievement
                    model_class = Achievement
                elif module["app"] == "users":
                    from users.models import CustomUser
                    model_class = CustomUser
                
                if model_class:
                    count = model_class.objects.count()
                    self.test_results["passed"].append(f"Модуль {module['name']}")
                    print(f"✓ Модуль {module['name']} функционирует, найдено {count} записей")
                else:
                    self.test_results["failed"].append(f"Модуль {module['name']}")
                    print(f"✗ Не удалось проверить модуль {module['name']}")
                    self.issues_found.append(f"Проблема с модулем {module['name']}")
            except Exception as e:
                self.test_results["failed"].append(f"Модуль {module['name']}")
                print(f"✗ Ошибка при проверке модуля {module['name']}: {e}")
                self.issues_found.append(f"Проблема с модулем {module['name']}")
                self.recommendations.append(f"Необходимо проверить и доработать модуль {module['name']}")
        
        # Проверка наличия звуковых файлов для уведомлений
        sound_files = ["success.mp3", "error.mp3", "warning.mp3", "info.mp3"]
        missing_sounds = []
        
        for sound_file in sound_files:
            sound_path = os.path.join(settings.STATIC_ROOT, "sounds", sound_file)
            if not os.path.exists(sound_path):
                missing_sounds.append(sound_file)
        
        if missing_sounds:
            self.test_results["warnings"].append("Звуковые файлы уведомлений")
            print(f"⚠ Отсутствуют звуковые файлы: {', '.join(missing_sounds)}")
            self.recommendations.append("Необходимо добавить отсутствующие звуковые файлы уведомлений")
        else:
            self.test_results["passed"].append("Звуковые файлы уведомлений")
            print("✓ Все звуковые файлы уведомлений присутствуют")
    
    def check_database_health(self):
        """Проверка состояния базы данных"""
        print("\nПроверка состояния базы данных...")
        
        # Проверка на наличие пустых обязательных полей
        # Проверка категорий с пустыми slug
        empty_slug_categories = Category.objects.filter(Q(slug=None) | Q(slug=''))
        if empty_slug_categories.exists():
            self.test_results["failed"].append("Категории с пустыми slug")
            print(f"✗ Найдено {empty_slug_categories.count()} категорий с пустыми slug")
            self.issues_found.append("Категории с пустыми slug")
            self.recommendations.append("Необходимо заполнить пустые slug категорий")
        else:
            self.test_results["passed"].append("Категории с пустыми slug")
            print("✓ Нет категорий с пустыми slug")
        
        # Проверка курсов с пустыми slug
        empty_slug_courses = Course.objects.filter(Q(slug=None) | Q(slug=''))
        if empty_slug_courses.exists():
            self.test_results["failed"].append("Курсы с пустыми slug")
            print(f"✗ Найдено {empty_slug_courses.count()} курсов с пустыми slug")
            self.issues_found.append("Курсы с пустыми slug")
            self.recommendations.append("Необходимо заполнить пустые slug курсов")
        else:
            self.test_results["passed"].append("Курсы с пустыми slug")
            print("✓ Нет курсов с пустыми slug")
        
        # Проверка модератор в курсах
        courses_without_author = Course.objects.filter(author=None)
        if courses_without_author.exists():
            self.test_results["failed"].append("Курсы без автора")
            print(f"✗ Найдено {courses_without_author.count()} курсов без автора")
            self.issues_found.append("Курсы без автора")
            self.recommendations.append("Необходимо назначить авторов для курсов")
        else:
            self.test_results["passed"].append("Курсы без автора")
            print("✓ Нет курсов без автора")
        
        # Проверка олимпиад без организатора
        olympiads_without_organizer = Olympiad.objects.filter(organizer=None)
        if olympiads_without_organizer.exists():
            self.test_results["failed"].append("Олимпиады без организатора")
            print(f"✗ Найдено {olympiads_without_organizer.count()} олимпиад без организатора")
            self.issues_found.append("Олимпиады без организатора")
            self.recommendations.append("Необходимо назначить организаторов для олимпиад")
        else:
            self.test_results["passed"].append("Олимпиады без организатора")
            print("✓ Нет олимпиад без организатора")
        
        # Проверка на наличие уроков без содержимого
        lessons_without_content = Lesson.objects.annotate(
            content_count=Count('contents')
        ).filter(content_count=0)
        
        if lessons_without_content.exists():
            self.test_results["warnings"].append("Уроки без содержимого")
            print(f"⚠ Найдено {lessons_without_content.count()} уроков без содержимого")
            self.recommendations.append("Необходимо добавить содержимое для уроков")
        else:
            self.test_results["passed"].append("Уроки без содержимого")
            print("✓ Нет уроков без содержимого")
        
        # Проверка на наличие заданий олимпиад без тестов
        tasks = OlympiadTask.objects.filter(task_type=OlympiadTask.TaskType.PROGRAMMING)
        if tasks.exists():
            # Здесь можно добавить проверку наличия тестовых случаев
            pass
    
    def print_test_results(self):
        """Вывод результатов тестирования"""
        print("\n" + "="*50)
        print("РЕЗУЛЬТАТЫ ФУНКЦИОНАЛЬНОГО ТЕСТИРОВАНИЯ")
        print("="*50)
        
        passed_count = len(self.test_results["passed"])
        failed_count = len(self.test_results["failed"])
        warnings_count = len(self.test_results["warnings"])
        total_tests = passed_count + failed_count
        
        print(f"\nУспешно пройденных тестов: {passed_count}")
        print(f"Неудачных тестов: {failed_count}")
        print(f"Предупреждений: {warnings_count}")
        
        if total_tests > 0:
            success_rate = (passed_count / total_tests) * 100
            print(f"Процент успеха: {success_rate:.1f}%")
        
        if self.issues_found:
            print("\nВЫЯВЛЕННЫЕ ПРОБЛЕМЫ:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"{i}. {issue}")
        
        if self.recommendations:
            print("\nРЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
            for i, recommendation in enumerate(self.recommendations, 1):
                print(f"{i}. {recommendation}")
        
        if not self.issues_found:
            print("\n✓ Тестирование не выявило серьезных проблем")
            
        if total_tests > 0:
            if success_rate >= 90:
                print("\nСистема находится в хорошем состоянии")
            elif success_rate >= 70:
                print("\nСистема требует некоторых доработок")
            else:
                print("\nСистема требует серьезных доработок")
    
    def run_tests(self):
        """Запуск всех функциональных тестов"""
        print("Начало функционального тестирования...")
        
        try:
            # Подготовка тестовых данных
            self.setup_test_data()
            
            # Тестирование регистрации и авторизации
            self.test_registration_system()
            
            # Тестирование системы курсов
            self.test_course_system()
            
            # Тестирование системы олимпиад
            self.test_olympiad_system()
            
            # Тестирование системы уведомлений
            self.test_notification_system()
            
            # Тестирование системы достижений
            self.test_achievement_system()
            
            # Проверка отсутствующих функций
            self.check_missing_features()
            
            # Проверка состояния базы данных
            self.check_database_health()
            
            # Вывод результатов
            self.print_test_results()
            
        except Exception as e:
            print(f"\nОшибка при выполнении тестирования: {e}")
            traceback.print_exc()


# Запускаем функциональное тестирование
if __name__ == '__main__':
    tester = FunctionalTester()
    tester.run_tests()