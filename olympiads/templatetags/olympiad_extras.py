from django import template
from django.template.defaultfilters import stringfilter
import datetime

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Получает элемент словаря по ключу в шаблоне"""
    return dictionary.get(str(key)) if dictionary else None

@register.filter(name='selectattr')
def selectattr(iterable, attr):
    """Фильтрует список объектов по атрибуту"""
    result = []
    for item in iterable:
        if isinstance(item, dict) and attr in item and item[attr]:
            result.append(item)
        elif hasattr(item, attr) and getattr(item, attr):
            result.append(item)
    return result

@register.filter(name='mul')
def mul(value, arg):
    """Умножает два числа"""
    return float(value) * float(arg)

@register.filter(name='div')
def div(value, arg):
    """Делит два числа"""
    if float(arg) == 0:
        return 0
    return float(value) / float(arg)

@register.filter(name='add')
def add_minutes(value, arg):
    """Добавляет указанное количество минут к datetime"""
    if not value:
        return value
    return value + datetime.timedelta(minutes=int(arg))

@register.filter(name='list')
def to_list(value):
    """Преобразует значение в список"""
    return list(value)

@register.simple_tag
def get_task_status(task_statuses, task_id):
    """Возвращает статус задания по его ID"""
    status = task_statuses.get(str(task_id), {})
    if status.get('is_correct'):
        return 'correct'
    elif status.get('submitted'):
        return 'submitted'
    return 'not_submitted'

@register.simple_tag
def get_progress_percentage(completed, total):
    """Вычисляет процент выполнения"""
    if int(total) == 0:
        return 0
    return int(int(completed) * 100 / int(total))