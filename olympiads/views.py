from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, Max
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator

from .models import (
    Olympiad, 
    OlympiadTask, 
    OlympiadTestCase, 
    OlympiadMultipleChoiceOption,
    OlympiadParticipation, 
    OlympiadTaskSubmission,
    OlympiadInvitation,
    OlympiadCertificate
)

from users.models import CustomUser

# Просмотр списка олимпиад
def olympiad_list(request):
    now = timezone.now()
    upcoming_olympiads = Olympiad.objects.filter(
        status=Olympiad.OlympiadStatus.PUBLISHED, 
        start_datetime__gt=now
    ).order_by('start_datetime')
    
    active_olympiads = Olympiad.objects.filter(
        status=Olympiad.OlympiadStatus.ACTIVE,
        start_datetime__lte=now,
        end_datetime__gte=now
    ).order_by('end_datetime')
    
    completed_olympiads = Olympiad.objects.filter(
        Q(status=Olympiad.OlympiadStatus.COMPLETED) | 
        Q(status=Olympiad.OlympiadStatus.ACTIVE, end_datetime__lt=now)
    ).order_by('-end_datetime')[:10]
    
    # Если пользователь авторизован, добавляем информацию об участии
    if request.user.is_authenticated:
        user_participations = OlympiadParticipation.objects.filter(user=request.user)
        user_participation_ids = {p.olympiad_id for p in user_participations}
        
        # Добавляем информацию о приглашениях
        user_invitations = OlympiadInvitation.objects.filter(
            user=request.user, 
            is_accepted=False,
            olympiad__start_datetime__gt=now
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
        'user_invitation_ids': user_invitation_ids
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
        
        user_invitation = OlympiadInvitation.objects.filter(
            olympiad=olympiad,
            user=request.user,
            is_accepted=False
        ).first()
        
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
        invitation = OlympiadInvitation.objects.filter(
            olympiad=olympiad,
            user=request.user,
            is_accepted=False
        ).first()
        
        if not invitation:
            messages.error(request, _('Эта олимпиада закрыта для регистрации'))
            return redirect('olympiads:olympiad_detail', olympiad_id=olympiad.id)
        
        # Принимаем приглашение
        invitation.is_accepted = True
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