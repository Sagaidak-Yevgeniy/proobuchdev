from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
import json
import datetime
from decimal import Decimal
from django.utils import timezone

from courses.models import Course, Enrollment
from gamification.models import Achievement, UserAchievement
from users.models import CustomUser
from lessons.models import Lesson, LessonCompletion
from notifications.models import Notification

from .models import Widget, DashboardLayout, WidgetDataCache
from .models_events import Event, EventParticipant
from .models_goals import StudentGoal, GoalStep
from .forms import WidgetForm, DashboardLayoutForm, WidgetPositionForm, WidgetSizeForm


@login_required
def new_dashboard(request):
    """Отображает новый, улучшенный дашборд пользователя"""
    user = request.user
    
    # Получаем базовую информацию о пользователе для приветствия
    context = {
        'user': user,
    }
    
    return render(request, 'dashboard/new_dashboard.html', context)

@login_required
def dashboard(request):
    """Отображает классический дашборд пользователя"""
    user = request.user
    
    # Получаем или создаем макет дашборда пользователя
    dashboard_layout, created = DashboardLayout.objects.get_or_create(
        user=user,
        defaults={
            'theme': 'light',
            'animation_speed': 'normal',
            'layout': {'widgets': []}
        }
    )
    
    # Получаем все виджеты пользователя
    widgets = Widget.objects.filter(user=user, is_active=True)
    
    context = {
        'dashboard_layout': dashboard_layout,
        'widgets': widgets,
        'widget_types': dict(Widget.TYPE_CHOICES),
        'widget_sizes': dict(Widget.SIZE_CHOICES),
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def dashboard_settings(request):
    """Настройки дашборда пользователя"""
    user = request.user
    dashboard_layout, created = DashboardLayout.objects.get_or_create(
        user=user,
        defaults={
            'theme': 'light',
            'animation_speed': 'normal',
            'layout': {'widgets': []}
        }
    )
    
    if request.method == 'POST':
        form = DashboardLayoutForm(request.POST, instance=dashboard_layout)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки дашборда сохранены')
            return redirect('dashboard:index')
    else:
        form = DashboardLayoutForm(instance=dashboard_layout)
    
    context = {
        'form': form,
    }
    
    return render(request, 'dashboard/settings.html', context)


@login_required
def add_widget(request):
    """Добавляет новый виджет на дашборд"""
    if request.method == 'POST':
        form = WidgetForm(request.POST)
        if form.is_valid():
            widget = form.save(commit=False)
            widget.user = request.user
            widget.save()
            
            # Создаем пустой кэш данных
            WidgetDataCache.objects.create(
                widget=widget,
                data={}
            )
            
            messages.success(request, 'Виджет добавлен на дашборд')
            return redirect('dashboard:index')
    else:
        form = WidgetForm()
    
    context = {
        'form': form,
        'action': 'add',
    }
    
    return render(request, 'dashboard/widget_form.html', context)


@login_required
def edit_widget(request, widget_id):
    """Редактирует существующий виджет"""
    widget = get_object_or_404(Widget, id=widget_id, user=request.user)
    
    if request.method == 'POST':
        form = WidgetForm(request.POST, instance=widget)
        if form.is_valid():
            form.save()
            messages.success(request, 'Виджет обновлен')
            return redirect('dashboard:index')
    else:
        form = WidgetForm(instance=widget)
    
    context = {
        'form': form,
        'widget': widget,
        'action': 'edit',
    }
    
    return render(request, 'dashboard/widget_form.html', context)


@login_required
def delete_widget(request, widget_id):
    """Удаляет виджет с дашборда"""
    widget = get_object_or_404(Widget, id=widget_id, user=request.user)
    
    if request.method == 'POST':
        widget.delete()
        messages.success(request, 'Виджет удален')
        return redirect('dashboard:index')
    
    context = {
        'widget': widget,
    }
    
    return render(request, 'dashboard/widget_confirm_delete.html', context)


@login_required
@require_POST
def update_widget_position(request, widget_id):
    """Обновляет позицию виджета на дашборде"""
    widget = get_object_or_404(Widget, id=widget_id, user=request.user)
    
    form = WidgetPositionForm(request.POST)
    if form.is_valid():
        widget.position_x = form.cleaned_data['position_x']
        widget.position_y = form.cleaned_data['position_y']
        widget.save()
        return JsonResponse({'status': 'ok'})
    
    return HttpResponseBadRequest('Invalid form data')


@login_required
@require_POST
def update_widget_size(request, widget_id):
    """Обновляет размер виджета на дашборде"""
    widget = get_object_or_404(Widget, id=widget_id, user=request.user)
    
    form = WidgetSizeForm(request.POST)
    if form.is_valid():
        widget.size = form.cleaned_data['size']
        widget.save()
        return JsonResponse({'status': 'ok'})
    
    return HttpResponseBadRequest('Invalid form data')


@login_required
@csrf_exempt
@require_POST
def save_layout(request):
    """Сохраняет макет дашборда"""
    user = request.user
    
    try:
        layout_data = json.loads(request.body)
        dashboard_layout = DashboardLayout.objects.get(user=user)
        dashboard_layout.layout = layout_data
        dashboard_layout.save()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@login_required
def get_widget_data(request, widget_id):
    """Возвращает данные для виджета"""
    widget = get_object_or_404(Widget, id=widget_id, user=request.user)
    
    # Пытаемся получить данные из кэша
    try:
        cache = WidgetDataCache.objects.get(widget=widget)
        # Если кэш достаточно свежий (например, обновлен не более 5 минут назад)
        if (datetime.datetime.now().astimezone() - cache.last_updated).total_seconds() < 300:
            return JsonResponse(cache.data)
    except WidgetDataCache.DoesNotExist:
        # Если кэша нет, создаем новый
        cache = WidgetDataCache.objects.create(widget=widget, data={})
    
    # Получаем свежие данные для виджета в зависимости от его типа
    data = {}
    
    if widget.widget_type == 'courses_progress':
        data = get_courses_progress_data(request.user)
    elif widget.widget_type == 'achievements':
        data = get_achievements_data(request.user)
    elif widget.widget_type == 'recent_activity':
        data = get_recent_activity_data(request.user)
    elif widget.widget_type == 'statistics':
        data = get_statistics_data(request.user)
    elif widget.widget_type == 'leaderboard':
        data = get_leaderboard_data()
    elif widget.widget_type == 'upcoming_lessons':
        data = get_upcoming_lessons_data(request.user)
    elif widget.widget_type == 'goals':
        data = get_goals_data(request.user)
    elif widget.widget_type == 'study_time':
        data = get_study_time_data(request.user)
    elif widget.widget_type == 'calendar':
        data = get_calendar_data(request.user)
    elif widget.widget_type == 'notes':
        data = get_notes_data(request.user)
    
    # Обновляем кэш
    cache.data = data
    cache.save()
    
    return JsonResponse(data)


# Вспомогательные функции для получения данных для виджетов

def get_courses_progress_data(user):
    """Получает данные о прогрессе по курсам пользователя"""
    enrollments = Enrollment.objects.filter(user=user, is_active=True)
    courses_data = []
    
    for enrollment in enrollments:
        course = enrollment.course
        total_lessons = Lesson.objects.filter(
            lesson_content__module__course=course, 
            is_published=True
        ).count()
        
        completed_lessons = LessonCompletion.objects.filter(
            user=user, 
            lesson__lesson_content__module__course=course
        ).count()
        
        if total_lessons > 0:
            progress_percent = int((completed_lessons / total_lessons) * 100)
        else:
            progress_percent = 0
        
        courses_data.append({
            'id': course.id,
            'title': course.title,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percent': progress_percent
        })
    
    return {
        'courses': courses_data
    }


def get_achievements_data(user):
    """Получает данные о достижениях пользователя"""
    user_achievements = UserAchievement.objects.filter(user=user)
    earned_achievements = []
    
    for user_achievement in user_achievements:
        earned_achievements.append({
            'id': user_achievement.achievement.id,
            'title': user_achievement.achievement.title,
            'description': user_achievement.achievement.description,
            'icon': user_achievement.achievement.icon_url if user_achievement.achievement.icon else None,
            'earned_at': user_achievement.earned_at.strftime('%d.%m.%Y')
        })
    
    # Получаем все доступные достижения, чтобы показать, какие еще не заработаны
    all_achievements = Achievement.objects.all()
    total_achievements = all_achievements.count()
    
    return {
        'achievements': earned_achievements,
        'total': total_achievements,
        'earned': len(earned_achievements)
    }


def get_recent_activity_data(user):
    """Получает данные о недавней активности пользователя"""
    # Получаем недавние уведомления
    recent_notifications = Notification.objects.filter(
        recipient=user
    ).order_by('-created_at')[:10]
    
    activities = []
    
    for notification in recent_notifications:
        activities.append({
            'type': notification.notification_type,
            'message': notification.message,
            'date': notification.created_at.strftime('%d.%m.%Y %H:%M'),
            'is_read': notification.is_read
        })
    
    # Получаем недавно заработанные достижения
    recent_achievements = UserAchievement.objects.filter(
        user=user
    ).order_by('-earned_at')[:5]
    
    for achievement in recent_achievements:
        if any(a['type'] == 'achievement_earned' and a['message'].find(achievement.achievement.title) != -1 for a in activities):
            continue
            
        activities.append({
            'type': 'achievement_earned',
            'message': f'Вы получили достижение "{achievement.achievement.title}"',
            'date': achievement.earned_at.strftime('%d.%m.%Y %H:%M'),
            'is_read': True
        })
    
    # Сортируем по дате
    activities.sort(key=lambda x: datetime.datetime.strptime(x['date'], '%d.%m.%Y %H:%M'), reverse=True)
    
    return {
        'activities': activities[:10]  # Возвращаем только 10 последних
    }


def get_statistics_data(user):
    """Получает статистические данные для пользователя"""
    # Количество завершенных уроков
    completed_lessons_count = LessonCompletion.objects.filter(user=user).count()
    
    # Количество заработанных достижений
    earned_achievements_count = UserAchievement.objects.filter(user=user).count()
    
    # Количество записанных курсов
    enrolled_courses_count = Enrollment.objects.filter(user=user, is_active=True).count()
    
    # Средний прогресс по курсам
    enrollments = Enrollment.objects.filter(user=user, is_active=True)
    total_progress = 0
    
    for enrollment in enrollments:
        course = enrollment.course
        total_lessons = Lesson.objects.filter(
            lesson_content__module__course=course,
            is_published=True
        ).count()
        
        if total_lessons > 0:
            completed_lessons = LessonCompletion.objects.filter(
                user=user,
                lesson__lesson_content__module__course=course
            ).count()
            
            progress = (completed_lessons / total_lessons) * 100
            total_progress += progress
    
    avg_progress = int(total_progress / enrollments.count()) if enrollments.count() > 0 else 0
    
    return {
        'completed_lessons': completed_lessons_count,
        'earned_achievements': earned_achievements_count,
        'enrolled_courses': enrolled_courses_count,
        'avg_progress': avg_progress
    }


def get_leaderboard_data():
    """Получает данные для таблицы лидеров"""
    # Подсчитываем рейтинг пользователей по количеству заработанных достижений
    from django.db.models import Count
    
    top_users = CustomUser.objects.annotate(
        achievements_count=Count('user_achievements')
    ).filter(
        achievements_count__gt=0
    ).order_by('-achievements_count')[:10]
    
    leaderboard = []
    
    for i, user in enumerate(top_users, 1):
        leaderboard.append({
            'rank': i,
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'achievements_count': user.achievements_count
        })
    
    return {
        'leaderboard': leaderboard
    }


def get_upcoming_lessons_data(user):
    """Получает данные о предстоящих уроках"""
    # Получаем все курсы пользователя
    enrollments = Enrollment.objects.filter(user=user, is_active=True)
    upcoming_lessons = []
    
    for enrollment in enrollments:
        course = enrollment.course
        
        # Получаем все уроки курса
        lessons = Lesson.objects.filter(
            lesson_content__module__course=course,
            is_published=True
        ).order_by('lesson_content__module__order', 'lesson_content__order')
        
        # Получаем завершенные уроки
        completed_lessons = LessonCompletion.objects.filter(
            user=user,
            lesson__lesson_content__module__course=course
        ).values_list('lesson_id', flat=True)
        
        # Находим первый незавершенный урок
        for lesson in lessons:
            if lesson.id not in completed_lessons:
                upcoming_lessons.append({
                    'course_title': course.title,
                    'lesson_title': lesson.title,
                    'lesson_url': reverse('lessons:detail', args=[lesson.id]),
                    'module_title': lesson.lesson_content.module.title
                })
                break
    
    return {
        'upcoming_lessons': upcoming_lessons
    }


def get_goals_data(user):
    """Получает данные о целях обучения пользователя"""
    # Получаем все цели пользователя
    student_goals = StudentGoal.objects.filter(user=user)
    
    active_goals = student_goals.filter(is_completed=False).count()
    completed_goals = student_goals.filter(is_completed=True).count()
    overdue_goals = sum(1 for goal in student_goals if goal.is_overdue)
    
    goals_data = []
    
    for goal in student_goals:
        # Получаем все шаги для цели
        steps = []
        for step in goal.steps.all().order_by('order'):
            steps.append({
                'id': step.id,
                'title': step.title,
                'description': step.description,
                'order': step.order,
                'is_completed': step.is_completed,
                'completed_at': step.completed_at.strftime('%Y-%m-%d %H:%M:%S') if step.completed_at else None
            })
        
        goals_data.append({
            'id': goal.id,
            'title': goal.title,
            'description': goal.description,
            'goal_type': goal.goal_type,
            'goal_type_display': goal.get_goal_type_display(),
            'priority': goal.priority,
            'priority_display': goal.get_priority_display(),
            'created_at': goal.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'due_date': goal.due_date.strftime('%Y-%m-%d') if goal.due_date else None,
            'is_completed': goal.is_completed,
            'completed_at': goal.completed_at.strftime('%Y-%m-%d %H:%M:%S') if goal.completed_at else None,
            'progress': goal.progress,
            'is_overdue': goal.is_overdue,
            'days_left': goal.days_left,
            'course': {
                'id': goal.course.id,
                'title': goal.course.title,
                'slug': goal.course.slug
            } if goal.course else None,
            'steps': steps
        })
    
    return {
        'goals': goals_data,
        'total': len(goals_data),
        'active': active_goals,
        'completed': completed_goals,
        'overdue': overdue_goals
    }


def get_study_time_data(user):
    """Получает данные о времени обучения пользователя"""
    # Здесь могла бы быть логика для получения фактического времени обучения
    # Пока что заглушка с примерами данных
    
    # Получаем время из настроек виджета пользователя, если он их сохранил
    widget = Widget.objects.filter(user=user, widget_type='study_time').first()
    
    study_time = {}
    if widget and widget.settings and 'study_time' in widget.settings:
        study_time = widget.settings['study_time']
    
    # Если данных нет или виджет не настроен, добавляем примеры
    if not study_time:
        # Генерируем данные для последних 7 дней
        today = datetime.datetime.now().date()
        days = []
        
        for i in range(7):
            day = today - datetime.timedelta(days=i)
            days.append({
                'date': day.strftime('%d.%m.%Y'),
                'day_of_week': day.strftime('%a'),
                'hours': round(Decimal(str(2 + (i % 3))), 1)  # Случайное число часов от 2 до 4
            })
        
        days.reverse()  # Для хронологического порядка
        
        study_time = {
            'days': days,
            'total_hours': sum(day['hours'] for day in days),
            'avg_hours': round(sum(day['hours'] for day in days) / len(days), 1)
        }
    
    return {
        'study_time': study_time
    }


def get_calendar_data(user):
    """Получает данные календаря событий"""
    # Получаем события из модели
    now = timezone.now()
    
    # Получаем активные события (текущие и будущие)
    upcoming_events = Event.objects.filter(
        end_time__gte=now,
        is_public=True
    ).order_by('start_time')
    
    # Получаем события, созданные пользователем
    user_events = Event.objects.filter(
        created_by=user
    ).exclude(
        id__in=upcoming_events.values_list('id', flat=True)
    ).order_by('start_time')
    
    # Получаем события, в которых пользователь является участником
    participation_events = Event.objects.filter(
        participants__user=user
    ).exclude(
        id__in=upcoming_events.values_list('id', flat=True)
    ).exclude(
        id__in=user_events.values_list('id', flat=True)
    ).order_by('start_time')
    
    # Объединяем события (без дубликатов)
    events_list = list(upcoming_events) + list(user_events) + list(participation_events)
    
    # Преобразуем события в формат для виджета
    events_data = []
    for event in events_list:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'date': event.start_time.strftime('%d.%m.%Y'),
            'time': event.start_time.strftime('%H:%M'),
            'end_time': event.end_time.strftime('%H:%M'),
            'description': event.description[:100] + ('...' if len(event.description) > 100 else ''),
            'location': event.location,
            'url': event.url,
            'event_type': event.get_event_type_display(),
            'is_past': event.is_past,
            'is_ongoing': event.is_ongoing,
            'is_owner': event.created_by.id == user.id
        })
    
    return {
        'events': sorted(events_data, key=lambda x: datetime.datetime.strptime(x['date'] + ' ' + x['time'], '%d.%m.%Y %H:%M'))
    }


def get_notes_data(user):
    """Получает данные заметок пользователя"""
    # Здесь могла бы быть логика для получения фактических заметок
    # Пока что заглушка с примерами заметок
    
    # Получаем заметки из настроек виджета пользователя, если он их сохранил
    widget = Widget.objects.filter(user=user, widget_type='notes').first()
    
    notes = []
    if widget and widget.settings and 'notes' in widget.settings:
        notes = widget.settings['notes']
    
    # Если заметок нет или виджет не настроен, добавляем примеры
    if not notes:
        notes = [
            {
                'id': 1,
                'title': 'Полезные ресурсы',
                'content': 'Документация Python: docs.python.org\nУроки по Django: djangoproject.com',
                'date': datetime.datetime.now().strftime('%d.%m.%Y'),
                'color': 'blue'
            },
            {
                'id': 2,
                'title': 'Важные команды Git',
                'content': 'git add .\ngit commit -m "Сообщение"\ngit push origin main',
                'date': datetime.datetime.now().strftime('%d.%m.%Y'),
                'color': 'green'
            }
        ]
    
    return {
        'notes': notes
    }


# Представления для работы с мероприятиями и целями

@login_required
def events_list(request):
    """Отображает страницу со списком мероприятий"""
    user = request.user
    
    context = {
        'user': user,
        'page_title': 'Мероприятия'
    }
    
    return render(request, 'dashboard/events.html', context)


@login_required
def goals_list(request):
    """Отображает страницу со списком целей обучения"""
    user = request.user
    
    context = {
        'user': user,
        'page_title': 'Цели обучения'
    }
    
    return render(request, 'dashboard/goals.html', context)