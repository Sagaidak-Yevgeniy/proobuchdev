from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from courses.models import Course, Enrollment
from .models import Lesson, LessonContent, LessonCompletion
from .forms import LessonForm, LessonContentForm
from assignments.models import Assignment, AssignmentSubmission

@login_required
def lesson_detail(request, pk):
    """Отображение детальной страницы урока"""
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.course
    
    # Проверяем, имеет ли пользователь доступ к уроку
    is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    is_author = (request.user == course.author)
    is_admin = request.user.profile.is_admin()
    
    if not (is_enrolled or is_author or is_admin):
        messages.error(request, 'У вас нет доступа к данному уроку. Пожалуйста, запишитесь на курс.')
        return redirect('course_detail', slug=course.slug)
    
    # Получаем все содержимое урока
    contents = lesson.contents.all().order_by('id')
    
    # Проверяем статус завершения урока для пользователя
    lesson_completion, created = LessonCompletion.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    
    # Проверяем, есть ли у урока задания и их статус выполнения
    assignments = []
    for content in contents:
        if content.content_type == 'assignment':
            assignment, _ = Assignment.objects.get_or_create(
                lesson_content=content,
                defaults={'title': f'Задание к уроку {lesson.title}'}
            )
            
            submission = AssignmentSubmission.objects.filter(
                assignment=assignment,
                user=request.user
            ).order_by('-submitted_at').first()
            
            assignments.append({
                'assignment': assignment,
                'submission': submission
            })
    
    # Получаем предыдущий и следующий уроки
    next_lesson = lesson.get_next_lesson()
    prev_lesson = lesson.get_previous_lesson()
    
    context = {
        'lesson': lesson,
        'course': course,
        'contents': contents,
        'next_lesson': next_lesson,
        'prev_lesson': prev_lesson,
        'lesson_completion': lesson_completion,
        'assignments': assignments,
        'is_enrolled': is_enrolled,
        'is_author': is_author
    }
    
    return render(request, 'lessons/lesson_detail.html', context)

@login_required
def lesson_create(request, course_id):
    """Создание нового урока для курса"""
    course = get_object_or_404(Course, id=course_id)
    
    # Проверка прав доступа
    if request.user != course.author and not request.user.profile.is_admin():
        messages.error(request, 'У вас нет прав для добавления уроков в этот курс.')
        return redirect('course_detail', slug=course.slug)
    
    # Определяем порядковый номер для нового урока
    last_lesson = Lesson.objects.filter(course=course).order_by('-order').first()
    next_order = 1 if not last_lesson else last_lesson.order + 1
    
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, f'Урок "{lesson.title}" успешно создан!')
            
            # Перенаправляем на создание содержимого урока
            return redirect('lesson_content_create', lesson_id=lesson.id)
    else:
        form = LessonForm(initial={'order': next_order})
    
    context = {
        'form': form,
        'course': course,
        'title': 'Создание нового урока'
    }
    
    return render(request, 'lessons/lesson_create.html', context)

@login_required
def lesson_edit(request, pk):
    """Редактирование урока"""
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.course
    
    # Проверка прав доступа
    if request.user != course.author and not request.user.profile.is_admin():
        messages.error(request, 'У вас нет прав для редактирования этого урока.')
        return redirect('lesson_detail', pk=lesson.pk)
    
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, f'Урок "{lesson.title}" успешно обновлен!')
            return redirect('lesson_detail', pk=lesson.pk)
    else:
        form = LessonForm(instance=lesson)
    
    context = {
        'form': form,
        'lesson': lesson,
        'course': course,
        'title': 'Редактирование урока'
    }
    
    return render(request, 'lessons/lesson_edit.html', context)

@login_required
def lesson_delete(request, pk):
    """Удаление урока"""
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.course
    
    # Проверка прав доступа
    if request.user != course.author and not request.user.profile.is_admin():
        messages.error(request, 'У вас нет прав для удаления этого урока.')
        return redirect('lesson_detail', pk=lesson.pk)
    
    if request.method == 'POST':
        course_slug = course.slug
        lesson_title = lesson.title
        lesson.delete()
        messages.success(request, f'Урок "{lesson_title}" успешно удален!')
        return redirect('course_detail', slug=course_slug)
    
    context = {
        'lesson': lesson,
        'course': course
    }
    
    return render(request, 'lessons/lesson_delete.html', context)

@login_required
def lesson_complete(request, pk):
    """Отметка урока как завершенного"""
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.course
    
    # Проверяем, зачислен ли пользователь на курс
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    
    # Получаем или создаем объект завершения урока
    lesson_completion, created = LessonCompletion.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    
    # Меняем статус завершения
    lesson_completion.completed = not lesson_completion.completed
    if lesson_completion.completed:
        lesson_completion.completed_at = timezone.now()
    else:
        lesson_completion.completed_at = None
    lesson_completion.save()
    
    # Обновляем прогресс курса
    enrollment.update_progress()
    
    status = 'завершен' if lesson_completion.completed else 'не завершен'
    messages.success(request, f'Урок "{lesson.title}" отмечен как {status}.')
    
    return redirect('lesson_detail', pk=lesson.pk)

@login_required
def lesson_content_detail(request, pk):
    """Отображение детальной страницы содержимого урока"""
    content = get_object_or_404(LessonContent, pk=pk)
    lesson = content.lesson
    course = lesson.course
    
    # Проверяем, имеет ли пользователь доступ к уроку
    is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    is_author = (request.user == course.author)
    is_admin = request.user.profile.is_admin()
    
    if not (is_enrolled or is_author or is_admin):
        messages.error(request, 'У вас нет доступа к данному содержимому.')
        return redirect('course_detail', slug=course.slug)
    
    # Если это задание, перенаправляем на страницу задания
    if content.content_type == 'assignment':
        assignment, created = Assignment.objects.get_or_create(
            lesson_content=content,
            defaults={'title': f'Задание к уроку {lesson.title}'}
        )
        return redirect('assignment_detail', pk=assignment.pk)
    
    context = {
        'content': content,
        'lesson': lesson,
        'course': course,
        'is_author': is_author,
        'is_admin': is_admin
    }
    
    return render(request, 'lessons/lesson_content_detail.html', context)

@login_required
def lesson_content_create(request, lesson_id):
    """Создание нового содержимого для урока"""
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    course = lesson.course
    
    # Проверка прав доступа
    if request.user != course.author and not request.user.profile.is_admin():
        messages.error(request, 'У вас нет прав для добавления содержимого в этот урок.')
        return redirect('lesson_detail', pk=lesson.pk)
    
    if request.method == 'POST':
        form = LessonContentForm(request.POST)
        if form.is_valid():
            content = form.save(commit=False)
            content.lesson = lesson
            content.save()
            
            content_type = form.cleaned_data.get('content_type')
            
            # Если создано задание, создаем соответствующий объект Assignment
            if content_type == 'assignment':
                from assignments.models import Assignment
                Assignment.objects.create(
                    lesson_content=content,
                    title=f'Задание к уроку {lesson.title}'
                )
                messages.success(request, 'Задание успешно создано!')
            else:
                messages.success(request, f'{content.get_content_type_display()} успешно добавлен в урок!')
            
            # Спрашиваем, хочет ли пользователь добавить еще содержимое или вернуться к уроку
            if 'add_more' in request.POST:
                return redirect('lesson_content_create', lesson_id=lesson.id)
            else:
                return redirect('lesson_detail', pk=lesson.pk)
    else:
        form = LessonContentForm()
    
    context = {
        'form': form,
        'lesson': lesson,
        'course': course,
        'title': 'Добавление содержимого к уроку'
    }
    
    return render(request, 'lessons/lesson_content_create.html', context)

@login_required
def lesson_content_edit(request, pk):
    """Редактирование содержимого урока"""
    content = get_object_or_404(LessonContent, pk=pk)
    lesson = content.lesson
    course = lesson.course
    
    # Проверка прав доступа
    if request.user != course.author and not request.user.profile.is_admin():
        messages.error(request, 'У вас нет прав для редактирования этого содержимого.')
        return redirect('lesson_detail', pk=lesson.pk)
    
    if request.method == 'POST':
        form = LessonContentForm(request.POST, instance=content)
        if form.is_valid():
            form.save()
            
            # Если изменился тип содержимого на задание, создаем объект Assignment
            if form.cleaned_data.get('content_type') == 'assignment':
                from assignments.models import Assignment
                Assignment.objects.get_or_create(
                    lesson_content=content,
                    defaults={'title': f'Задание к уроку {lesson.title}'}
                )
            
            messages.success(request, 'Содержимое урока успешно обновлено!')
            return redirect('lesson_detail', pk=lesson.pk)
    else:
        form = LessonContentForm(instance=content)
    
    context = {
        'form': form,
        'content': content,
        'lesson': lesson,
        'course': course,
        'title': 'Редактирование содержимого урока'
    }
    
    return render(request, 'lessons/lesson_content_edit.html', context)

@login_required
def lesson_content_delete(request, pk):
    """Удаление содержимого урока"""
    content = get_object_or_404(LessonContent, pk=pk)
    lesson = content.lesson
    course = lesson.course
    
    # Проверка прав доступа
    if request.user != course.author and not request.user.profile.is_admin():
        messages.error(request, 'У вас нет прав для удаления этого содержимого.')
        return redirect('lesson_detail', pk=lesson.pk)
    
    if request.method == 'POST':
        content.delete()
        messages.success(request, 'Содержимое урока успешно удалено!')
        return redirect('lesson_detail', pk=lesson.pk)
    
    context = {
        'content': content,
        'lesson': lesson,
        'course': course
    }
    
    return render(request, 'lessons/lesson_content_delete.html', context)
