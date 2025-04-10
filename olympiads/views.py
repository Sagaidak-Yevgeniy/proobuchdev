from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, Max, Avg
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt

from .code_runner import format_code as format_code_function
from .forms import OlympiadForm, ProblemForm, TestCaseForm, SubmissionForm
from .models import (
    Olympiad, OlympiadTask, OlympiadParticipation, OlympiadTaskSubmission,
    OlympiadInvitation, OlympiadUserInvitation, OlympiadMultipleChoiceOption,
    OlympiadTestCase, OlympiadCertificate
)
from users.models import CustomUser
from courses.models import Course

import json
import datetime
import random
import string

def generate_random_code(length=8):
    """Генерирует случайный код для приглашения"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# Просмотр списка олимпиад
def olympiad_list(request):
    now = timezone.now()
    
    # Параметры фильтрации
    search_query = request.GET.get('search', '')
    filter_status = request.GET.get('status', '')
    
    # Базовый запрос
    olympiads_query = Olympiad.objects
    
    # Применяем поисковый запрос, если он есть
    if search_query:
        olympiads_query = olympiads_query.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    # Фильтр по статусу
    if filter_status == 'upcoming':
        # Только предстоящие
        olympiads = olympiads_query.filter(
            Q(status=Olympiad.OlympiadStatus.PUBLISHED) & 
            Q(start_datetime__gt=now)
        ).order_by('start_datetime')
        
        upcoming_olympiads = olympiads
        active_olympiads = []
        completed_olympiads = []
    elif filter_status == 'active':
        # Только активные
        # Олимпиада активна если:
        # 1. Статус ACTIVE и время проведения не истекло
        # 2. Или статус PUBLISHED, начало уже наступило, а конец еще не наступил
        olympiads = olympiads_query.filter(
            Q(status=Olympiad.OlympiadStatus.ACTIVE, end_datetime__gte=now) |
            Q(status=Olympiad.OlympiadStatus.PUBLISHED, start_datetime__lte=now, end_datetime__gte=now)
        ).order_by('end_datetime')
        
        upcoming_olympiads = []
        active_olympiads = olympiads
        completed_olympiads = []
    elif filter_status == 'completed':
        # Только завершенные
        # Олимпиада завершена если:
        # 1. Статус COMPLETED
        # 2. Или статус ACTIVE и время окончания уже наступило
        # 3. Или статус PUBLISHED и время окончания уже наступило
        olympiads = olympiads_query.filter(
            Q(status=Olympiad.OlympiadStatus.COMPLETED) | 
            Q(status=Olympiad.OlympiadStatus.ACTIVE, end_datetime__lt=now) |
            Q(status=Olympiad.OlympiadStatus.PUBLISHED, end_datetime__lt=now)
        ).order_by('-end_datetime')
        
        upcoming_olympiads = []
        active_olympiads = []
        completed_olympiads = olympiads
    else:
        # Без фильтра показываем все категории
        # Предстоящие олимпиады
        upcoming_olympiads = olympiads_query.filter(
            Q(status=Olympiad.OlympiadStatus.PUBLISHED) & 
            Q(start_datetime__gt=now)
        ).order_by('start_datetime')
        
        # Активные олимпиады
        active_olympiads = olympiads_query.filter(
            Q(status=Olympiad.OlympiadStatus.ACTIVE, end_datetime__gte=now) |
            Q(status=Olympiad.OlympiadStatus.PUBLISHED, start_datetime__lte=now, end_datetime__gte=now)
        ).order_by('end_datetime')
        
        # Завершенные олимпиады
        completed_olympiads = olympiads_query.filter(
            Q(status=Olympiad.OlympiadStatus.COMPLETED) | 
            Q(status=Olympiad.OlympiadStatus.ACTIVE, end_datetime__lt=now) |
            Q(status=Olympiad.OlympiadStatus.PUBLISHED, end_datetime__lt=now)
        ).order_by('-end_datetime')[:10]
    
    # Если пользователь авторизован, добавляем информацию об участии
    if request.user.is_authenticated:
        user_participations = OlympiadParticipation.objects.filter(user=request.user)
        user_participation_ids = {p.olympiad_id for p in user_participations}
        
        # Временное решение: отключаем приглашения до выполнения миграции
        user_invitations = []
        user_invitation_ids = set()
    else:
        user_participation_ids = set()
        user_invitation_ids = set()
    
    context = {
        'upcoming_olympiads': upcoming_olympiads,
        'active_olympiads': active_olympiads,
        'completed_olympiads': completed_olympiads,
        'user_participation_ids': user_participation_ids,
        'user_invitation_ids': user_invitation_ids,
        'search_query': search_query,
        'filter_status': filter_status
    }
    
    return render(request, 'olympiads/olympiad_list.html', context)

# Просмотр деталей олимпиады
def olympiad_detail(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    now = timezone.now()
    
    # Определяем статус олимпиады для текущего пользователя
    user_participation = None
    user_invitation = None
    can_register = False
    
    if request.user.is_authenticated:
        user_participation = OlympiadParticipation.objects.filter(
            olympiad=olympiad,
            user=request.user
        ).first()
        
        # Временно отключено из-за проблем с моделью
        # user_invitation = OlympiadUserInvitation.objects.filter(
        #    olympiad=olympiad,
        #    user=request.user,
        #    is_accepted=False
        # ).first()
        user_invitation = None
        
        # Пользователь может зарегистрироваться, если:
        # 1. Олимпиада еще не началась
        # 2. Олимпиада открытая или пользователь приглашен
        # 3. Пользователь еще не зарегистрирован
        if olympiad.start_datetime > now and not user_participation:
            if olympiad.is_open or user_invitation:
                can_register = True
    
    # Подсчитываем общее количество заданий и баллов
    task_count = olympiad.tasks.count()
    total_points = olympiad.tasks.aggregate(total=Sum('points'))['total'] or 0
    
    # Получаем топ-5 участников
    top_participants = OlympiadParticipation.objects.filter(
        olympiad=olympiad,
        is_completed=True
    ).order_by('-score')[:5]
    
    # Добавляем состояние олимпиады в контекст для улучшения работы шаблона
    olympiad_is_active = olympiad.is_active()
    olympiad_is_completed = olympiad.is_completed()
    olympiad_has_started = olympiad.has_started()
    olympiad_is_upcoming = olympiad.is_upcoming()
    
    context = {
        'olympiad': olympiad,
        'user_participation': user_participation,
        'user_invitation': user_invitation,
        'can_register': can_register,
        'task_count': task_count,
        'total_points': total_points,
        'top_participants': top_participants,
        'now': now,
        'olympiad_is_active': olympiad_is_active,
        'olympiad_is_completed': olympiad_is_completed, 
        'olympiad_has_started': olympiad_has_started,
        'olympiad_is_upcoming': olympiad_is_upcoming
    }
    
    return render(request, 'olympiads/olympiad_detail.html', context)

# Регистрация на олимпиаду
@login_required
def olympiad_register(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    now = timezone.now()
    
    # Проверяем, может ли пользователь зарегистрироваться
    if olympiad.start_datetime <= now:
        messages.error(request, _('Регистрация на эту олимпиаду уже закрыта'))
        return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)
    
    # Проверяем, не зарегистрирован ли пользователь уже
    if OlympiadParticipation.objects.filter(olympiad=olympiad, user=request.user).exists():
        messages.info(request, _('Вы уже зарегистрированы на эту олимпиаду'))
        return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)
    
    # Проверяем, открытая ли олимпиада
    if not olympiad.is_open:
        # Временное решение: разрешаем регистрацию на все олимпиады
        # до восстановления функциональности приглашений
        pass
        
        # Оригинальный код:
        # invitation = OlympiadUserInvitation.objects.filter(
        #     olympiad=olympiad,
        #     user=request.user,
        #     is_accepted=False
        # ).first()
        # 
        # if not invitation:
        #     messages.error(request, _('Эта олимпиада закрыта для регистрации'))
        #     return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)
        # 
        # invitation.is_accepted = True
        # invitation.save()
    
    # Регистрируем пользователя
    max_score = olympiad.tasks.aggregate(total=Sum('points'))['total'] or 0
    
    OlympiadParticipation.objects.create(
        olympiad=olympiad,
        user=request.user,
        max_score=max_score
    )
    
    messages.success(request, _('Вы успешно зарегистрировались на олимпиаду'))
    
    # Если олимпиада уже началась, перенаправляем на страницу с заданиями
    if olympiad.has_started() and olympiad.is_active():
        return redirect('olympiads:olympiad_tasks', olympiad_id=olympiad.id)
    else:
        return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)

# Просмотр заданий олимпиады
@login_required
def olympiad_tasks(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем, зарегистрирован ли пользователь
    participation = get_object_or_404(
        OlympiadParticipation, 
        olympiad=olympiad,
        user=request.user
    )
    
    now = timezone.now()
    
    # Проверяем, началась ли олимпиада
    if olympiad.start_datetime > now:
        messages.error(request, _('Олимпиада еще не началась'))
        return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)
    
    # Проверяем, не завершил ли пользователь олимпиаду
    if participation.is_completed:
        messages.info(request, _('Вы уже завершили эту олимпиаду'))
        return redirect('olympiads:olympiad_results', olympiad_id=olympiad.id)
    
    # Проверяем, не истекло ли время
    if olympiad.end_datetime < now:
        participation.is_completed = True
        participation.finished_at = now
        participation.save()
        
        messages.info(request, _('Время олимпиады истекло'))
        return redirect('olympiads:olympiad_results', olympiad_id=olympiad.id)
    
    # Если установлен лимит времени, проверяем, не истекло ли время для конкретного участника
    if olympiad.time_limit_minutes > 0:
        time_passed = (now - participation.started_at).total_seconds() / 60
        
        if time_passed >= olympiad.time_limit_minutes:
            participation.is_completed = True
            participation.finished_at = participation.started_at + timezone.timedelta(minutes=olympiad.time_limit_minutes)
            participation.save()
            
            messages.info(request, _('Ваше время на выполнение олимпиады истекло'))
            return redirect('olympiads:olympiad_results', olympiad_id=olympiad.id)
        
        # Сколько времени осталось
        time_left = olympiad.time_limit_minutes - time_passed
    else:
        # Сколько времени осталось до конца олимпиады
        time_left = (olympiad.end_datetime - now).total_seconds() / 60
    
    # Получаем все задания олимпиады в порядке их выполнения
    all_tasks = olympiad.tasks.all().order_by('order')
    
    # Определяем, какие задания доступны участнику
    available_tasks = []
    current_task = None
    next_task_locked = False
    
    # Подсчитываем статистику выполнения заданий
    completed_tasks = 0
    total_score = 0
    
    # Для каждого задания получаем информацию о сдаче и доступности
    task_statuses = {}
    
    for task in all_tasks:
        # Получаем последнюю отправку для задания
        submission = OlympiadTaskSubmission.objects.filter(
            participation=participation,
            task=task
        ).order_by('-submitted_at').first()
        
        is_correct = submission.is_correct if submission else False
        has_submission = submission is not None
        score = submission.score if submission else 0
        
        if is_correct:
            completed_tasks += 1
            total_score += score
        
        # Первое задание всегда доступно
        if len(available_tasks) == 0:
            available = True
        # Последующие задания доступны только если предыдущее выполнено правильно
        elif next_task_locked:
            available = False
        else:
            # Если предыдущее задание решено правильно, открываем следующее
            prev_task = available_tasks[-1]
            prev_submission = OlympiadTaskSubmission.objects.filter(
                participation=participation,
                task=prev_task
            ).order_by('-submitted_at').first()
            
            if prev_submission and prev_submission.is_correct:
                available = True
            else:
                available = False
                next_task_locked = True
        
        # Добавляем информацию о доступности задания
        task_statuses[task.id] = {
            'submitted': has_submission,
            'is_correct': is_correct,
            'score': score,
            'submission_id': submission.id if submission else None,
            'available': available
        }
        
        # Если задание доступно, добавляем его в список
        if available:
            available_tasks.append(task)
            # Если ещё нет выбранного текущего задания или предыдущее задание
            # ещё не решено правильно, устанавливаем его как текущее
            if current_task is None or not is_correct:
                current_task = task
    
    # Если нет текущего задания, выбираем первое доступное
    if current_task is None and available_tasks:
        current_task = available_tasks[0]
    
    # Вычисляем прогресс выполнения олимпиады
    progress = {
        'completed': completed_tasks,
        'total': all_tasks.count(),
        'percent': int(completed_tasks / max(1, all_tasks.count()) * 100)
    }
    
    # Добавляем состояние олимпиады в контекст для улучшения работы шаблона
    olympiad_is_active = olympiad.is_active()
    olympiad_is_completed = olympiad.is_completed()
    olympiad_has_started = olympiad.has_started()
    olympiad_is_upcoming = olympiad.is_upcoming()
    
    context = {
        'olympiad': olympiad,
        'participation': participation,
        'tasks': all_tasks,
        'available_tasks': available_tasks,
        'task_statuses': task_statuses,
        'current_task': current_task,
        'time_left_minutes': int(time_left),
        'progress': progress,
        'olympiad_is_active': olympiad_is_active,
        'olympiad_is_completed': olympiad_is_completed, 
        'olympiad_has_started': olympiad_has_started,
        'olympiad_is_upcoming': olympiad_is_upcoming
    }
    
    return render(request, 'olympiads/olympiad_tasks.html', context)

# Просмотр детальной информации о задании
@login_required
def olympiad_task_detail(request, olympiad_id, task_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    task = get_object_or_404(OlympiadTask, id=task_id, olympiad=olympiad)
    
    # Проверяем, зарегистрирован ли пользователь
    participation = get_object_or_404(
        OlympiadParticipation, 
        olympiad=olympiad,
        user=request.user
    )
    
    now = timezone.now()
    
    # Проверяем, не завершил ли пользователь олимпиаду
    if participation.is_completed:
        messages.info(request, _('Вы уже завершили эту олимпиаду'))
        return redirect('olympiads:olympiad_results', olympiad_id=olympiad.id)
    
    # Проверяем, не истекло ли время
    if olympiad.end_datetime < now:
        participation.is_completed = True
        participation.finished_at = now
        participation.save()
        
        messages.info(request, _('Время олимпиады истекло'))
        return redirect('olympiads:olympiad_results', olympiad_id=olympiad.id)
    
    # Проверяем, доступно ли это задание пользователю
    # Получаем все задания олимпиады
    tasks = olympiad.tasks.all().order_by('order')
    
    # Определяем, какие задания доступны участнику
    task_available = False
    
    if tasks.first().id == task.id:
        # Первое задание всегда доступно
        task_available = True
    else:
        # Находим предыдущее задание
        prev_task = None
        for t in tasks:
            if t.id == task.id:
                break
            prev_task = t
        
        # Проверяем, решено ли предыдущее задание
        if prev_task:
            prev_submission = OlympiadTaskSubmission.objects.filter(
                participation=participation,
                task=prev_task,
                is_correct=True
            ).first()
            
            task_available = prev_submission is not None
    
    # Если задание недоступно, перенаправляем на страницу со списком заданий
    if not task_available:
        messages.error(request, _('Это задание будет доступно после выполнения предыдущего задания'))
        return redirect('olympiads:olympiad_tasks', olympiad_id=olympiad.id)
    
    # Получаем последнюю отправку для этого задания
    submission = OlympiadTaskSubmission.objects.filter(
        participation=participation,
        task=task
    ).order_by('-submitted_at').first()
    
    # Получаем тестовые случаи (только нескрытые)
    test_cases = task.test_cases.filter(is_hidden=False).order_by('order')
    
    # Если задание с выбором вариантов, получаем варианты
    options = None
    if task.task_type == OlympiadTask.TaskType.MULTIPLE_CHOICE:
        options = task.options.all().order_by('order')
    
    # Получаем предыдущее и следующее задание для навигации
    prev_task = None
    next_task = None
    found_current = False
    
    for t in tasks:
        if found_current:
            next_task = t
            break
        elif t.id == task.id:
            found_current = True
        else:
            prev_task = t
    
    # Проверяем, доступно ли следующее задание
    next_task_available = False
    if next_task and submission and submission.is_correct:
        next_task_available = True
    
    # Получаем информацию о прогрессе
    completed_tasks = OlympiadTaskSubmission.objects.filter(
        participation=participation,
        is_correct=True
    ).values('task').distinct().count()
    
    progress = {
        'completed': completed_tasks,
        'total': tasks.count(),
        'percent': int(completed_tasks / max(1, tasks.count()) * 100)
    }
    
    # Получаем информацию о времени
    if olympiad.time_limit_minutes > 0:
        time_passed = (now - participation.started_at).total_seconds() / 60
        time_left = max(0, olympiad.time_limit_minutes - time_passed)
    else:
        time_left = (olympiad.end_datetime - now).total_seconds() / 60
    
    # Для задания типа "программирование" подготавливаем редактор кода
    initial_code = ""
    language = "python"
    
    if task.task_type == OlympiadTask.TaskType.PROGRAMMING:
        if submission:
            initial_code = submission.code
        
        # Настройка URL для редактора кода
        urls = {
            'execute': reverse('olympiads:olympiad_task_execute', args=[olympiad.id, task.id]),
            'save': reverse('olympiads:olympiad_task_save', args=[olympiad.id, task.id]),
            'test': reverse('olympiads:olympiad_task_test', args=[olympiad.id, task.id]),
        }
    else:
        urls = {}
    
    # Добавляем состояние олимпиады в контекст для улучшения работы шаблона
    olympiad_is_active = olympiad.is_active()
    olympiad_is_completed = olympiad.is_completed()
    olympiad_has_started = olympiad.has_started()
    olympiad_is_upcoming = olympiad.is_upcoming()
    
    context = {
        'olympiad': olympiad,
        'participation': participation,
        'task': task,
        'submission': submission,
        'test_cases': test_cases,
        'options': options,
        'prev_task': prev_task,
        'next_task': next_task,
        'next_task_available': next_task_available,
        'progress': progress,
        'time_left_minutes': int(time_left),
        'initial_code': initial_code,
        'language': language,
        'urls': urls,
        'olympiad_is_active': olympiad_is_active,
        'olympiad_is_completed': olympiad_is_completed, 
        'olympiad_has_started': olympiad_has_started,
        'olympiad_is_upcoming': olympiad_is_upcoming
    }
    
    # Используем шаблон olympiad_task.html для отображения задания
    return render(request, 'olympiads/olympiad_task.html', context)

# Отправка решения задания
@login_required
def olympiad_task_submit(request, olympiad_id, task_id):
    if request.method != 'POST':
        return redirect('olympiads:olympiad_task_detail', olympiad_id=olympiad_id, task_id=task_id)
    
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    task = get_object_or_404(OlympiadTask, id=task_id, olympiad=olympiad)
    
    # Проверяем, зарегистрирован ли пользователь
    participation = get_object_or_404(
        OlympiadParticipation, 
        olympiad=olympiad,
        user=request.user
    )
    
    now = timezone.now()
    
    # Проверяем, не завершил ли пользователь олимпиаду
    if participation.is_completed:
        messages.info(request, _('Вы уже завершили эту олимпиаду'))
        return redirect('olympiads:olympiad_results', olympiad_id=olympiad.id)
    
    # Проверяем, не истекло ли время
    if olympiad.end_datetime < now:
        participation.is_completed = True
        participation.finished_at = now
        participation.save()
        
        messages.info(request, _('Время олимпиады истекло'))
        return redirect('olympiads:olympiad_results', olympiad_id=olympiad.id)
    
    # Создаем новую отправку
    submission = OlympiadTaskSubmission(
        participation=participation,
        task=task,
        max_score=task.points
    )
    
    # Обрабатываем тип задания
    if task.task_type == OlympiadTask.TaskType.PROGRAMMING:
        code = request.POST.get('code', '')
        submission.code = code
        
        # Здесь должен быть код для проверки программы
        # Для примера просто считаем, что решение верное, если код непустой
        if code.strip():
            submission.is_correct = True
            submission.score = task.points
            submission.passed_test_cases = task.test_cases.count()
            submission.total_test_cases = task.test_cases.count()
        
    elif task.task_type == OlympiadTask.TaskType.THEORETICAL:
        answer = request.POST.get('answer', '')
        submission.text_answer = answer
        
        # Для теоретического вопроса нужна проверка преподавателем
        # Пока считаем, что ответ не проверен
        submission.is_correct = False
        submission.score = 0
        
    elif task.task_type == OlympiadTask.TaskType.MULTIPLE_CHOICE:
        # Сохраняем отправку сначала без опций
        submission.save()
        
        # Добавляем выбранные опции
        selected_option_ids = request.POST.getlist('options')
        
        if selected_option_ids:
            selected_options = OlympiadMultipleChoiceOption.objects.filter(id__in=selected_option_ids, task=task)
            submission.selected_options.set(selected_options)
            
            # Проверяем правильность ответа
            all_options = task.options.all()
            correct_options = all_options.filter(is_correct=True)
            
            # Считаем ответ правильным, если выбраны все правильные опции и только они
            selected_correct = selected_options.filter(is_correct=True).count()
            selected_incorrect = selected_options.filter(is_correct=False).count()
            
            if selected_correct == correct_options.count() and selected_incorrect == 0:
                submission.is_correct = True
                submission.score = task.points
    
    # Сохраняем отправку
    if task.task_type != OlympiadTask.TaskType.MULTIPLE_CHOICE:
        submission.save()
    
    # Обновляем общий балл участника
    participation.calculate_score()
    
    messages.success(request, _('Решение успешно отправлено!'))
    return redirect('olympiads:olympiad_task_detail', olympiad_id=olympiad.id, task_id=task.id)

# Просмотр результатов олимпиады
@login_required
def olympiad_results(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем, зарегистрирован ли пользователь
    participation = get_object_or_404(
        OlympiadParticipation, 
        olympiad=olympiad,
        user=request.user
    )
    
    # Получаем все задания и отправки
    tasks = olympiad.tasks.all().order_by('order')
    submissions = OlympiadTaskSubmission.objects.filter(
        participation=participation
    )
    
    # Группируем отправки по заданиям
    submission_by_task = {}
    for submission in submissions:
        if submission.task_id not in submission_by_task or submission.submitted_at > submission_by_task[submission.task_id].submitted_at:
            submission_by_task[submission.task_id] = submission
    
    # Формируем данные о результатах
    results = []
    for task in tasks:
        submission = submission_by_task.get(task.id)
        results.append({
            'task': task,
            'submission': submission,
            'is_correct': submission.is_correct if submission else False,
            'score': submission.score if submission else 0,
            'max_score': task.points
        })
    
    # Проверяем, доступен ли сертификат
    has_certificate = False
    certificate = None
    
    if participation.passed:
        certificate = OlympiadCertificate.objects.filter(participation=participation).first()
        has_certificate = certificate is not None
    
    # Получаем топ-10 участников
    top_participants = OlympiadParticipation.objects.filter(
        olympiad=olympiad,
        is_completed=True
    ).order_by('-score')[:10]
    
    # Определяем место пользователя в рейтинге
    if participation.is_completed:
        user_rank = OlympiadParticipation.objects.filter(
            olympiad=olympiad,
            is_completed=True,
            score__gt=participation.score
        ).count() + 1
    else:
        user_rank = None
    
    # Добавляем состояние олимпиады в контекст для улучшения работы шаблона
    olympiad_is_active = olympiad.is_active()
    olympiad_is_completed = olympiad.is_completed()
    olympiad_has_started = olympiad.has_started()
    olympiad_is_upcoming = olympiad.is_upcoming()
    
    context = {
        'olympiad': olympiad,
        'participation': participation,
        'results': results,
        'has_certificate': has_certificate,
        'certificate': certificate,
        'top_participants': top_participants,
        'user_rank': user_rank,
        'olympiad_is_active': olympiad_is_active,
        'olympiad_is_completed': olympiad_is_completed, 
        'olympiad_has_started': olympiad_has_started,
        'olympiad_is_upcoming': olympiad_is_upcoming
    }
    
    return render(request, 'olympiads/olympiad_results.html', context)

# Получение сертификата
@login_required
def olympiad_certificate(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем, зарегистрирован ли пользователь
    participation = get_object_or_404(
        OlympiadParticipation, 
        olympiad=olympiad,
        user=request.user
    )
    
    # Проверяем, имеет ли пользователь сертификат
    if not participation.passed:
        messages.error(request, _('Вы не прошли олимпиаду'))
        return redirect('olympiads:olympiad_results', olympiad_id=olympiad.id)
    
    # Проверяем, есть ли уже сертификат
    certificate = OlympiadCertificate.objects.filter(participation=participation).first()
    
    if certificate:
        # Возвращаем существующий сертификат
        return redirect(certificate.certificate_file.url)
    
    # Создаем новый сертификат
    # Генерируем уникальный ID сертификата
    import uuid
    certificate_id = str(uuid.uuid4())
    
    # Создаем сертификат
    certificate = OlympiadCertificate.objects.create(
        participation=participation,
        certificate_id=certificate_id
    )
    
    # Генерируем PDF-файл сертификата (заглушка)
    # Здесь должен быть код для генерации PDF-сертификата
    
    messages.success(request, _('Сертификат успешно создан!'))
    return redirect('olympiads:olympiad_results', olympiad_id=olympiad.id)

# === Управление олимпиадами (для преподавателей и администраторов) ===

# Список олимпиад для управления
@login_required
def olympiad_manage_list(request):
    # Проверяем права доступа
    if not (request.user.profile.is_teacher or request.user.profile.is_admin):
        messages.error(request, _('У вас нет прав для доступа к этой странице'))
        return redirect('olympiads:olympiad_list')
    
    # Получаем все олимпиады, созданные пользователем
    olympiads = Olympiad.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Для администраторов показываем все олимпиады
    if request.user.profile.is_admin:
        olympiads = Olympiad.objects.all().order_by('-created_at')
    
    context = {
        'olympiads': olympiads
    }
    
    return render(request, 'olympiads/manage/olympiad_list.html', context)

# Создание новой олимпиады
@login_required
def olympiad_create(request):
    # Проверяем права доступа
    if not (request.user.profile.is_teacher or request.user.profile.is_admin):
        messages.error(request, _('У вас нет прав для доступа к этой странице'))
        return redirect('olympiads:olympiad_list')
    
    if request.method == 'POST':
        # Используем ModelForm для обработки данных
        form = OlympiadForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Создаем объект олимпиады, но не сохраняем его в базу
            olympiad = form.save(commit=False)
            # Добавляем автора олимпиады
            olympiad.created_by = request.user
            # Если статус не указан, устанавливаем черновик
            if not olympiad.status:
                olympiad.status = Olympiad.OlympiadStatus.DRAFT
            # Сохраняем олимпиаду в базу
            olympiad.save()
            
            messages.success(request, _('Олимпиада успешно создана!'))
            return redirect('olympiads:olympiad_edit', olympiad_id=olympiad.id)
        else:
            # Если форма не валидна, отображаем её с ошибками
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            
            context = {
                'title': _('Создание олимпиады'),
                'form': form
            }
            return render(request, 'olympiads/olympiad_form.html', context)
    else:
        # Создаем пустую форму с начальными значениями
        form = OlympiadForm(initial={
            'status': Olympiad.OlympiadStatus.DRAFT,
            'is_open': True,
            'is_rated': True,
            'time_limit_minutes': 0,
            'min_passing_score': 0
        })
    
    # Отображаем форму создания
    context = {
        'title': _('Создание олимпиады'),
        'form': form
    }
    
    return render(request, 'olympiads/olympiad_form.html', context)

# Редактирование олимпиады
@login_required
def olympiad_edit(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем права доступа
    if not (request.user == olympiad.created_by or request.user.profile.is_admin):
        messages.error(request, _('У вас нет прав для редактирования этой олимпиады'))
        return redirect('olympiads:olympiad_list')
    
    if request.method == 'POST':
        # Используем ModelForm для обработки данных
        form = OlympiadForm(request.POST, request.FILES, instance=olympiad)
        
        if form.is_valid():
            # Сохраняем изменения
            form.save()
            messages.success(request, _('Олимпиада успешно обновлена!'))
            
            # Перенаправляем на страницу редактирования с обновленной формой
            return redirect('olympiads:olympiad_edit', olympiad_id=olympiad.id)
        else:
            # Если форма не валидна, отображаем её с ошибками
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Создаем форму с данными олимпиады
        form = OlympiadForm(instance=olympiad)
    
    # Получаем все задания олимпиады
    tasks = olympiad.tasks.all().order_by('order')
    
    context = {
        'title': _('Редактирование олимпиады'),
        'olympiad': olympiad,
        'form': form,
        'tasks': tasks
    }
    
    return render(request, 'olympiads/olympiad_form.html', context)

# Публикация олимпиады
@login_required
def olympiad_publish(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем права доступа
    if not (request.user == olympiad.created_by or request.user.profile.is_admin):
        messages.error(request, _('У вас нет прав для публикации этой олимпиады'))
        return redirect('olympiads:olympiad_list')
    
    # Проверяем, есть ли задания
    if olympiad.tasks.count() == 0:
        messages.error(request, _('Невозможно опубликовать олимпиаду без заданий'))
        return redirect('olympiads:olympiad_edit', olympiad_id=olympiad.id)
    
    # Проверяем статус олимпиады
    if olympiad.status == Olympiad.OlympiadStatus.DRAFT:
        olympiad.status = Olympiad.OlympiadStatus.PUBLISHED
        messages.success(request, _('Олимпиада успешно опубликована!'))
    elif olympiad.status == Olympiad.OlympiadStatus.PUBLISHED:
        # Если дата начала уже наступила, активируем олимпиаду
        now = timezone.now()
        if olympiad.start_datetime <= now:
            olympiad.status = Olympiad.OlympiadStatus.ACTIVE
            messages.success(request, _('Олимпиада успешно активирована!'))
        else:
            messages.info(request, _('Олимпиада уже опубликована'))
    elif olympiad.status == Olympiad.OlympiadStatus.ACTIVE:
        olympiad.status = Olympiad.OlympiadStatus.COMPLETED
        messages.success(request, _('Олимпиада отмечена как завершенная!'))
    else:
        messages.info(request, _('Невозможно изменить статус олимпиады'))
    
    olympiad.save()
    return redirect('olympiads:olympiad_edit', olympiad_id=olympiad.id)

# Создание нового задания для олимпиады
@login_required
def olympiad_task_create(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем права доступа
    if not (request.user == olympiad.created_by or request.user.profile.is_admin):
        messages.error(request, _('У вас нет прав для добавления заданий к этой олимпиаде'))
        return redirect('olympiads:olympiad_list')
    
    if request.method == 'POST':
        # Основные поля
        title = request.POST.get('title')
        description = request.POST.get('description')
        task_type = request.POST.get('task_type')
        points = int(request.POST.get('points', 1))
        
        # Дополнительные поля
        difficulty = int(request.POST.get('difficulty', 3))
        topic = request.POST.get('topic', '')
        course_id = request.POST.get('course', '')
        
        # Настройки отображения
        use_markdown = 'use_markdown' in request.POST
        use_latex = 'use_latex' in request.POST
        
        # Лимиты и ограничения
        max_attempts = int(request.POST.get('max_attempts', 0))
        time_limit_minutes = int(request.POST.get('time_limit_minutes', 0))
        memory_limit_mb = int(request.POST.get('memory_limit_mb', 0)) if task_type == 'programming' else 0
        
        # Порядок и другие параметры
        order = int(request.POST.get('order', 0))
        if order == 0:
            # Находим максимальный порядок и добавляем 10
            max_order = olympiad.tasks.aggregate(max_order=Max('order'))['max_order'] or 0
            order = max_order + 10
            
        min_passing_score = int(request.POST.get('min_passing_score', 0))
        
        # Создаем новое задание с расширенными параметрами
        task_data = {
            'olympiad': olympiad,
            'title': title,
            'description': description,
            'task_type': task_type,
            'points': points,
            'order': order,
            'difficulty': difficulty,
            'topic': topic,
            'use_markdown': use_markdown,
            'use_latex': use_latex,
            'max_attempts': max_attempts,
            'time_limit_minutes': time_limit_minutes,
            'memory_limit_mb': memory_limit_mb,
            'min_passing_score': min_passing_score
        }
        
        # Если это задание на программирование, добавляем начальный код
        if task_type == 'programming':
            task_data['initial_code'] = request.POST.get('initial_code', '')
        
        # Если указан связанный курс, добавляем его
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
                task_data['course'] = course
            except Course.DoesNotExist:
                pass
        
        task = OlympiadTask.objects.create(**task_data)
        
        messages.success(request, _('Задание успешно создано!'))
        return redirect('olympiads:olympiad_task_edit', olympiad_id=olympiad.id, task_id=task.id)
    
    # Получаем список доступных курсов для выбора
    courses = Course.objects.all()
    
    context = {
        'olympiad': olympiad,
        'task_types': OlympiadTask.TaskType.choices,
        'courses': courses
    }
    
    return render(request, 'olympiads/manage/task_create.html', context)

# Редактирование задания
@login_required
def olympiad_task_edit(request, olympiad_id, task_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    task = get_object_or_404(OlympiadTask, id=task_id, olympiad=olympiad)
    
    # Проверяем права доступа
    if not (request.user == olympiad.created_by or request.user.profile.is_admin):
        messages.error(request, _('У вас нет прав для редактирования заданий этой олимпиады'))
        return redirect('olympiads:olympiad_list')
    
    if request.method == 'POST':
        # Основные поля
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        task.points = int(request.POST.get('points', 1))
        task.order = int(request.POST.get('order', task.order))
        
        # Дополнительные поля
        task.difficulty = int(request.POST.get('difficulty', 3))
        task.topic = request.POST.get('topic', '')
        course_id = request.POST.get('course', '')
        
        # Настройки отображения
        task.use_markdown = 'use_markdown' in request.POST
        task.use_latex = 'use_latex' in request.POST
        
        # Лимиты и ограничения
        task.max_attempts = int(request.POST.get('max_attempts', 0))
        task.time_limit_minutes = int(request.POST.get('time_limit_minutes', 0))
        task.min_passing_score = int(request.POST.get('min_passing_score', 0))
        
        # Если это задание на программирование, обновляем особые поля
        if task.task_type == 'programming':
            task.initial_code = request.POST.get('initial_code', '')
            task.memory_limit_mb = int(request.POST.get('memory_limit_mb', 0))
            
            # Обработка тестовых случаев будет здесь
            # ...
        
        # Если это задание с выбором вариантов, обрабатываем варианты
        elif task.task_type == 'multiple_choice':
            # Обработка вариантов выбора будет реализована позже
            pass
        
        # Связанный курс
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
                task.course = course
            except Course.DoesNotExist:
                task.course = None
        else:
            task.course = None
        
        # Сохраняем изменения
        task.save()
        
        messages.success(request, _('Задание успешно обновлено!'))
        return redirect('olympiads:olympiad_task_edit', olympiad_id=olympiad.id, task_id=task.id)
    
    # Получаем тестовые случаи и варианты ответов
    test_cases = task.test_cases.all().order_by('order')
    options = task.options.all().order_by('order')
    
    # Получаем список доступных курсов для выбора
    courses = Course.objects.all()
    
    context = {
        'olympiad': olympiad,
        'task': task,
        'test_cases': test_cases,
        'options': options,
        'courses': courses,
        'task_types': OlympiadTask.TaskType.choices,
    }
    
    return render(request, 'olympiads/manage/task_edit.html', context)

# Просмотр списка участников олимпиады
@login_required
def olympiad_participants(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем права доступа
    if not (request.user == olympiad.created_by or request.user.profile.is_admin):
        messages.error(request, _('У вас нет прав для просмотра участников этой олимпиады'))
        return redirect('olympiads:olympiad_list')
    
    # Получаем всех участников
    participants = OlympiadParticipation.objects.filter(olympiad=olympiad).order_by('-score')
    
    context = {
        'olympiad': olympiad,
        'participants': participants
    }
    
    return render(request, 'olympiads/manage/participants.html', context)

# Управление приглашениями на олимпиаду
@login_required
def olympiad_invitations(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем права доступа
    if not (request.user == olympiad.created_by or request.user.profile.is_admin):
        messages.error(request, _('У вас нет прав для управления приглашениями этой олимпиады'))
        return redirect('olympiads:olympiad_list')
    
    if request.method == 'POST':
        # Обрабатываем форму приглашения
        username = request.POST.get('username')
        
        try:
            user = CustomUser.objects.get(username=username)
            
            # Проверяем, не зарегистрирован ли уже пользователь
            if OlympiadParticipation.objects.filter(olympiad=olympiad, user=user).exists():
                messages.info(request, _('Пользователь уже зарегистрирован на эту олимпиаду'))
            
            # Временное решение: отключаем приглашения через OlympiadUserInvitation
            else:
                # Вместо OlympiadUserInvitation используем OlympiadInvitation
                code = generate_random_code()
                OlympiadInvitation.objects.create(
                    olympiad=olympiad,
                    code=code,
                    is_active=True,
                    max_uses=1,
                    invited_by=request.user
                )
                messages.success(request, _('Ссылка-приглашение для пользователя создана: код {}').format(code))
                messages.success(request, _('Приглашение успешно отправлено!'))
        
        except CustomUser.DoesNotExist:
            messages.error(request, _('Пользователь с таким именем не найден'))
    
    # Получаем все приглашения
    invitations = OlympiadInvitation.objects.filter(olympiad=olympiad).order_by('-created_at')
    
    context = {
        'olympiad': olympiad,
        'invitations': invitations
    }
    
    return render(request, 'olympiads/manage/invitations.html', context)

# Завершение олимпиады участником
@login_required
def olympiad_finish(request, olympiad_id):
    if request.method != 'POST':
        return redirect('olympiads:olympiad_tasks', olympiad_id=olympiad_id)
    
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем, зарегистрирован ли пользователь
    participation = get_object_or_404(
        OlympiadParticipation, 
        olympiad=olympiad,
        user=request.user
    )
    
    # Если олимпиада уже завершена, перенаправляем на результаты
    if participation.is_completed:
        return redirect('olympiads:olympiad_results', olympiad_id=olympiad.id)
    
    now = timezone.now()
    
    # Отмечаем олимпиаду как завершенную
    participation.is_completed = True
    participation.finished_at = now
    participation.save()
    
    # Обновляем общий балл
    participation.calculate_score()
    
    messages.success(request, _('Вы успешно завершили олимпиаду!'))
    return redirect('olympiads:olympiad_results', olympiad_id=olympiad.id)

# Просмотр таблицы лидеров олимпиады
@login_required
def olympiad_leaderboard(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Получаем завершенные участия в порядке убывания баллов и времени
    participations = OlympiadParticipation.objects.filter(
        olympiad=olympiad,
        is_completed=True
    ).order_by('-score', 'finished_at')
    
    # Создаем пагинатор
    paginator = Paginator(participations, 20)
    page_number = request.GET.get('page', 1)
    participants_page = paginator.get_page(page_number)
    
    # Получаем ранг текущего пользователя
    user_rank = None
    if request.user.is_authenticated:
        user_participation = OlympiadParticipation.objects.filter(
            olympiad=olympiad,
            user=request.user,
            is_completed=True
        ).first()
        
        if user_participation:
            for i, participation in enumerate(participations):
                if participation.user_id == request.user.id:
                    user_rank = i + 1
                    break
    
    context = {
        'olympiad': olympiad,
        'participants': participants_page,
        'user_rank': user_rank,
        'total_participants': participations.count()
    }
    
    return render(request, 'olympiads/olympiad_leaderboard.html', context)

# API для обновления прогресса участника
@login_required
@require_POST
@csrf_exempt
def olympiad_update_progress(request, olympiad_id):
    try:
        olympiad = get_object_or_404(Olympiad, id=olympiad_id)
        
        # Проверяем, зарегистрирован ли пользователь
        participation = get_object_or_404(
            OlympiadParticipation, 
            olympiad=olympiad,
            user=request.user
        )
        
        # Проверяем, не завершил ли пользователь олимпиаду
        if participation.is_completed:
            return JsonResponse({'status': 'error', 'message': 'Олимпиада уже завершена'})
        
        # Получаем задания и их статус
        tasks = olympiad.tasks.all()
        task_statuses = {}
        
        for task in tasks:
            submission = OlympiadTaskSubmission.objects.filter(
                participation=participation,
                task=task
            ).order_by('-submitted_at').first()
            
            task_statuses[str(task.id)] = {
                'submitted': submission is not None,
                'is_correct': submission.is_correct if submission else False,
                'score': submission.score if submission else 0
            }
        
        # Обновляем общий балл
        participation.calculate_score()
        
        # Проверяем, не истекло ли время
        now = timezone.now()
        time_left = 0
        
        if olympiad.time_limit_minutes > 0:
            time_passed = (now - participation.started_at).total_seconds() / 60
            time_left = max(0, olympiad.time_limit_minutes - time_passed)
        else:
            time_left = max(0, (olympiad.end_datetime - now).total_seconds() / 60)
        
        return JsonResponse({
            'status': 'success',
            'task_statuses': task_statuses,
            'score': participation.score,
            'max_score': participation.max_score,
            'time_left_minutes': int(time_left)
        })
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# Завершение олимпиады организатором
# Активирует олимпиаду (изменяет статус на ACTIVE)
@login_required
def olympiad_activate(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем права доступа
    if not (request.user.is_staff or request.user == olympiad.created_by):
        messages.error(request, _('У вас нет прав для активации этой олимпиады'))
        return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)
    
    # Активируем олимпиаду
    olympiad.status = Olympiad.OlympiadStatus.ACTIVE
    olympiad.save()
    
    messages.success(request, _('Олимпиада успешно активирована!'))
    return redirect('olympiads:olympiad_edit', olympiad_id=olympiad.id)

# Деактивирует олимпиаду (изменяет статус на PUBLISHED)
@login_required
def olympiad_deactivate(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем права доступа
    if not (request.user.is_staff or request.user == olympiad.created_by):
        messages.error(request, _('У вас нет прав для деактивации этой олимпиады'))
        return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)
    
    # Деактивируем олимпиаду
    olympiad.status = Olympiad.OlympiadStatus.PUBLISHED
    olympiad.save()
    
    messages.success(request, _('Олимпиада успешно деактивирована!'))
    return redirect('olympiads:olympiad_edit', olympiad_id=olympiad.id)

@login_required
def olympiad_complete(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем права доступа
    if not (request.user.is_staff or request.user == olympiad.created_by):
        messages.error(request, _('У вас нет прав для управления этой олимпиадой'))
        return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)
    
    if request.method == 'POST':
        olympiad.status = Olympiad.OlympiadStatus.COMPLETED
        olympiad.save()
        
        # Завершаем все незавершенные участия
        now = timezone.now()
        OlympiadParticipation.objects.filter(
            olympiad=olympiad,
            is_completed=False
        ).update(is_completed=True, finished_at=now)
        
        messages.success(request, _('Олимпиада успешно завершена'))
        return redirect('olympiads:olympiad_manage_list')
    
    context = {
        'olympiad': olympiad
    }
    
    return render(request, 'olympiads/manage/complete.html', context)

# Архивация олимпиады
@login_required
def olympiad_archive(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем права доступа
    if not (request.user.is_staff or request.user == olympiad.created_by):
        messages.error(request, _('У вас нет прав для управления этой олимпиадой'))
        return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)
    
    if request.method == 'POST':
        olympiad.status = Olympiad.OlympiadStatus.ARCHIVED
        olympiad.save()
        
        messages.success(request, _('Олимпиада успешно архивирована'))
        return redirect('olympiads:olympiad_manage_list')
    
    context = {
        'olympiad': olympiad
    }
    
    return render(request, 'olympiads/manage/archive.html', context)

# Удаление задания олимпиады
@login_required
def olympiad_task_delete(request, olympiad_id, task_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    task = get_object_or_404(OlympiadTask, id=task_id, olympiad=olympiad)
    
    # Проверяем права доступа
    if not (request.user.is_staff or request.user == olympiad.created_by):
        messages.error(request, _('У вас нет прав для управления этой олимпиадой'))
        return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)
    
    if request.method == 'POST':
        task.delete()
        
        # Пересчитываем порядок заданий
        for i, t in enumerate(olympiad.tasks.all().order_by('order')):
            t.order = i + 1
            t.save()
        
        messages.success(request, _('Задание успешно удалено'))
        return redirect('olympiads:olympiad_edit', olympiad_id=olympiad.id)
    
    context = {
        'olympiad': olympiad,
        'task': task
    }
    
    return render(request, 'olympiads/manage/task_delete.html', context)

# Статистика олимпиады
@login_required
def olympiad_statistics(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем права доступа
    if not (request.user.is_staff or request.user == olympiad.created_by):
        messages.error(request, _('У вас нет прав для просмотра статистики этой олимпиады'))
        return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)
    
    # Получаем общую статистику
    total_participants = OlympiadParticipation.objects.filter(olympiad=olympiad).count()
    completed_participants = OlympiadParticipation.objects.filter(olympiad=olympiad, is_completed=True).count()
    passed_participants = OlympiadParticipation.objects.filter(olympiad=olympiad, passed=True).count()
    
    # Статистика по заданиям
    tasks = olympiad.tasks.all().order_by('order')
    tasks_stats = []
    
    for task in tasks:
        submissions = OlympiadTaskSubmission.objects.filter(task=task)
        attempts = submissions.count()
        correct = submissions.filter(is_correct=True).count()
        avg_score = submissions.aggregate(avg=Avg('score'))['avg'] or 0
        
        tasks_stats.append({
            'task': task,
            'attempts': attempts,
            'correct': correct,
            'success_rate': (correct / attempts * 100) if attempts > 0 else 0,
            'avg_score': avg_score
        })
    
    # Распределение баллов
    score_distribution = OlympiadParticipation.objects.filter(
        olympiad=olympiad,
        is_completed=True
    ).values('score').annotate(count=Count('id')).order_by('score')
    
    context = {
        'olympiad': olympiad,
        'total_participants': total_participants,
        'completed_participants': completed_participants,
        'passed_participants': passed_participants,
        'completion_rate': (completed_participants / total_participants * 100) if total_participants > 0 else 0,
        'pass_rate': (passed_participants / completed_participants * 100) if completed_participants > 0 else 0,
        'tasks_stats': tasks_stats,
        'score_distribution': score_distribution
    }
    
    return render(request, 'olympiads/olympiad_statistics.html', context)


# API для выполнения кода
@login_required
@require_POST
def execute_code(request, olympiad_id, task_id):
    # Получаем объекты из базы данных
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    task = get_object_or_404(OlympiadTask, id=task_id, olympiad=olympiad)
    
    # Проверяем, что задание является задачей программирования
    if task.task_type != OlympiadTask.TaskType.PROGRAMMING:
        return JsonResponse({
            'success': False,
            'error': 'Это задание не является задачей программирования'
        })
    
    # Проверяем, что олимпиада активна и пользователь может участвовать
    if not olympiad.can_participate(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете участвовать в этой олимпиаде'
        })
    
    # Парсим JSON-данные из запроса
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        language = data.get('language', 'python')
        input_data = data.get('input', '')
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'Неверный формат данных'
        })
    
    # Проверяем, что код не пустой
    if not code.strip():
        return JsonResponse({
            'success': False,
            'error': 'Код не может быть пустым'
        })
    
    # Импортируем модуль для запуска кода
    from .code_runner import (
        run_code_with_input, 
        ExecutionTimeLimitExceeded, 
        ExecutionMemoryLimitExceeded, 
        ExecutionRuntimeError, 
        CompilationError,
        DEFAULT_TIME_LIMIT,
        DEFAULT_MEMORY_LIMIT
    )
    
    # Определяем ограничения
    time_limit = task.time_limit_minutes * 60 if task.time_limit_minutes > 0 else DEFAULT_TIME_LIMIT
    memory_limit = task.memory_limit_mb if task.memory_limit_mb > 0 else DEFAULT_MEMORY_LIMIT
    
    try:
        # Компилируем и запускаем код
        from .code_runner import compile_code
        temp_dir, filename, executable = compile_code(code, language)
        
        try:
            # Запускаем код с пользовательским вводом
            output, execution_time, memory_usage = run_code_with_input(
                executable, language, input_data, time_limit, memory_limit
            )
            
            # Возвращаем результат
            return JsonResponse({
                'success': True,
                'output': output,
                'execution_time': execution_time,
                'memory_usage': memory_usage
            })
            
        finally:
            # Удаляем временные файлы
            import shutil
            shutil.rmtree(temp_dir)
            
    except CompilationError as e:
        return JsonResponse({
            'success': False,
            'error': 'Ошибка компиляции',
            'error_details': str(e)
        })
    except ExecutionTimeLimitExceeded as e:
        return JsonResponse({
            'success': False,
            'error': 'Превышено ограничение по времени',
            'error_details': str(e)
        })
    except ExecutionMemoryLimitExceeded as e:
        return JsonResponse({
            'success': False,
            'error': 'Превышено ограничение по памяти',
            'error_details': str(e)
        })
    except ExecutionRuntimeError as e:
        return JsonResponse({
            'success': False,
            'error': 'Ошибка выполнения',
            'error_details': str(e)
        })
    except Exception as e:
        # Обрабатываем прочие ошибки
        return JsonResponse({
            'success': False,
            'error': 'Произошла ошибка при выполнении кода',
            'error_details': str(e)
        })


# API для сохранения кода
@login_required
@require_POST
def save_code(request, olympiad_id, task_id):
    # Получаем объекты из базы данных
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    task = get_object_or_404(OlympiadTask, id=task_id, olympiad=olympiad)
    
    # Проверяем, что задание является задачей программирования
    if task.task_type != OlympiadTask.TaskType.PROGRAMMING:
        return JsonResponse({
            'success': False,
            'error': 'Это задание не является задачей программирования'
        })
    
    # Проверяем, что олимпиада активна и пользователь может участвовать
    if not olympiad.can_participate(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете участвовать в этой олимпиаде'
        })
    
    # Парсим JSON-данные из запроса
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        language = data.get('language', 'python')
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'Неверный формат данных'
        })
    
    # Получаем или создаем запись об участии
    participation, created = OlympiadParticipation.objects.get_or_create(
        olympiad=olympiad,
        user=request.user,
        defaults={
            'max_score': sum(task.points for task in olympiad.tasks.all())
        }
    )
    
    # Создаем или обновляем submission
    submission, created = OlympiadTaskSubmission.objects.get_or_create(
        participation=participation,
        task=task,
        defaults={
            'code': code,
            'max_score': task.points
        }
    )
    
    if not created:
        submission.code = code
        submission.save(update_fields=['code'])
    
    return JsonResponse({
        'success': True,
        'message': 'Код успешно сохранен'
    })


# API для тестирования кода
@login_required
@require_POST
def test_code(request, olympiad_id, task_id):
    # Получаем объекты из базы данных
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    task = get_object_or_404(OlympiadTask, id=task_id, olympiad=olympiad)
    
    # Проверяем, что задание является задачей программирования
    if task.task_type != OlympiadTask.TaskType.PROGRAMMING:
        return JsonResponse({
            'success': False,
            'error': 'Это задание не является задачей программирования'
        })
    
    # Проверяем, что олимпиада активна и пользователь может участвовать
    if not olympiad.can_participate(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Вы не можете участвовать в этой олимпиаде'
        })
    
    # Парсим JSON-данные из запроса
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        language = data.get('language', 'python')
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'Неверный формат данных'
        })
    
    # Проверяем, что код не пустой
    if not code.strip():
        return JsonResponse({
            'success': False,
            'error': 'Код не может быть пустым'
        })
    
    # Получаем тестовые случаи
    test_cases = task.test_cases.all().order_by('order')
    
    # Если тестовые случаи отсутствуют
    if not test_cases.exists():
        return JsonResponse({
            'success': False,
            'error': 'Для этого задания не настроены тестовые случаи'
        })
    
    # Формируем список тестов для проверки
    test_case_data = [(tc.input_data, tc.expected_output) for tc in test_cases]
    
    # Импортируем модуль для проверки решения
    from .code_runner import check_solution
    
    # Определяем ограничения
    time_limit = task.time_limit_minutes * 60 if task.time_limit_minutes > 0 else 5
    memory_limit = task.memory_limit_mb if task.memory_limit_mb > 0 else 512
    
    try:
        # Проверяем решение на всех тестовых случаях
        results, passed_count, total_count = check_solution(
            code, language, test_case_data, 
            time_limit=time_limit, memory_limit=memory_limit
        )
        
        # Считаем баллы за решение
        max_score = task.points
        score = round(max_score * (passed_count / total_count)) if total_count > 0 else 0
        is_correct = passed_count == total_count
        
        # Получаем или создаем запись об участии
        participation, created = OlympiadParticipation.objects.get_or_create(
            olympiad=olympiad,
            user=request.user,
            defaults={
                'max_score': sum(t.points for t in olympiad.tasks.all())
            }
        )
        
        # Сохраняем результаты
        submission = OlympiadTaskSubmission.objects.create(
            participation=participation,
            task=task,
            code=code,
            score=score,
            max_score=max_score,
            is_correct=is_correct,
            passed_test_cases=passed_count,
            total_test_cases=total_count
        )
        
        # Обновляем общий счет участника
        participation.calculate_score()
        
        # Преобразуем результаты для отправки
        formatted_results = []
        for i, result in enumerate(results):
            test_case = test_cases[i]
            formatted_results.append({
                'test_case_id': result['test_case_id'],
                'passed': result['passed'],
                'input_data': test_case.input_data if not test_case.is_hidden else '(скрытый тест)',
                'expected': test_case.expected_output if not test_case.is_hidden else '(скрытый тест)',
                'output': result['output'],
                'error': result['error'],
                'execution_time': result['execution_time'],
                'memory_usage': result['memory_usage']
            })
        
        # Возвращаем результат проверки
        return JsonResponse({
            'success': True,
            'passed_tests': passed_count,
            'total_tests': total_count,
            'score': score,
            'max_score': max_score,
            'is_correct': is_correct,
            'test_results': formatted_results
        })
        
    except Exception as e:
        # Обрабатываем ошибки
        return JsonResponse({
            'success': False,
            'error': 'Произошла ошибка при проверке решения',
            'error_details': str(e)
        })
    
    return render(request, 'olympiads/manage/statistics.html', context)


# Регистрация на олимпиаду по коду приглашения
@login_required
def olympiad_join_by_invitation(request, code):
    # Ищем приглашение по коду
    invitation = get_object_or_404(OlympiadInvitation, code=code)
    olympiad = invitation.olympiad
    
    # Проверяем действительность приглашения
    if not invitation.is_valid():
        if invitation.expires_at and timezone.now() > invitation.expires_at:
            messages.error(request, _('Срок действия приглашения истек'))
        elif invitation.max_uses > 0 and invitation.used_count >= invitation.max_uses:
            messages.error(request, _('Превышено максимальное количество использований приглашения'))
        else:
            messages.error(request, _('Приглашение недействительно'))
        return redirect('olympiads:olympiad_list')
    
    # Проверяем статус олимпиады
    if olympiad.status != Olympiad.OlympiadStatus.PUBLISHED and olympiad.status != Olympiad.OlympiadStatus.ACTIVE:
        messages.error(request, _('Регистрация на эту олимпиаду недоступна'))
        return redirect('olympiads:olympiad_list')
    
    # Проверяем, не зарегистрирован ли пользователь уже
    if OlympiadParticipation.objects.filter(olympiad=olympiad, user=request.user).exists():
        messages.info(request, _('Вы уже зарегистрированы на эту олимпиаду'))
    else:
        # Регистрируем пользователя
        max_score = olympiad.tasks.aggregate(total=Sum('points'))['total'] or 0
        
        OlympiadParticipation.objects.create(
            olympiad=olympiad,
            user=request.user,
            max_score=max_score
        )
        
        # Увеличиваем счетчик использований приглашения
        invitation.use()
        messages.success(request, _('Вы успешно зарегистрировались на олимпиаду по приглашению!'))
    
    # Если олимпиада активна, перенаправляем на страницу с заданиями
    if olympiad.status == Olympiad.OlympiadStatus.ACTIVE:
        return redirect('olympiads:olympiad_tasks', olympiad_id=olympiad.id)
    
    return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)