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
import json
import datetime

from .models import (
    Olympiad, 
    OlympiadTask, 
    OlympiadTestCase, 
    OlympiadMultipleChoiceOption,
    OlympiadParticipation, 
    OlympiadTaskSubmission,
    OlympiadInvitation,
    OlympiadUserInvitation,
    OlympiadCertificate
)

from users.models import CustomUser

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
            status=Olympiad.OlympiadStatus.PUBLISHED, 
            start_datetime__gt=now
        ).order_by('start_datetime')
        
        upcoming_olympiads = olympiads
        active_olympiads = []
        completed_olympiads = []
    elif filter_status == 'active':
        # Только активные
        olympiads = olympiads_query.filter(
            Q(status=Olympiad.OlympiadStatus.ACTIVE) |
            Q(status=Olympiad.OlympiadStatus.PUBLISHED, start_datetime__lte=now, end_datetime__gte=now)
        ).order_by('end_datetime')
        
        upcoming_olympiads = []
        active_olympiads = olympiads
        completed_olympiads = []
    elif filter_status == 'completed':
        # Только завершенные
        olympiads = olympiads_query.filter(
            Q(status=Olympiad.OlympiadStatus.COMPLETED) | 
            Q(status=Olympiad.OlympiadStatus.ACTIVE, end_datetime__lt=now)
        ).order_by('-end_datetime')
        
        upcoming_olympiads = []
        active_olympiads = []
        completed_olympiads = olympiads
    else:
        # Без фильтра показываем все категории
        upcoming_olympiads = olympiads_query.filter(
            status=Olympiad.OlympiadStatus.PUBLISHED, 
            start_datetime__gt=now
        ).order_by('start_datetime')
        
        active_olympiads = olympiads_query.filter(
            Q(status=Olympiad.OlympiadStatus.ACTIVE) |
            Q(status=Olympiad.OlympiadStatus.PUBLISHED, start_datetime__lte=now, end_datetime__gte=now)
        ).order_by('end_datetime')
        
        completed_olympiads = olympiads_query.filter(
            Q(status=Olympiad.OlympiadStatus.COMPLETED) | 
            Q(status=Olympiad.OlympiadStatus.ACTIVE, end_datetime__lt=now)
        ).order_by('-end_datetime')[:10]
    
    # Если пользователь авторизован, добавляем информацию об участии
    if request.user.is_authenticated:
        user_participations = OlympiadParticipation.objects.filter(user=request.user)
        user_participation_ids = {p.olympiad_id for p in user_participations}
        
        # Добавляем информацию о приглашениях (используем существующую модель OlympiadInvitation)
        user_invitations = OlympiadInvitation.objects.filter(
            user=request.user,
            is_active=True  # используем поле is_active вместо is_accepted
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )
        user_invitation_ids = {i.olympiad_id for i in user_invitations}
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
    
    context = {
        'olympiad': olympiad,
        'user_participation': user_participation,
        'user_invitation': user_invitation,
        'can_register': can_register,
        'task_count': task_count,
        'total_points': total_points,
        'top_participants': top_participants,
        'now': now
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
    
    # Проверяем, открытая ли олимпиада или есть ли приглашение
    if not olympiad.is_open:
        # Используем существующую модель OlympiadInvitation вместо OlympiadUserInvitation
        invitation = OlympiadInvitation.objects.filter(
            olympiad=olympiad,
            user=request.user,
            is_active=True
        ).first()
        
        if not invitation:
            messages.error(request, _('Эта олимпиада закрыта для регистрации'))
            return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)
        
        # Помечаем приглашение как использованное
        invitation.is_active = False
        invitation.used_count += 1
        invitation.save()
    
    # Регистрируем пользователя
    max_score = olympiad.tasks.aggregate(total=Sum('points'))['total'] or 0
    
    OlympiadParticipation.objects.create(
        olympiad=olympiad,
        user=request.user,
        max_score=max_score
    )
    
    messages.success(request, _('Вы успешно зарегистрировались на олимпиаду'))
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
    
    # Получаем все задания олимпиады
    tasks = olympiad.tasks.all().order_by('order')
    
    # Для каждого задания получаем информацию о сдаче
    task_statuses = {}
    for task in tasks:
        submission = OlympiadTaskSubmission.objects.filter(
            participation=participation,
            task=task
        ).order_by('-submitted_at').first()
        
        task_statuses[task.id] = {
            'submitted': submission is not None,
            'is_correct': submission.is_correct if submission else False,
            'score': submission.score if submission else 0,
            'submission_id': submission.id if submission else None
        }
    
    context = {
        'olympiad': olympiad,
        'participation': participation,
        'tasks': tasks,
        'task_statuses': task_statuses,
        'time_left_minutes': int(time_left)
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
    
    context = {
        'olympiad': olympiad,
        'participation': participation,
        'task': task,
        'submission': submission,
        'test_cases': test_cases,
        'options': options
    }
    
    return render(request, 'olympiads/olympiad_task_detail.html', context)

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
    
    context = {
        'olympiad': olympiad,
        'participation': participation,
        'results': results,
        'has_certificate': has_certificate,
        'certificate': certificate,
        'top_participants': top_participants,
        'user_rank': user_rank
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
        # Обрабатываем данные формы
        title = request.POST.get('title')
        description = request.POST.get('description')
        short_description = request.POST.get('short_description', '')
        start_datetime_str = request.POST.get('start_datetime')
        end_datetime_str = request.POST.get('end_datetime')
        time_limit_minutes = int(request.POST.get('time_limit_minutes', '0') or '0')
        is_open = request.POST.get('is_open') == 'on'
        min_passing_score = int(request.POST.get('min_passing_score', '0') or '0')
        
        # Преобразуем строки дат в объекты datetime
        from datetime import datetime
        
        if not start_datetime_str:
            messages.error(request, _('Необходимо указать дату и время начала олимпиады'))
            return redirect('olympiads:olympiad_create')
            
        if not end_datetime_str:
            messages.error(request, _('Необходимо указать дату и время окончания олимпиады'))
            return redirect('olympiads:olympiad_create')
            
        try:
            start_datetime = datetime.fromisoformat(start_datetime_str.replace('T', ' '))
            end_datetime = datetime.fromisoformat(end_datetime_str.replace('T', ' '))
        except ValueError:
            messages.error(request, _('Некорректный формат даты и времени'))
            return redirect('olympiads:olympiad_create')
        
        # Создаем новую олимпиаду
        olympiad = Olympiad.objects.create(
            title=title,
            description=description,
            short_description=short_description,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            time_limit_minutes=time_limit_minutes,
            is_open=is_open,
            min_passing_score=min_passing_score,
            created_by=request.user,
            status=Olympiad.OlympiadStatus.DRAFT
        )
        
        messages.success(request, _('Олимпиада успешно создана!'))
        return redirect('olympiads:olympiad_edit', olympiad_id=olympiad.id)
    
    context = {}
    return render(request, 'olympiads/manage/olympiad_create.html', context)

# Редактирование олимпиады
@login_required
def olympiad_edit(request, olympiad_id):
    olympiad = get_object_or_404(Olympiad, id=olympiad_id)
    
    # Проверяем права доступа
    if not (request.user == olympiad.created_by or request.user.profile.is_admin):
        messages.error(request, _('У вас нет прав для редактирования этой олимпиады'))
        return redirect('olympiads:olympiad_list')
    
    if request.method == 'POST':
        # Обрабатываем данные формы
        olympiad.title = request.POST.get('title')
        olympiad.description = request.POST.get('description')
        olympiad.short_description = request.POST.get('short_description', '')
        
        start_datetime_str = request.POST.get('start_datetime')
        end_datetime_str = request.POST.get('end_datetime')
        
        # Преобразуем строки дат в объекты datetime
        from datetime import datetime
        
        if not start_datetime_str:
            messages.error(request, _('Необходимо указать дату и время начала олимпиады'))
            return redirect('olympiads:olympiad_edit', olympiad_id=olympiad.id)
            
        if not end_datetime_str:
            messages.error(request, _('Необходимо указать дату и время окончания олимпиады'))
            return redirect('olympiads:olympiad_edit', olympiad_id=olympiad.id)
            
        try:
            olympiad.start_datetime = datetime.fromisoformat(start_datetime_str.replace('T', ' '))
            olympiad.end_datetime = datetime.fromisoformat(end_datetime_str.replace('T', ' '))
        except ValueError:
            messages.error(request, _('Некорректный формат даты и времени'))
            return redirect('olympiads:olympiad_edit', olympiad_id=olympiad.id)
        
        olympiad.time_limit_minutes = int(request.POST.get('time_limit_minutes', '0') or '0')
        olympiad.is_open = request.POST.get('is_open') == 'on'
        olympiad.min_passing_score = int(request.POST.get('min_passing_score', '0') or '0')
        
        # Сохраняем изменения
        olympiad.save()
        
        messages.success(request, _('Олимпиада успешно обновлена!'))
        return redirect('olympiads:olympiad_edit', olympiad_id=olympiad.id)
    
    # Получаем все задания олимпиады
    tasks = olympiad.tasks.all().order_by('order')
    
    context = {
        'olympiad': olympiad,
        'tasks': tasks
    }
    
    return render(request, 'olympiads/manage/olympiad_edit.html', context)

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
        # Обрабатываем данные формы
        title = request.POST.get('title')
        description = request.POST.get('description')
        task_type = request.POST.get('task_type')
        points = request.POST.get('points', 1)
        
        # Находим максимальный порядок и добавляем 10
        max_order = olympiad.tasks.aggregate(max_order=Max('order'))['max_order'] or 0
        order = max_order + 10
        
        # Создаем новое задание
        task = OlympiadTask.objects.create(
            olympiad=olympiad,
            title=title,
            description=description,
            task_type=task_type,
            points=points,
            order=order
        )
        
        # Если это задание на программирование, добавляем начальный код
        if task_type == OlympiadTask.TaskType.PROGRAMMING:
            initial_code = request.POST.get('initial_code', '')
            task.initial_code = initial_code
            task.save()
        
        messages.success(request, _('Задание успешно создано!'))
        return redirect('olympiads:olympiad_task_edit', olympiad_id=olympiad.id, task_id=task.id)
    
    context = {
        'olympiad': olympiad,
        'task_types': OlympiadTask.TaskType.choices
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
        # Обрабатываем данные формы
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        task.points = request.POST.get('points', 1)
        task.order = request.POST.get('order', task.order)
        
        # Если это задание на программирование, обновляем начальный код
        if task.task_type == OlympiadTask.TaskType.PROGRAMMING:
            task.initial_code = request.POST.get('initial_code', '')
            
            # Обрабатываем тестовые случаи
            # ...
        
        # Если это задание с выбором вариантов, обрабатываем варианты
        elif task.task_type == OlympiadTask.TaskType.MULTIPLE_CHOICE:
            # Обработка вариантов выбора будет реализована позже
            pass
        
        # Сохраняем изменения
        task.save()
        
        messages.success(request, _('Задание успешно обновлено!'))
        return redirect('olympiads:olympiad_task_edit', olympiad_id=olympiad.id, task_id=task.id)
    
    # Получаем тестовые случаи и варианты ответов
    test_cases = task.test_cases.all().order_by('order')
    options = task.options.all().order_by('order')
    
    context = {
        'olympiad': olympiad,
        'task': task,
        'test_cases': test_cases,
        'options': options
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
            
            # Проверяем, не приглашен ли уже пользователь
            elif OlympiadInvitation.objects.filter(olympiad=olympiad, user=user).exists():
                messages.info(request, _('Пользователь уже приглашен на эту олимпиаду'))
            
            else:
                # Создаем новое приглашение
                OlympiadInvitation.objects.create(
                    olympiad=olympiad,
                    user=user,
                    invited_by=request.user
                )
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