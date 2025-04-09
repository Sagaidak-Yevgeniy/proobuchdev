"""
Модуль для решения проблем с CSRF в среде Replit через кастомный middleware.
"""

from django.middleware.csrf import CsrfViewMiddleware, get_token
from django.views.decorators.csrf import ensure_csrf_cookie as django_ensure_csrf_cookie
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from functools import wraps

# Реэкспортируем стандартную функцию ensure_csrf_cookie для совместимости
ensure_csrf_cookie = django_ensure_csrf_cookie


class CustomCsrfMiddleware(CsrfViewMiddleware):
    """
    Кастомный middleware, который перехватывает ошибки CSRF и
    перенаправляет пользователя на предыдущую страницу с сообщением об ошибке,
    вместо показа стандартной страницы с ошибкой 403.
    """
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        """
        Переопределяем стандартную обработку CSRF для более дружественного UX.
        """
        # Вызываем стандартную проверку CSRF
        result = super().process_view(request, callback, callback_args, callback_kwargs)
        
        # Если нет ошибки CSRF (result = None), просто пропускаем запрос
        if result is None:
            return None
        
        # Если ошибка в запросе не POST, обрабатываем по умолчанию
        if request.method != 'POST':
            return result
        
        # Если есть ошибка CSRF и это POST-запрос, делаем редирект
        # с информативным сообщением
        referer = request.META.get('HTTP_REFERER', '/')
        
        # Логируем ошибку CSRF для отладки
        if settings.DEBUG:
            print(f"CSRF Error: {request.path}, Referer: {referer}")
            print(f"CSRF Cookie: {request.COOKIES.get('csrftoken')}")
            print(f"CSRF Token in POST: {request.POST.get('csrfmiddlewaretoken')}")
        
        # Добавляем сообщение об ошибке
        if hasattr(request, '_messages'):
            messages.error(
                request,
                "Произошла ошибка безопасности (CSRF). "
                "Пожалуйста, повторите отправку формы."
            )
        
        # Для форм авторизации перенаправляем на страницу входа
        if request.path == reverse('login'):
            return HttpResponseRedirect(reverse('login'))
        
        # Для форм регистрации перенаправляем на страницу регистрации
        if request.path == reverse('register'):
            return HttpResponseRedirect(reverse('register'))
            
        # В остальных случаях возвращаем на предыдущую страницу или на главную
        return HttpResponseRedirect(referer)


def csrf_failure_view(request, reason=""):
    """
    Кастомная обработка ошибок CSRF для более дружественного UX.
    Перенаправляет пользователя на предыдущую страницу с сообщением об ошибке.
    """
    # Получаем предыдущую страницу или используем главную страницу
    referer = request.META.get('HTTP_REFERER', '/')
    
    # Логируем ошибку CSRF для отладки
    if settings.DEBUG:
        print(f"CSRF Failure View: {request.path}, Reason: {reason}")
        print(f"Referer: {referer}")
        print(f"CSRF Cookie: {request.COOKIES.get('csrftoken')}")
    
    # Добавляем сообщение об ошибке
    if hasattr(request, '_messages'):
        messages.error(
            request,
            "Произошла ошибка безопасности (CSRF). "
            "Пожалуйста, повторите отправку формы."
        )
    
    # Для форм авторизации перенаправляем на страницу входа
    if request.path == reverse('login'):
        return HttpResponseRedirect(reverse('login'))
    
    # Для форм регистрации перенаправляем на страницу регистрации
    if request.path == reverse('register'):
        return HttpResponseRedirect(reverse('register'))
        
    # В остальных случаях возвращаем на предыдущую страницу или на главную
    return HttpResponseRedirect(referer)