from django import template
from django.utils.safestring import mark_safe
from olympiads.models import OlympiadTaskSubmission

register = template.Library()

@register.filter
def is_correct(task, participation):
    """Проверяет, правильно ли выполнено задание"""
    submission = OlympiadTaskSubmission.objects.filter(
        participation=participation, 
        task=task, 
        is_correct=True
    ).first()
    return submission is not None

@register.filter
def is_attempted(task, participation):
    """Проверяет, была ли попытка выполнить задание"""
    submission = OlympiadTaskSubmission.objects.filter(
        participation=participation, 
        task=task
    ).first()
    return submission is not None

@register.filter
def get_item(dictionary, key):
    """Получает значение из словаря по ключу"""
    return dictionary.get(key, {})

@register.filter
def task_status_badge(task, participation):
    """Возвращает HTML-бейдж со статусом задания"""
    submission = OlympiadTaskSubmission.objects.filter(
        participation=participation, 
        task=task
    ).order_by('-submitted_at').first()
    
    if not submission:
        return mark_safe('<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200">Не начато</span>')
    
    if submission.is_correct:
        return mark_safe('<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200"><svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg>Выполнено</span>')
    
    return mark_safe('<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200"><svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>В процессе</span>')

@register.filter
def task_score(task, participation):
    """Возвращает баллы за задание"""
    submission = OlympiadTaskSubmission.objects.filter(
        participation=participation, 
        task=task
    ).order_by('-submitted_at').first()
    
    if not submission:
        return f"0/{task.points}"
    
    return f"{submission.score}/{task.points}"

@register.filter
def task_availability_icon(task, task_statuses):
    """Возвращает иконку доступности задания"""
    task_status = task_statuses.get(task.id, {})
    
    if task_status.get('is_correct', False):
        return mark_safe('<i class="fas fa-check-circle text-green-500"></i>')
    
    if task_status.get('available', False):
        return mark_safe('<i class="fas fa-unlock text-blue-500"></i>')
    
    return mark_safe('<i class="fas fa-lock text-gray-500"></i>')

@register.filter
def percentage(value, max_value):
    """Вычисляет процент от максимального значения"""
    if not max_value:
        return 0
    return int((float(value) / float(max_value)) * 100)

@register.filter
def multiply(value, arg):
    """Умножает значение на аргумент"""
    return float(value) * float(arg)

@register.filter
def divide(value, arg):
    """Делит значение на аргумент"""
    if not arg:
        return 0
    return float(value) / float(arg)

@register.filter
def subtract(value, arg):
    """Вычитает аргумент из значения"""
    return float(value) - float(arg)