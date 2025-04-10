import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "educational_platform.settings")
django.setup()

from django.urls import reverse, NoReverseMatch
from courses.models import Course
from lessons.models import Lesson

def check_url(name, args=None):
    try:
        url = reverse(name, args=args)
        print(f"✓ {name}: {url}")
        return True
    except NoReverseMatch as e:
        print(f"✗ {name}: {e}")
        return False

print("\n===== Проверка URL маршрутов =====\n")

# Базовые маршруты
print("Базовые маршруты:")
check_url('home')
check_url('login')
check_url('logout')
check_url('register')

# Курсы
print("\nМаршруты курсов:")
check_url('course_list')
first_course = Course.objects.first()
if first_course:
    check_url('course_detail', [first_course.slug])
    check_url('course_enroll', [first_course.slug])

# Уроки
print("\nМаршруты уроков:")
first_lesson = Lesson.objects.first()
if first_lesson and first_course:
    try:
        check_url('lesson_detail', [first_course.slug, first_lesson.id])
    except Exception as e:
        print(f"✗ lesson_detail с двумя аргументами: {e}")
    
    try:
        check_url('lesson_detail', [first_lesson.id])
    except Exception as e:
        print(f"✗ lesson_detail с одним аргументом: {e}")
    
    check_url('lesson_complete', [first_lesson.id])

# Олимпиады
print("\nМаршруты олимпиад:")
check_url('olympiads:olympiad_list')
check_url('olympiads:olympiad_manage_list')
check_url('olympiads:olympiad_create')

from olympiads.models import Olympiad, OlympiadTask
first_olympiad = Olympiad.objects.first()
if first_olympiad:
    check_url('olympiads:olympiad_detail', [first_olympiad.id])
    check_url('olympiads:olympiad_register', [first_olympiad.id])
    
    first_task = OlympiadTask.objects.filter(olympiad=first_olympiad).first()
    if first_task:
        check_url('olympiads:olympiad_task', [first_olympiad.id, first_task.id])
        check_url('olympiads:olympiad_task_submit', [first_olympiad.id, first_task.id])

# Сертификаты
print("\nМаршруты сертификатов:")
try:
    check_url('olympiads:olympiad_certificate_list')
except Exception as e:
    print(f"✗ olympiad_certificate_list: {e}")

if first_olympiad:
    try:
        check_url('olympiads:olympiad_certificate', [first_olympiad.id])
    except Exception as e:
        print(f"✗ olympiad_certificate с одним аргументом: {e}")

# Уведомления
print("\nМаршруты уведомлений:")
check_url('notifications:notification_list')
check_url('notifications:notification_count')

# Достижения
print("\nМаршруты достижений:")
check_url('gamification:achievement_list')

print("\nПроверка завершена.")
