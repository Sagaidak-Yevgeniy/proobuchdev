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