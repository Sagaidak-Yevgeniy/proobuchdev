from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Count, F

from users.models import CustomUser
from lessons.models import LessonCompletion, Lesson
from courses.models import Enrollment
from .models import Achievement, UserAchievement, Badge, UserBadge, PointsHistory


@receiver(post_save, sender=UserAchievement)
def award_achievement_points(sender, instance, created, **kwargs):
    """Начисляет очки пользователю при получении достижения"""
    if created:
        points = instance.achievement.points
        print(f"Начисление {points} очков пользователю {instance.user.username} за достижение '{instance.achievement.name}'")
        
        # Добавляем запись в историю очков
        PointsHistory.objects.create(
            user=instance.user,
            points=points,
            action='achievement',
            description=f'Получено достижение: {instance.achievement.name}'
        )
        print(f"Запись в историю очков добавлена")

        # Проверяем, следует ли выдать пользователю новые значки
        check_badges_for_user(instance.user)


def check_badges_for_user(user):
    """Проверяет, следует ли выдать пользователю новые значки"""
    print(f"Проверяем значки для пользователя {user.username}")
    
    # Получаем все значки, которые пользователь еще не имеет, отсортированные по требуемым очкам
    user_badges = UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    available_badges = Badge.objects.exclude(id__in=user_badges).order_by('required_points')
    
    # Получаем общее количество очков пользователя из истории
    from django.db.models import Sum
    total_points = PointsHistory.objects.filter(user=user).aggregate(total=Sum('points'))['total'] or 0
    print(f"Общее количество очков пользователя: {total_points}")
    
    # Выдаем все значки, для которых у пользователя достаточно очков
    for badge in available_badges:
        if total_points >= badge.required_points:
            print(f"Выдаем значок '{badge.name}' пользователю {user.username}")
            UserBadge.objects.create(
                user=user,
                badge=badge
            )
            
            # Добавляем запись в историю очков о получении значка
            PointsHistory.objects.create(
                user=user,
                points=0,  # Значок сам по себе не дает очков
                action='other',
                description=f'Получен значок: {badge.name}'
            )
            print(f"Значок '{badge.name}' успешно выдан")


@receiver(post_save, sender=LessonCompletion)
def check_lesson_completion_achievements(sender, instance, created, **kwargs):
    """Проверяет и выдает достижения при завершении урока пользователем"""
    print(f"Обработка события завершения урока для пользователя {instance.user.username}, урок: {instance.lesson.title}")
    
    # Проверяем только если урок отмечен как завершенный
    if instance.completed:
        print(f"Урок {instance.lesson.title} отмечен как завершенный")
        user = instance.user
        lesson = instance.lesson
        course = lesson.course

        # Получаем все достижения связанные с уроками
        lesson_achievements = Achievement.objects.filter(type='lesson')
        
        # Проверяем достижения для первого завершенного урока
        first_lesson_achievements = lesson_achievements.filter(name__icontains='первый урок')
        if first_lesson_achievements.exists() and LessonCompletion.objects.filter(user=user, completed=True).count() == 1:
            print(f"Пользователь {user.username} завершил свой первый урок!")
            for achievement in first_lesson_achievements:
                UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                print(f"Выдано достижение: {achievement.name}")
        
        # Подсчитываем количество завершенных уроков в текущем курсе
        completed_lessons_in_course = LessonCompletion.objects.filter(
            user=user,
            lesson__course=course,
            completed=True
        ).count()
        print(f"Завершено {completed_lessons_in_course} уроков в курсе {course.title}")
        
        # Проверяем достижения для завершения 5 уроков
        five_lessons_achievements = lesson_achievements.filter(name__icontains='5 уроков')
        if five_lessons_achievements.exists() and completed_lessons_in_course >= 5:
            print(f"Пользователь {user.username} завершил 5 уроков в курсе!")
            for achievement in five_lessons_achievements:
                UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                print(f"Выдано достижение: {achievement.name}")
        
        # Проверяем достижения для завершения 10 уроков
        ten_lessons_achievements = lesson_achievements.filter(name__icontains='10 уроков')
        if ten_lessons_achievements.exists() and completed_lessons_in_course >= 10:
            print(f"Пользователь {user.username} завершил 10 уроков в курсе!")
            for achievement in ten_lessons_achievements:
                UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                print(f"Выдано достижение: {achievement.name}")
        
        # Проверяем, все ли уроки курса завершены
        total_lessons_in_course = Lesson.objects.filter(course=course).count()
        if total_lessons_in_course > 0 and completed_lessons_in_course == total_lessons_in_course:
            print(f"Пользователь {user.username} завершил все уроки в курсе {course.title}!")
            course_achievements = Achievement.objects.filter(type='course', name__icontains='курс')
            for achievement in course_achievements:
                UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                print(f"Выдано достижение: {achievement.name}")


@receiver(post_save, sender=Enrollment)
def check_enrollment_achievements(sender, instance, created, **kwargs):
    """Проверяет и выдает достижения при записи на курс"""
    if created:
        print(f"Пользователь {instance.user.username} записался на курс {instance.course.title}")
        user = instance.user
        
        # Считаем, на сколько курсов записан пользователь
        enrollment_count = Enrollment.objects.filter(user=user).count()
        print(f"Пользователь записан на {enrollment_count} курсов")
        
        # Достижение за первую запись на курс
        first_enrollment_achievements = Achievement.objects.filter(type='course', name__icontains='первый курс')
        if first_enrollment_achievements.exists() and enrollment_count == 1:
            print(f"Это первая запись на курс для {user.username}!")
            for achievement in first_enrollment_achievements:
                UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                print(f"Выдано достижение: {achievement.name}")
        
        # Достижение за запись на 3 курса
        three_courses_achievements = Achievement.objects.filter(type='course', name__icontains='3 курса')
        if three_courses_achievements.exists() and enrollment_count >= 3:
            print(f"Пользователь {user.username} записан на 3 и более курсов!")
            for achievement in three_courses_achievements:
                UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                print(f"Выдано достижение: {achievement.name}")