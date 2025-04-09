"""
Этот модуль содержит утилиты для работы с CSRF на платформе Replit.

ВНИМАНИЕ: Ранее здесь был хак для обхода CSRF защиты, 
но теперь мы используем стандартный подход Django с правильными настройками.
"""

import functools
from django.middleware.csrf import get_token

def ensure_csrf_cookie(view_func):
    """
    Декоратор, который гарантирует, что CSRF-токен доступен в куки.
    
    Это помогает обеспечить наличие CSRF-токена даже при первом запросе,
    что может быть полезно для систем, которые полагаются на JavaScript
    для отправки форм.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Генерируем CSRF-токен явно, чтобы он был установлен в куки
        get_token(request)
        
        # Вызываем оригинальное представление
        return view_func(request, *args, **kwargs)
    
    return wrapper

# Обратная совместимость со старым кодом
# В новом коде рекомендуется использовать ensure_csrf_cookie
csrf_exempt_with_token = ensure_csrf_cookie