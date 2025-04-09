from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.utils import timezone
from django.db.models import Max, Q
from django.urls import reverse

from .models import Olympiad, Problem, TestCase, Submission, OlympiadParticipant, TestResult
from .forms import OlympiadForm, ProblemForm, TestCaseForm, SubmissionForm

import json
from datetime import datetime, timedelta


def olympiad_list(request):
    """Отображает список всех опубликованных олимпиад с фильтрацией"""
    # Получение параметров фильтрации
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    # Базовый запрос - только опубликованные олимпиады
    olympiads = Olympiad.objects.filter(is_published=True)
    
    # Фильтрация по статусу
    if status == 'active':
        olympiads = olympiads.filter(
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        )
    elif status == 'future':
        olympiads = olympiads.filter(start_time__gt=timezone.now())
    elif status == 'past':
        olympiads = olympiads.filter(end_time__lt=timezone.now())
    
    # Поиск по названию или описанию
    if search:
        olympiads = olympiads.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    
    # Сортировка: сначала активные, затем предстоящие, затем завершенные
    olympiads = olympiads.order_by(
        # Сортируем активные олимпиады по времени окончания
        -Q(start_time__lte=timezone.now(), end_time__gte=timezone.now()) * 2,
        # Затем предстоящие по времени начала
        -Q(start_time__gt=timezone.now()) * 1,
        'start_time'
    )
    
    # Пагинация
    paginator = Paginator(olympiads, 9)  # 9 олимпиад на странице
    page_number = request.GET.get('page')
    olympiads = paginator.get_page(page_number)
    
    # Отображение статуса для пустых состояний
    status_display = {
        'active': 'Активные',
        'future': 'Предстоящие',
        'past': 'Завершенные',
    }.get(status, '')
    
    context = {
        'olympiads': olympiads,
        'status': status,
        'search': search,
        'status_display': status_display,
    }
    
    return render(request, 'olympiads/olympiad_list.html', context)


def olympiad_detail(request, slug):
    """Отображает детальную информацию об олимпиаде и её задачах"""
    olympiad = get_object_or_404(Olympiad, slug=slug, is_published=True)
    
    # Проверка, участвует ли пользователь в олимпиаде
    is_participating = False
    if request.user.is_authenticated:
        is_participating = OlympiadParticipant.objects.filter(
            olympiad=olympiad, user=request.user
        ).exists()
    
    # Получение задач олимпиады
    problems = olympiad.problems.all().order_by('order')
    
    # Вычисление продолжительности олимпиады
    duration = olympiad.end_time - olympiad.start_time
    days, seconds = duration.days, duration.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if days > 0:
        duration_str = f"{days} д. {hours} ч."
    else:
        duration_str = f"{hours} ч. {minutes} мин."
    
    # Статистика решений (только для участников олимпиады или после завершения)
    user_submissions = {}
    solved_problems = 0
    total_points = 0
    total_available_points = problems.aggregate(total=sum(p.points for p in problems))['total'] or 0
    
    if request.user.is_authenticated and (is_participating or olympiad.is_past() or request.user.is_staff):
        # Получение лучших отправок пользователя по каждой задаче
        submissions = Submission.objects.filter(
            olympiad=olympiad,
            user=request.user
        )
        
        for problem in problems:
            best_submission = submissions.filter(
                problem=problem
            ).order_by('-points', 'submitted_at').first()
            
            if best_submission:
                user_submissions[problem.id] = {
                    'id': best_submission.id,
                    'status': best_submission.status,
                    'points': best_submission.points,
                }
                
                if best_submission.status == 'accepted':
                    solved_problems += 1
                    total_points += best_submission.points
    
    # Вычисляем процент выполнения
    completion_percent = round((total_points / total_available_points) * 100) if total_available_points > 0 else 0
    
    context = {
        'olympiad': olympiad,
        'problems': problems,
        'duration': duration_str,
        'is_participating': is_participating,
        'user_submissions': user_submissions,
        'solved_problems': solved_problems,
        'total_points': total_points,
        'total_available_points': total_available_points,
        'completion_percent': completion_percent
    }
    
    return render(request, 'olympiads/olympiad_detail.html', context)


@login_required
def olympiad_register(request, slug):
    """Регистрирует пользователя для участия в олимпиаде"""
    olympiad = get_object_or_404(Olympiad, slug=slug, is_published=True)
    
    # Проверяем, что олимпиада активна или ещё не началась
    if olympiad.is_past():
        messages.error(request, "Невозможно зарегистрироваться. Олимпиада уже завершена.")
        return redirect('olympiad_detail', slug=slug)
    
    # Проверяем, уже ли пользователь участвует
    if OlympiadParticipant.objects.filter(olympiad=olympiad, user=request.user).exists():
        messages.info(request, "Вы уже зарегистрированы для участия в этой олимпиаде.")
    else:
        # Регистрируем пользователя
        OlympiadParticipant.objects.create(
            olympiad=olympiad,
            user=request.user
        )
        messages.success(request, f"Вы успешно зарегистрированы для участия в олимпиаде '{olympiad.title}'.")
    
    return redirect('olympiad_detail', slug=slug)


def problem_detail(request, olympiad_slug, pk):
    """Отображает детальную информацию о задаче олимпиады и форму отправки решения"""
    olympiad = get_object_or_404(Olympiad, slug=olympiad_slug, is_published=True)
    problem = get_object_or_404(Problem, pk=pk, olympiad=olympiad)
    
    # Проверка доступа к задаче
    can_submit = False
    is_participating = False
    
    if request.user.is_authenticated:
        is_participating = OlympiadParticipant.objects.filter(
            olympiad=olympiad, user=request.user
        ).exists()
        
        # Пользователь может отправлять решения, если он участник и олимпиада активна
        can_submit = is_participating and olympiad.is_active()
    
    # Получаем примеры тестовых случаев (is_example=True)
    examples = problem.test_cases.filter(is_example=True).order_by('order')
    
    # Считаем общее количество тестов
    test_count = problem.test_cases.count()
    
    # Получаем лучшую отправку пользователя для этой задачи
    best_submission = None
    submissions = []
    
    if request.user.is_authenticated:
        user_submissions = Submission.objects.filter(
            problem=problem,
            user=request.user
        ).order_by('-submitted_at')
        
        submissions = user_submissions[:5]  # Последние 5 отправок
        
        best_submission = user_submissions.order_by('-points', 'submitted_at').first()
    
    # Форма отправки решения
    form = SubmissionForm() if can_submit else None
    
    context = {
        'olympiad': olympiad,
        'problem': problem,
        'examples': examples,
        'test_count': test_count,
        'can_submit': can_submit,
        'is_participating': is_participating,
        'best_submission': best_submission,
        'submissions': submissions,
        'form': form
    }
    
    return render(request, 'olympiads/problem_detail.html', context)


@login_required
def submit_solution(request, olympiad_slug, problem_id):
    """Обрабатывает отправку решения задачи"""
    olympiad = get_object_or_404(Olympiad, slug=olympiad_slug, is_published=True)
    problem = get_object_or_404(Problem, pk=problem_id, olympiad=olympiad)
    
    # Проверяем, что пользователь зарегистрирован как участник
    is_participant = OlympiadParticipant.objects.filter(
        olympiad=olympiad, user=request.user
    ).exists()
    
    if not is_participant:
        messages.error(request, "Вы должны быть зарегистрированы как участник олимпиады.")
        return redirect('problem_detail', olympiad_slug=olympiad_slug, pk=problem_id)
    
    # Проверяем, что олимпиада активна
    if not olympiad.is_active():
        messages.error(request, "Отправка решений возможна только во время проведения олимпиады.")
        return redirect('problem_detail', olympiad_slug=olympiad_slug, pk=problem_id)
    
    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.problem = problem
            submission.olympiad = olympiad
            submission.save()
            
            # Здесь можно добавить запуск асинхронной задачи для проверки решения
            # from .tasks import check_submission
            # check_submission.delay(submission.id)
            
            messages.success(request, "Ваше решение отправлено на проверку.")
            return redirect('submission_detail', olympiad_slug=olympiad_slug, submission_id=submission.id)
    else:
        form = SubmissionForm()
    
    # Если мы здесь, значит форма невалидна или это GET-запрос
    context = {
        'olympiad': olympiad,
        'problem': problem,
        'form': form
    }
    
    return render(request, 'olympiads/problem_detail.html', context)


def submission_detail(request, olympiad_slug, submission_id):
    """Отображает детальную информацию о отправке решения"""
    olympiad = get_object_or_404(Olympiad, slug=olympiad_slug, is_published=True)
    submission = get_object_or_404(Submission, pk=submission_id, olympiad=olympiad)
    
    # Проверка прав доступа: только владелец, администраторы или после завершения олимпиады
    if not (request.user == submission.user or request.user.is_staff or olympiad.is_past()):
        messages.error(request, "У вас нет прав для просмотра этой отправки.")
        return redirect('olympiad_detail', slug=olympiad_slug)
    
    # Получаем результаты тестирования
    test_results = submission.test_results.all().order_by('test_case__order')
    
    # Определяем, показывать ли детали для непримерных тестов
    show_details = olympiad.is_past() or request.user.is_staff
    is_creator = request.user.is_staff
    
    context = {
        'olympiad': olympiad,
        'submission': submission,
        'test_results': test_results,
        'show_details': show_details,
        'is_creator': is_creator
    }
    
    return render(request, 'olympiads/submission_detail.html', context)


def submission_list(request, slug):
    """Отображает список отправок решений для олимпиады с фильтрацией"""
    olympiad = get_object_or_404(Olympiad, slug=slug, is_published=True)
    
    # Проверка доступа
    is_participating = False
    if request.user.is_authenticated:
        is_participating = OlympiadParticipant.objects.filter(
            olympiad=olympiad, user=request.user
        ).exists()
    
    if not (is_participating or request.user.is_staff or olympiad.is_past()):
        messages.error(request, "У вас нет прав для просмотра отправок.")
        return redirect('olympiad_detail', slug=slug)
    
    # Фильтрация
    submissions = Submission.objects.filter(olympiad=olympiad)
    
    # Если не администратор, показываем только отправки текущего пользователя
    if not request.user.is_staff:
        submissions = submissions.filter(user=request.user)
    
    # Фильтр по задаче
    problem_id = request.GET.get('problem')
    if problem_id:
        submissions = submissions.filter(problem_id=problem_id)
    
    # Фильтр по статусу
    status = request.GET.get('status')
    if status:
        submissions = submissions.filter(status=status)
    
    # Фильтр по пользователю (только для администраторов)
    user_id = request.GET.get('user')
    if user_id and request.user.is_staff:
        submissions = submissions.filter(user_id=user_id)
    
    # Сортировка по времени отправки (по умолчанию - сначала новые)
    submissions = submissions.order_by('-submitted_at')
    
    # Пагинация
    paginator = Paginator(submissions, 25)  # 25 отправок на странице
    page_number = request.GET.get('page')
    submissions = paginator.get_page(page_number)
    
    # Получаем список задач для фильтра
    problems = Problem.objects.filter(olympiad=olympiad).order_by('order')
    
    context = {
        'olympiad': olympiad,
        'submissions': submissions,
        'problem_id': int(problem_id) if problem_id and problem_id.isdigit() else None,
        'status': status,
        'problems': problems,
        'is_staff': request.user.is_staff
    }
    
    return render(request, 'olympiads/submission_list.html', context)


def olympiad_leaderboard(request, slug):
    """Отображает таблицу результатов олимпиады"""
    olympiad = get_object_or_404(Olympiad, slug=slug, is_published=True)
    
    # Получаем список участников, отсортированный по количеству баллов
    participants = OlympiadParticipant.objects.filter(
        olympiad=olympiad
    ).order_by('-total_points', '-solved_problems', 'registered_at')
    
    # Получаем список задач
    problems = Problem.objects.filter(olympiad=olympiad).order_by('order')
    
    # Собираем результаты для всех участников
    results = {}
    for participant in participants:
        # Обновляем статистику участника
        participant.update_statistics()
        
        # Получаем статус решения каждой задачи участником
        user_results = {
            'user_id': participant.user_id,
            'username': participant.user.username,
            'total_points': participant.total_points,
            'solved_problems': participant.solved_problems,
            'problems': {}
        }
        
        # Находим лучшие отправки пользователя для каждой задачи
        submissions = Submission.objects.filter(
            olympiad=olympiad,
            user=participant.user
        )
        
        for problem in problems:
            best_submission = submissions.filter(
                problem=problem
            ).order_by('-points', 'submitted_at').first()
            
            if best_submission:
                user_results['problems'][problem.id] = {
                    'status': best_submission.status,
                    'points': best_submission.points,
                    'submission_id': best_submission.id
                }
        
        results[participant.user_id] = user_results
    
    context = {
        'olympiad': olympiad,
        'participants': participants,
        'problems': problems,
        'results': results
    }
    
    return render(request, 'olympiads/leaderboard.html', context)


# Административные представления для управления олимпиадами

@login_required
def olympiad_create(request):
    """Создание новой олимпиады (только для персонала)"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для создания олимпиад.")
        return redirect('olympiad_list')
    
    if request.method == 'POST':
        form = OlympiadForm(request.POST)
        if form.is_valid():
            olympiad = form.save(commit=False)
            olympiad.creator = request.user
            olympiad.save()
            messages.success(request, f"Олимпиада '{olympiad.title}' успешно создана.")
            return redirect('olympiad_detail', slug=olympiad.slug)
    else:
        # Устанавливаем начальные значения для олимпиады
        tomorrow = timezone.now() + timedelta(days=1)
        next_week = tomorrow + timedelta(days=7)
        
        # Устанавливаем время начала на 10:00, а время окончания на 14:00
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = next_week.replace(hour=14, minute=0, second=0, microsecond=0)
        
        form = OlympiadForm(initial={
            'start_time': start_time,
            'end_time': end_time,
            'is_published': False
        })
    
    context = {
        'form': form,
        'is_creating': True
    }
    
    return render(request, 'olympiads/olympiad_form.html', context)


@login_required
def olympiad_edit(request, slug):
    """Редактирование существующей олимпиады (только для персонала)"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для редактирования олимпиад.")
        return redirect('olympiad_list')
    
    olympiad = get_object_or_404(Olympiad, slug=slug)
    
    if request.method == 'POST':
        form = OlympiadForm(request.POST, instance=olympiad)
        if form.is_valid():
            form.save()
            messages.success(request, f"Олимпиада '{olympiad.title}' успешно обновлена.")
            return redirect('olympiad_detail', slug=olympiad.slug)
    else:
        form = OlympiadForm(instance=olympiad)
    
    context = {
        'form': form,
        'olympiad': olympiad,
        'is_creating': False
    }
    
    return render(request, 'olympiads/olympiad_form.html', context)


@login_required
def olympiad_delete(request, slug):
    """Удаление олимпиады (только для персонала)"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для удаления олимпиад.")
        return redirect('olympiad_list')
    
    olympiad = get_object_or_404(Olympiad, slug=slug)
    
    if request.method == 'POST':
        olympiad.delete()
        messages.success(request, f"Олимпиада '{olympiad.title}' успешно удалена.")
        return redirect('olympiad_list')
    
    return redirect('olympiad_detail', slug=slug)


@login_required
def olympiad_publish(request, slug):
    """Публикация олимпиады (только для персонала)"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для публикации олимпиад.")
        return redirect('olympiad_list')
    
    olympiad = get_object_or_404(Olympiad, slug=slug)
    
    if request.method == 'POST':
        olympiad.is_published = not olympiad.is_published
        olympiad.save()
        
        status = "опубликована" if olympiad.is_published else "снята с публикации"
        messages.success(request, f"Олимпиада '{olympiad.title}' успешно {status}.")
    
    return redirect('olympiad_detail', slug=slug)


@login_required
def problem_create(request, olympiad_slug):
    """Создание новой задачи для олимпиады (только для персонала)"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для создания задач.")
        return redirect('olympiad_detail', slug=olympiad_slug)
    
    olympiad = get_object_or_404(Olympiad, slug=olympiad_slug)
    
    if request.method == 'POST':
        form = ProblemForm(request.POST)
        if form.is_valid():
            problem = form.save(commit=False)
            problem.olympiad = olympiad
            
            # Устанавливаем порядковый номер
            if not problem.order:
                max_order = Problem.objects.filter(olympiad=olympiad).aggregate(Max('order'))['order__max'] or 0
                problem.order = max_order + 1
            
            problem.save()
            messages.success(request, f"Задача '{problem.title}' успешно создана.")
            return redirect('problem_detail', olympiad_slug=olympiad_slug, pk=problem.pk)
    else:
        form = ProblemForm()
    
    context = {
        'form': form,
        'olympiad': olympiad,
        'is_creating': True
    }
    
    return render(request, 'olympiads/problem_form.html', context)


@login_required
def problem_edit(request, olympiad_slug, pk):
    """Редактирование задачи олимпиады (только для персонала)"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для редактирования задач.")
        return redirect('olympiad_detail', slug=olympiad_slug)
    
    olympiad = get_object_or_404(Olympiad, slug=olympiad_slug)
    problem = get_object_or_404(Problem, pk=pk, olympiad=olympiad)
    
    if request.method == 'POST':
        form = ProblemForm(request.POST, instance=problem)
        if form.is_valid():
            form.save()
            messages.success(request, f"Задача '{problem.title}' успешно обновлена.")
            return redirect('problem_detail', olympiad_slug=olympiad_slug, pk=problem.pk)
    else:
        form = ProblemForm(instance=problem)
    
    # Получаем список тестовых случаев для этой задачи
    test_cases = TestCase.objects.filter(problem=problem).order_by('order')
    
    context = {
        'form': form,
        'olympiad': olympiad,
        'problem': problem,
        'test_cases': test_cases,
        'is_creating': False
    }
    
    return render(request, 'olympiads/problem_form.html', context)


@login_required
def problem_delete(request, olympiad_slug, pk):
    """Удаление задачи олимпиады (только для персонала)"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для удаления задач.")
        return redirect('olympiad_detail', slug=olympiad_slug)
    
    olympiad = get_object_or_404(Olympiad, slug=olympiad_slug)
    problem = get_object_or_404(Problem, pk=pk, olympiad=olympiad)
    
    if request.method == 'POST':
        problem.delete()
        messages.success(request, f"Задача '{problem.title}' успешно удалена.")
        return redirect('olympiad_detail', slug=olympiad_slug)
    
    return redirect('problem_detail', olympiad_slug=olympiad_slug, pk=pk)


@login_required
def testcase_create(request, olympiad_slug, problem_pk):
    """Создание нового тестового случая для задачи (только для персонала)"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для создания тестовых случаев.")
        return redirect('problem_detail', olympiad_slug=olympiad_slug, pk=problem_pk)
    
    olympiad = get_object_or_404(Olympiad, slug=olympiad_slug)
    problem = get_object_or_404(Problem, pk=problem_pk, olympiad=olympiad)
    
    if request.method == 'POST':
        form = TestCaseForm(request.POST)
        if form.is_valid():
            test_case = form.save(commit=False)
            test_case.problem = problem
            
            # Устанавливаем порядковый номер
            if not test_case.order:
                max_order = TestCase.objects.filter(problem=problem).aggregate(Max('order'))['order__max'] or 0
                test_case.order = max_order + 1
            
            test_case.save()
            messages.success(request, "Тестовый случай успешно создан.")
            return redirect('problem_edit', olympiad_slug=olympiad_slug, pk=problem_pk)
    else:
        form = TestCaseForm()
    
    context = {
        'form': form,
        'olympiad': olympiad,
        'problem': problem,
        'is_creating': True
    }
    
    return render(request, 'olympiads/testcase_form.html', context)


@login_required
def testcase_edit(request, olympiad_slug, problem_pk, pk):
    """Редактирование тестового случая (только для персонала)"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для редактирования тестовых случаев.")
        return redirect('problem_detail', olympiad_slug=olympiad_slug, pk=problem_pk)
    
    olympiad = get_object_or_404(Olympiad, slug=olympiad_slug)
    problem = get_object_or_404(Problem, pk=problem_pk, olympiad=olympiad)
    test_case = get_object_or_404(TestCase, pk=pk, problem=problem)
    
    if request.method == 'POST':
        form = TestCaseForm(request.POST, instance=test_case)
        if form.is_valid():
            form.save()
            messages.success(request, "Тестовый случай успешно обновлен.")
            return redirect('problem_edit', olympiad_slug=olympiad_slug, pk=problem_pk)
    else:
        form = TestCaseForm(instance=test_case)
    
    context = {
        'form': form,
        'olympiad': olympiad,
        'problem': problem,
        'test_case': test_case,
        'is_creating': False
    }
    
    return render(request, 'olympiads/testcase_form.html', context)


@login_required
def testcase_delete(request, olympiad_slug, problem_pk, pk):
    """Удаление тестового случая (только для персонала)"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для удаления тестовых случаев.")
        return redirect('problem_detail', olympiad_slug=olympiad_slug, pk=problem_pk)
    
    olympiad = get_object_or_404(Olympiad, slug=olympiad_slug)
    problem = get_object_or_404(Problem, pk=problem_pk, olympiad=olympiad)
    test_case = get_object_or_404(TestCase, pk=pk, problem=problem)
    
    if request.method == 'POST':
        test_case.delete()
        messages.success(request, "Тестовый случай успешно удален.")
    
    return redirect('problem_edit', olympiad_slug=olympiad_slug, pk=problem_pk)