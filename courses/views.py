from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Course, Category, Enrollment
from .forms import CourseForm, CategoryForm
from lessons.models import Lesson

def course_list(request):
    """Отображение списка опубликованных курсов"""
    courses = Course.objects.filter(is_published=True).order_by('-created_at')
    categories = Category.objects.all()
    
    # Фильтрация по категории
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        courses = courses.filter(category=category)
    
    # Поиск по названию
    search_query = request.GET.get('search')
    if search_query:
        courses = courses.filter(title__icontains=search_query)
    
    # Пагинация
    paginator = Paginator(courses, 9)  # 9 курсов на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_slug
    }
    
    return render(request, 'courses/course_list.html', context)

def course_detail(request, slug):
    """Отображение детальной страницы курса"""
    course = get_object_or_404(Course, slug=slug)
    
    # Если курс не опубликован, то его могут видеть только автор и администраторы
    if not course.is_published and not (
        request.user.is_authenticated and 
        (request.user == course.author or request.user.profile.is_admin())
    ):
        messages.error(request, 'Этот курс недоступен.')
        return redirect('course_list')
    
    # Проверяем, зачислен ли текущий пользователь на курс
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    
    # Получаем список уроков курса
    lessons = Lesson.objects.filter(course=course).order_by('order')
    
    context = {
        'course': course,
        'lessons': lessons,
        'is_enrolled': is_enrolled,
        'enrolled_count': course.enrolled_students_count()
    }
    
    return render(request, 'courses/course_detail.html', context)

@login_required
def course_create(request):
    """Создание нового курса (только для преподавателей и администраторов)"""
    # Проверка прав доступа
    if not (request.user.profile.role == 'teacher' or request.user.profile.role == 'admin'):
        messages.error(request, 'У вас нет прав для создания курсов.')
        return redirect('course_list')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.author = request.user
            course.save()
            messages.success(request, f'Курс "{course.title}" успешно создан!')
            return redirect('course_detail', slug=course.slug)
    else:
        form = CourseForm()
    
    context = {
        'form': form,
        'title': 'Создание нового курса'
    }
    
    return render(request, 'courses/course_create.html', context)

@login_required
def course_edit(request, slug):
    """Редактирование курса (только для автора и администраторов)"""
    course = get_object_or_404(Course, slug=slug)
    
    # Проверка прав доступа
    if request.user != course.author and not request.user.profile.role == 'admin':
        messages.error(request, 'У вас нет прав для редактирования этого курса.')
        return redirect('course_detail', slug=course.slug)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Курс "{course.title}" успешно обновлен!')
            return redirect('course_detail', slug=course.slug)
    else:
        form = CourseForm(instance=course)
    
    context = {
        'form': form,
        'course': course,
        'title': 'Редактирование курса'
    }
    
    return render(request, 'courses/course_edit.html', context)


@login_required
def course_edit_content(request, slug):
    """Редактирование содержимого курса (уроки и материалы)"""
    from django.db import models
    from lessons.models import Lesson, LessonContent
    from lessons.forms import LessonForm, LessonContentForm
    
    course = get_object_or_404(Course, slug=slug)
    
    # Проверка прав доступа
    if request.user != course.author and not request.user.profile.role == 'admin':
        messages.error(request, 'У вас нет прав для редактирования содержимого этого курса.')
        return redirect('course_detail', slug=course.slug)
    
    # Получаем все уроки курса с их содержимым
    lessons = Lesson.objects.filter(course=course).order_by('order')
    
    context = {
        'course': course,
        'lessons': lessons,
        'title': 'Редактирование содержимого курса'
    }
    
    # Если это POST запрос для обновления урока
    if request.method == 'POST' and 'lesson_id' in request.POST:
        lesson_id = request.POST.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        
        lesson_form = LessonForm(request.POST, instance=lesson)
        if lesson_form.is_valid():
            lesson_form.save()
            
            # Если урок содержит содержимое, обновляем его
            if hasattr(lesson, 'content'):
                content_form = LessonContentForm(request.POST, instance=lesson.content)
                if content_form.is_valid():
                    content_form.save()
            else:
                # Создаем новое содержимое для урока
                content_form = LessonContentForm(request.POST)
                if content_form.is_valid():
                    content = content_form.save(commit=False)
                    content.lesson = lesson
                    content.save()
            
            messages.success(request, f'Урок "{lesson.title}" успешно обновлен!')
            return redirect('course_edit_content', slug=course.slug)
    
    # Если это POST запрос для создания нового урока
    elif request.method == 'POST' and 'new_lesson' in request.POST:
        lesson_form = LessonForm(request.POST)
        content_form = LessonContentForm(request.POST)
        
        if lesson_form.is_valid():
            lesson = lesson_form.save(commit=False)
            lesson.course = course
            
            # Определяем порядковый номер для нового урока
            if not lesson.order:
                max_order = lessons.aggregate(models.Max('order'))['order__max'] or 0
                lesson.order = max_order + 1
            
            lesson.save()
            
            if content_form.is_valid():
                content = content_form.save(commit=False)
                content.lesson = lesson
                content.save()
            
            messages.success(request, f'Новый урок "{lesson.title}" успешно создан!')
            return redirect('course_edit_content', slug=course.slug)
    
    # Если это POST запрос для удаления урока
    elif request.method == 'POST' and 'delete_lesson' in request.POST:
        lesson_id = request.POST.get('delete_lesson')
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        lesson_title = lesson.title
        lesson.delete()
        
        messages.success(request, f'Урок "{lesson_title}" успешно удален!')
        return redirect('course_edit_content', slug=course.slug)
    
    return render(request, 'courses/course_edit_content.html', context)

@login_required
def course_delete(request, slug):
    """Удаление курса (только для автора и администраторов)"""
    course = get_object_or_404(Course, slug=slug)
    
    # Проверка прав доступа
    if request.user != course.author and not request.user.profile.role == 'admin':
        messages.error(request, 'У вас нет прав для удаления этого курса.')
        return redirect('course_detail', slug=course.slug)
    
    if request.method == 'POST':
        course_title = course.title
        course.delete()
        messages.success(request, f'Курс "{course_title}" успешно удален!')
        return redirect('course_list')
    
    context = {
        'course': course
    }
    
    return render(request, 'courses/course_delete.html', context)

@login_required
def course_enroll(request, slug):
    """Зачисление пользователя на курс"""
    course = get_object_or_404(Course, slug=slug)
    
    # Проверяем, опубликован ли курс
    if not course.is_published:
        messages.error(request, 'Этот курс недоступен для зачисления.')
        return redirect('course_list')
    
    # Проверяем, не зачислен ли уже пользователь
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, 'Вы уже зачислены на этот курс.')
    else:
        Enrollment.objects.create(user=request.user, course=course)
        messages.success(request, f'Вы успешно зачислены на курс "{course.title}"!')
    
    return redirect('course_detail', slug=course.slug)

def category_detail(request, slug):
    """Отображение курсов определенной категории"""
    category = get_object_or_404(Category, slug=slug)
    courses = Course.objects.filter(category=category, is_published=True).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(courses, 9)  # 9 курсов на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj
    }
    
    return render(request, 'courses/category_detail.html', context)

@login_required
def my_courses(request):
    """Отображение курсов пользователя (созданных или на которые записан)"""
    # Курсы, созданные пользователем
    created_courses = Course.objects.filter(author=request.user).order_by('-created_at')
    
    # Курсы, на которые записан пользователь
    enrollments = Enrollment.objects.filter(user=request.user).order_by('-enrolled_at')
    
    context = {
        'created_courses': created_courses,
        'enrollments': enrollments
    }
    
    return render(request, 'courses/my_courses.html', context)
