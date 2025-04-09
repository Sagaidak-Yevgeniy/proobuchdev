"""
Кастомные представления для административного интерфейса Django
"""

from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth import REDIRECT_FIELD_NAME, login
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie


class AdminLoginView(LoginView):
    """
    Кастомное представление для входа в административный интерфейс Django
    с поддержкой работы на Replit.
    """
    template_name = 'admin/login.html'
    form_class = AdminAuthenticationForm

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        # Применяем наш декоратор для обеспечения CSRF защиты
        return ensure_csrf_cookie(view)

    def get_success_url(self):
        url = self.get_redirect_url()
        return url or resolve_url(reverse('admin:index'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('Log in'),
            'app_path': self.request.get_full_path(),
            'next': self.request.GET.get(REDIRECT_FIELD_NAME, ''),
            **(self.extra_context or {}),
        })
        return context