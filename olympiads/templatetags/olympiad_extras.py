from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def is_correct(task, participation):
    """
    Проверяет, правильно ли решено задание пользователем
    
    Args:
        task: объект задания OlympiadTask
        participation: объект участия OlympiadParticipation
    
    Returns:
        bool: True, если задание решено правильно, иначе False
    """
    if not task or not participation:
        return False
    
    submission = task.submissions.filter(
        participation=participation,
        is_correct=True
    ).first()
    
    return submission is not None

@register.filter
def is_attempted(task, participation):
    """
    Проверяет, была ли попытка решить задание пользователем
    
    Args:
        task: объект задания OlympiadTask
        participation: объект участия OlympiadParticipation
    
    Returns:
        bool: True, если была попытка решить задание, иначе False
    """
    if not task or not participation:
        return False
    
    submission = task.submissions.filter(
        participation=participation
    ).exists()
    
    return submission

@register.filter
def attempts_count(task, participation):
    """
    Возвращает количество попыток решения задания пользователем
    
    Args:
        task: объект задания OlympiadTask
        participation: объект участия OlympiadParticipation
    
    Returns:
        int: количество попыток
    """
    if not task or not participation:
        return 0
    
    return task.submissions.filter(
        participation=participation
    ).count()

@register.filter
def max_score(task, participation):
    """
    Возвращает максимальный балл за задание
    
    Args:
        task: объект задания OlympiadTask
        participation: объект участия OlympiadParticipation
    
    Returns:
        int: максимальный балл
    """
    if not task:
        return 0
    
    return task.points

@register.filter
def get_score(task, participation):
    """
    Возвращает набранные баллы за задание
    
    Args:
        task: объект задания OlympiadTask
        participation: объект участия OlympiadParticipation
    
    Returns:
        int: набранные баллы
    """
    if not task or not participation:
        return 0
    
    submission = task.submissions.filter(
        participation=participation,
    ).order_by('-score').first()
    
    return submission.score if submission else 0

@register.filter
def format_time_remaining(milliseconds):
    """
    Форматирует оставшееся время в удобный для чтения формат
    
    Args:
        milliseconds: оставшееся время в миллисекундах
    
    Returns:
        str: отформатированная строка времени
    """
    if milliseconds <= 0:
        return "00:00:00"
    
    # Переводим в секунды
    seconds = milliseconds // 1000
    
    # Рассчитываем часы, минуты и секунды
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    
    # Если больше 24 часов, показываем в днях
    if hours >= 24:
        days = hours // 24
        hours %= 24
        return f"{days}д {hours:02d}:{minutes:02d}:{seconds:02d}"
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

@register.filter
def get_best_submission(task, participation):
    """
    Возвращает лучшую отправку для задания
    
    Args:
        task: объект задания OlympiadTask
        participation: объект участия OlympiadParticipation
    
    Returns:
        OlympiadTaskSubmission: лучшая отправка или None
    """
    if not task or not participation:
        return None
    
    return task.submissions.filter(
        participation=participation
    ).order_by('-score', '-submitted_at').first()

@register.filter
def format_time(seconds):
    """
    Форматирует время выполнения в удобный для чтения формат
    
    Args:
        seconds: время в секундах
    
    Returns:
        str: отформатированная строка времени
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.2f} мкс"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} мс"
    else:
        return f"{seconds:.2f} сек"

@register.filter
def format_memory(megabytes):
    """
    Форматирует объем используемой памяти в удобный для чтения формат
    
    Args:
        megabytes: объем памяти в мегабайтах
    
    Returns:
        str: отформатированная строка объема памяти
    """
    if megabytes < 0.1:
        return f"{megabytes * 1024:.2f} КБ"
    else:
        return f"{megabytes:.2f} МБ"