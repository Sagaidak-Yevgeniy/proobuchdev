from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Assignment, TestCase, AssignmentSubmission
from .forms import AssignmentForm, TestCaseForm, SubmissionForm
from .code_checker import check_assignment
from courses.models import Enrollment

@login_required
def assignment_detail(request, pk):
    """Отображение детальной страницы задания"""
    assignment = get_object_or_404(Assignment, pk=pk)
    lesson_content = assignment.lesson_content
    lesson = lesson_content.lesson
    course = lesson.course
    
    # Проверяем, имеет ли пользователь доступ к заданию
    is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    is_author = (request.user == course.author)
    is_admin = request.user.profile.is_admin()
    
    if not (is_enrolled or is_author or is_admin) and not assignment.is_public:
        messages.error(request, 'У вас нет доступа к данному заданию.')
        return redirect('course_detail', slug=course.slug)
    
    # Получаем видимые тесты
    visible_test_cases = assignment.test_cases.filter(is_hidden=False)
    
    # Получаем последнюю отправку пользователя
    latest_submission = AssignmentSubmission.objects.filter(
        user=request.user,
        assignment=assignment
    ).order_by('-submitted_at').first()
    
    # Получаем все отправки пользователя
    all_submissions = AssignmentSubmission.objects.filter(
        user=request.user,
        assignment=assignment
    ).order_by('-submitted_at')
    
    # Статистика по заданию
    submission_count = assignment.get_submission_count()
    success_rate = assignment.get_success_rate()
    
    context = {
        'assignment': assignment,
        'lesson_content': lesson_content,
        'lesson': lesson,
        'course': course,
        'visible_test_cases': visible_test_cases,
        'latest_submission': latest_submission,
        'all_submissions': all_submissions,
        'submission_count': submission_count,
        'success_rate': success_rate,
        'is_author': is_author,
        'is_admin': is_admin
    }
    
    return render(request, 'assignments/assignment_detail.html', context)

@login_required
def assignment_solve(request, pk):
    """Страница решения задания"""
    assignment = get_object_or_404(Assignment, pk=pk)
    lesson_content = assignment.lesson_content
    lesson = lesson_content.lesson
    course = lesson.course
    
    # Проверяем, имеет ли пользователь доступ к заданию
    is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    
    if not is_enrolled and not assignment.is_public:
        messages.error(request, 'Вы должны быть зачислены на курс, чтобы решать это задание.')
        return redirect('course_detail', slug=course.slug)
    
    # Получаем видимые тесты
    visible_test_cases = assignment.test_cases.filter(is_hidden=False)
    
    # Получаем последнюю отправку пользователя или создаем новую с начальным кодом
    latest_submission = AssignmentSubmission.objects.filter(
        user=request.user,
        assignment=assignment
    ).order_by('-submitted_at').first()
    
    initial_code = latest_submission.code if latest_submission else assignment.initial_code
    
    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.assignment = assignment
            submission.status = 'pending'
            submission.save()
            
            # Проверяем решение
            check_assignment(submission)
            
            if submission.status == 'passed':
                messages.success(request, 'Поздравляем! Ваше решение успешно прошло все тесты.')
            else:
                messages.warning(request, 'Ваше решение не прошло некоторые тесты. Попробуйте еще раз.')
            
            return redirect('submission_detail', pk=submission.pk)
    else:
        form = SubmissionForm(initial={'code': initial_code})
    
    context = {
        'form': form,
        'assignment': assignment,
        'lesson': lesson,
        'course': course,
        'visible_test_cases': visible_test_cases,
        'latest_submission': latest_submission
    }
    
    return render(request, 'assignments/assignment_solve.html', context)

@login_required
def assignment_edit(request, pk):
    """Редактирование задания"""
    assignment = get_object_or_404(Assignment, pk=pk)
    lesson_content = assignment.lesson_content
    lesson = lesson_content.lesson
    course = lesson.course
    
    # Проверка прав доступа
    if request.user != course.author and not request.user.profile.is_admin():
        messages.error(request, 'У вас нет прав для редактирования этого задания.')
        return redirect('assignment_detail', pk=assignment.pk)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Задание "{assignment.title}" успешно обновлено!')
            
            # Обновляем содержимое урока, если необходимо
            lesson_content.content = form.cleaned_data.get('task_description')
            lesson_content.save()
            
            return redirect('assignment_detail', pk=assignment.pk)
    else:
        form = AssignmentForm(instance=assignment)
    
    context = {
        'form': form,
        'assignment': assignment,
        'lesson': lesson,
        'course': course,
        'title': 'Редактирование задания'
    }
    
    return render(request, 'assignments/assignment_edit.html', context)

@login_required
def submission_detail(request, pk):
    """Отображение детальной страницы отправки решения"""
    submission = get_object_or_404(AssignmentSubmission, pk=pk)
    assignment = submission.assignment
    lesson_content = assignment.lesson_content
    lesson = lesson_content.lesson
    course = lesson.course
    
    # Проверяем, имеет ли пользователь доступ к этой отправке
    if request.user != submission.user and request.user != course.author and not request.user.profile.is_admin():
        messages.error(request, 'У вас нет доступа к этой отправке.')
        return redirect('assignment_detail', pk=assignment.pk)
    
    context = {
        'submission': submission,
        'assignment': assignment,
        'lesson': lesson,
        'course': course
    }
    
    return render(request, 'assignments/submission_detail.html', context)

@login_required
def test_case_create(request, assignment_id):
    """Создание тестового случая для задания"""
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    lesson_content = assignment.lesson_content
    lesson = lesson_content.lesson
    course = lesson.course
    
    # Проверка прав доступа
    if request.user != course.author and not request.user.profile.is_admin():
        messages.error(request, 'У вас нет прав для добавления тестовых случаев к этому заданию.')
        return redirect('assignment_detail', pk=assignment.pk)
    
    if request.method == 'POST':
        form = TestCaseForm(request.POST)
        if form.is_valid():
            test_case = form.save(commit=False)
            test_case.assignment = assignment
            test_case.save()
            messages.success(request, 'Тестовый случай успешно добавлен!')
            
            # Спрашиваем, хочет ли пользователь добавить еще тестовый случай или вернуться к заданию
            if 'add_more' in request.POST:
                return redirect('test_case_create', assignment_id=assignment.id)
            else:
                return redirect('assignment_detail', pk=assignment.pk)
    else:
        form = TestCaseForm()
    
    context = {
        'form': form,
        'assignment': assignment,
        'lesson': lesson,
        'course': course,
        'title': 'Добавление тестового случая'
    }
    
    return render(request, 'assignments/test_case_create.html', context)

@login_required
def test_case_edit(request, pk):
    """Редактирование тестового случая"""
    test_case = get_object_or_404(TestCase, pk=pk)
    assignment = test_case.assignment
    lesson_content = assignment.lesson_content
    lesson = lesson_content.lesson
    course = lesson.course
    
    # Проверка прав доступа
    if request.user != course.author and not request.user.profile.is_admin():
        messages.error(request, 'У вас нет прав для редактирования этого тестового случая.')
        return redirect('assignment_detail', pk=assignment.pk)
    
    if request.method == 'POST':
        form = TestCaseForm(request.POST, instance=test_case)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тестовый случай успешно обновлен!')
            return redirect('assignment_detail', pk=assignment.pk)
    else:
        form = TestCaseForm(instance=test_case)
    
    context = {
        'form': form,
        'test_case': test_case,
        'assignment': assignment,
        'lesson': lesson,
        'course': course,
        'title': 'Редактирование тестового случая'
    }
    
    return render(request, 'assignments/test_case_edit.html', context)

@login_required
def test_case_delete(request, pk):
    """Удаление тестового случая"""
    test_case = get_object_or_404(TestCase, pk=pk)
    assignment = test_case.assignment
    lesson_content = assignment.lesson_content
    lesson = lesson_content.lesson
    course = lesson.course
    
    # Проверка прав доступа
    if request.user != course.author and not request.user.profile.is_admin():
        messages.error(request, 'У вас нет прав для удаления этого тестового случая.')
        return redirect('assignment_detail', pk=assignment.pk)
    
    if request.method == 'POST':
        test_case.delete()
        messages.success(request, 'Тестовый случай успешно удален!')
        return redirect('assignment_detail', pk=assignment.pk)
    
    context = {
        'test_case': test_case,
        'assignment': assignment,
        'lesson': lesson,
        'course': course
    }
    
    return render(request, 'assignments/test_case_delete.html', context)
