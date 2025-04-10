from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
import json
import random
from datetime import datetime, timedelta

from courses.models import Course, Enrollment
from gamification.models import Achievement, UserAchievement
from users.models import CustomUser
from lessons.models import Lesson, LessonCompletion
from assignments.models import AssignmentSubmission
from notifications.models import Notification
from .models import Widget, DashboardLayout, WidgetDataCache

# Общие функции
def format_date(date):
    """Форматирует дату в человекочитаемый вид"""
    today = timezone.now().date()
    date_obj = date.date() if hasattr(date, 'date') else date
    
    if date_obj == today:
        return f"Сегодня, {date.strftime('%H:%M')}"
    elif date_obj == today - timedelta(days=1):
        return f"Вчера, {date.strftime('%H:%M')}"
    else:
        return date.strftime('%d.%m.%Y, %H:%M')

# API эндпоинты для дашборда
@login_required
def get_statistics(request):
    """API-эндпоинт для получения общей статистики пользователя"""
    user = request.user
    
    # Количество завершенных уроков
    completed_lessons = LessonCompletion.objects.filter(user=user).count()
    
    # Количество заработанных достижений
    earned_achievements = UserAchievement.objects.filter(user=user).count()
    
    # Количество записанных курсов
    enrolled_courses = Enrollment.objects.filter(user=user).count()
    
    # Общее количество очков (используем достижения как источник очков)
    total_points = UserAchievement.objects.filter(user=user).aggregate(
        Sum('achievement__points'))['achievement__points__sum'] or 0
    
    # Рассчитываем тренды (на самом деле это будет имитация, потому что у нас нет истории)
    # В реальной системе здесь будет анализ данных за предыдущие периоды
    
    # Случайные тренды для демонстрации UI (в реальной системе здесь будет анализ данных)
    lessons_trend = random.randint(2, 15)
    achievements_trend = random.randint(0, 10)
    points_trend = random.randint(10, 100)
    
    return JsonResponse({
        'completed_lessons': completed_lessons,
        'earned_achievements': earned_achievements,
        'enrolled_courses': enrolled_courses,
        'total_points': total_points,
        'lessons_trend': lessons_trend,
        'achievements_trend': achievements_trend,
        'points_trend': points_trend
    })

@login_required
def get_courses_progress(request):
    """API-эндпоинт для получения прогресса по курсам пользователя"""
    user = request.user
    
    enrollments = Enrollment.objects.filter(user=user)
    courses_data = []
    
    for enrollment in enrollments:
        course = enrollment.course
        
        # Получаем все уроки курса, которые опубликованы
        total_lessons = Lesson.objects.filter(
            lesson_content__module__course=course, 
            is_published=True
        ).count()
        
        # Получаем завершенные уроки пользователя
        completed_lessons = LessonCompletion.objects.filter(
            user=user, 
            lesson__lesson_content__module__course=course
        ).count()
        
        # Вычисляем процент прогресса
        if total_lessons > 0:
            progress_percent = int((completed_lessons / total_lessons) * 100)
        else:
            progress_percent = 0
        
        courses_data.append({
            'id': course.id,
            'title': course.title,
            'slug': course.slug,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percent': progress_percent
        })
    
    # Сортируем курсы по проценту прогресса (в порядке убывания)
    courses_data.sort(key=lambda x: x['progress_percent'], reverse=True)
    
    return JsonResponse({
        'courses': courses_data
    })

@login_required
def get_recent_activity(request):
    """API-эндпоинт для получения недавней активности пользователя"""
    user = request.user
    
    # Получаем недавние уведомления
    recent_notifications = Notification.objects.filter(
        user=user
    ).order_by('-created_at')[:10]
    
    activities = []
    
    for notification in recent_notifications:
        activities.append({
            'id': notification.id,
            'type': notification.notification_type,
            'message': notification.message,
            'date': format_date(notification.created_at),
            'is_read': notification.is_read
        })
    
    # Получаем недавно заработанные достижения
    recent_achievements = UserAchievement.objects.filter(
        user=user
    ).order_by('-earned_at')[:5]
    
    for achievement in recent_achievements:
        # Проверяем, нет ли уже уведомления об этом достижении
        if not any(a['type'] == 'achievement_earned' and achievement.achievement.name in a['message'] for a in activities):
            activities.append({
                'id': f"achievement_{achievement.id}",
                'type': 'achievement_earned',
                'message': f'Получено достижение "{achievement.achievement.name}"',
                'date': format_date(achievement.earned_at),
                'is_read': True
            })
    
    # Получаем недавно завершенные уроки, если их еще нет в уведомлениях
    recent_completions = LessonCompletion.objects.filter(
        user=user
    ).order_by('-completed_at')[:5]
    
    for completion in recent_completions:
        # Проверяем, нет ли уже уведомления об этом завершении урока
        if completion.completed_at and not any(a['type'] == 'lesson_completed' and completion.lesson.title in a['message'] for a in activities):
            activities.append({
                'id': f"lesson_{completion.id}",
                'type': 'lesson_completed',
                'message': f'Завершен урок "{completion.lesson.title}"',
                'date': format_date(completion.completed_at),
                'is_read': True
            })
    
    # Сортируем по дате
    activities.sort(key=lambda x: datetime.strptime(x['date'].split(', ')[1] if ', ' in x['date'] else x['date'], '%H:%M') 
                   if 'Сегодня' in x['date'] or 'Вчера' in x['date'] 
                   else datetime.strptime(x['date'], '%d.%m.%Y, %H:%M'), 
                   reverse=True)
    
    return JsonResponse({
        'activities': activities[:10]  # Возвращаем только 10 последних
    })

@login_required
def get_achievements(request):
    """API-эндпоинт для получения достижений пользователя"""
    user = request.user
    
    user_achievements = user.achievements.all().order_by('-earned_at')
    
    achievements_data = []
    
    for user_achievement in user_achievements:
        achievement = user_achievement.achievement
        achievements_data.append({
            'id': achievement.id,
            'title': achievement.name,
            'description': achievement.description,
            'icon': achievement.icon.url if achievement.icon else 'fas fa-medal',  # Иконка по умолчанию, если нет
            'earned_at': format_date(user_achievement.earned_at),
            'points': achievement.points
        })
    
    # Получаем все доступные достижения, чтобы показать процент выполнения
    all_achievements = Achievement.objects.all()
    total_achievements = all_achievements.count()
    
    return JsonResponse({
        'achievements': achievements_data,
        'total': total_achievements,
        'earned': len(achievements_data),
        'completion_percentage': int((len(achievements_data) / total_achievements) * 100) if total_achievements > 0 else 0
    })

@login_required
def get_schedule(request):
    """API-эндпоинт для получения расписания пользователя"""
    user = request.user
    
    # Получаем все записанные курсы пользователя
    enrollments = Enrollment.objects.filter(
        user=user
    )
    
    schedule = []
    today = timezone.now().date()
    
    for enrollment in enrollments:
        course = enrollment.course
        
        # Получаем все уроки курса
        lessons = Lesson.objects.filter(
            lesson_content__module__course=course,
            is_published=True
        ).order_by('lesson_content__module__order', 'lesson_content__order')
        
        # Получаем завершенные уроки пользователя
        completed_lessons = LessonCompletion.objects.filter(
            user=user,
            lesson__in=lessons
        ).values_list('lesson_id', flat=True)
        
        # Находим первый незавершенный урок
        next_lesson = None
        for lesson in lessons:
            if lesson.id not in completed_lessons:
                next_lesson = lesson
                break
        
        if next_lesson:
            # Создаем запись в расписании для этого урока
            # В реальном приложении здесь будет использоваться реальное время из расписания
            schedule.append({
                'id': next_lesson.id,
                'title': next_lesson.title,
                'course': course.title,
                'module': next_lesson.lesson_content.module.title,
                'url': f'/lessons/{next_lesson.id}/',
                'time': f"{random.randint(10, 18)}:{random.choice(['00', '30'])}",  # Случайное время для демонстрации
                'date': today.strftime('%d.%m.%Y')
            })
    
    # Сортируем расписание по времени
    schedule.sort(key=lambda x: x['time'])
    
    return JsonResponse({
        'schedule': schedule
    })

@login_required
def get_leaderboard(request):
    """API-эндпоинт для получения рейтинга пользователей"""
    # Подсчитываем общее количество очков для каждого пользователя на основе достижений
    top_users = CustomUser.objects.annotate(
        points=Sum('achievements__achievement__points')
    ).filter(
        points__isnull=False
    ).order_by('-points')[:10]
    
    current_user = request.user
    leaderboard = []
    
    for i, user in enumerate(top_users, 1):
        is_current_user = user.id == current_user.id
        
        leaderboard.append({
            'rank': i,
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'points': user.points or 0,
            'is_current_user': is_current_user
        })
    
    # Если текущего пользователя нет в топ-10, добавляем его
    if not any(item['is_current_user'] for item in leaderboard):
        # Получаем позицию текущего пользователя в общем рейтинге
        current_user_points = UserAchievement.objects.filter(user=current_user).aggregate(
            Sum('achievement__points'))['achievement__points__sum'] or 0
        
        # Подсчитываем его ранг
        higher_users_count = CustomUser.objects.annotate(
            points=Sum('achievements__achievement__points')
        ).filter(
            points__gt=current_user_points
        ).count()
        
        current_user_rank = higher_users_count + 1
        
        # Добавляем пользователя в конец списка
        leaderboard.append({
            'rank': current_user_rank,
            'username': current_user.username,
            'full_name': f"{current_user.first_name} {current_user.last_name}".strip() or current_user.username,
            'points': current_user_points,
            'is_current_user': True
        })
    
    return JsonResponse({
        'leaderboard': leaderboard
    })

@login_required
def get_goals(request):
    """API-эндпоинт для получения целей обучения пользователя"""
    user = request.user
    
    # Получаем виджет с целями обучения или создаем его, если его нет
    goals_widget, created = Widget.objects.get_or_create(
        user=user,
        widget_type='goals',
        defaults={
            'title': 'Цели обучения',
            'settings': {'goals': []}
        }
    )
    
    # Получаем цели из настроек виджета
    goals = goals_widget.settings.get('goals', []) if goals_widget.settings else []
    
    return JsonResponse({
        'goals': goals
    })

@login_required
@require_POST
def add_goal(request):
    """API-эндпоинт для добавления новой цели обучения"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        title = data.get('title')
        due_date = data.get('due_date')
        
        if not title:
            return JsonResponse({'success': False, 'error': 'Название цели не может быть пустым'}, status=400)
        
        # Получаем виджет с целями обучения
        goals_widget, created = Widget.objects.get_or_create(
            user=user,
            widget_type='goals',
            defaults={
                'title': 'Цели обучения',
                'settings': {'goals': []}
            }
        )
        
        # Получаем текущие цели и добавляем новую
        goals = goals_widget.settings.get('goals', []) if goals_widget.settings else []
        
        # Создаем новую цель
        new_goal = {
            'id': int(timezone.now().timestamp()),  # Простой уникальный ID
            'title': title,
            'completed': False,
            'created_at': timezone.now().strftime('%d.%m.%Y'),
        }
        
        if due_date:
            new_goal['due_date'] = due_date
        
        goals.append(new_goal)
        
        # Обновляем настройки виджета
        if not goals_widget.settings:
            goals_widget.settings = {}
        
        goals_widget.settings['goals'] = goals
        goals_widget.save()
        
        return JsonResponse({'success': True, 'goal': new_goal})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def toggle_goal(request, goal_id):
    """API-эндпоинт для переключения статуса цели обучения"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        completed = data.get('completed', False)
        
        # Получаем виджет с целями обучения
        goals_widget = Widget.objects.get(user=user, widget_type='goals')
        
        # Получаем текущие цели
        goals = goals_widget.settings.get('goals', []) if goals_widget.settings else []
        
        # Находим цель по ID и обновляем ее статус
        for goal in goals:
            if goal.get('id') == goal_id:
                goal['completed'] = completed
                goal['completed_at'] = timezone.now().strftime('%d.%m.%Y') if completed else None
                break
        
        # Обновляем настройки виджета
        goals_widget.settings['goals'] = goals
        goals_widget.save()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["DELETE"])
def delete_goal(request, goal_id):
    """API-эндпоинт для удаления цели обучения"""
    user = request.user
    
    try:
        # Получаем виджет с целями обучения
        goals_widget = Widget.objects.get(user=user, widget_type='goals')
        
        # Получаем текущие цели
        goals = goals_widget.settings.get('goals', []) if goals_widget.settings else []
        
        # Удаляем цель по ID
        goals = [goal for goal in goals if goal.get('id') != goal_id]
        
        # Обновляем настройки виджета
        goals_widget.settings['goals'] = goals
        goals_widget.save()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)