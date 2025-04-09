from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Фильтр Django для получения значения из словаря по ключу.
    Используется в шаблонах для доступа к вложенным словарям.
    
    Пример использования:
    {{ my_dict|get_item:my_key }}
    
    Args:
        dictionary: Словарь, из которого нужно получить значение
        key: Ключ для поиска в словаре
        
    Returns:
        Значение по ключу или None, если ключ не найден
    """
    if dictionary is None:
        return None
    
    try:
        return dictionary.get(key)
    except (AttributeError, KeyError, TypeError):
        return None

@register.filter
def filter_passed(test_results):
    """
    Фильтр для подсчета количества пройденных тестов.
    
    Args:
        test_results: Список результатов тестов
        
    Returns:
        Количество пройденных тестов
    """
    if not test_results:
        return 0
    
    return sum(1 for result in test_results if result.passed)

@register.simple_tag
def widthratio(value, max_value, scale):
    """
    Вычисляет соотношение между value и max_value, умноженное на scale.
    Безопасно обрабатывает случай деления на ноль.
    
    Args:
        value: Числитель
        max_value: Знаменатель
        scale: Множитель (обычно 100 для процентов)
        
    Returns:
        Вычисленное значение или 0, если max_value = 0
    """
    try:
        return int(float(value) / float(max_value) * float(scale))
    except (ValueError, ZeroDivisionError):
        return 0