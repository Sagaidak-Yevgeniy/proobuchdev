"""
URL configuration for educational_platform project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from .admin_views import AdminLoginView

# Переопределяем URL для входа в административный интерфейс
admin.site.login = AdminLoginView.as_view()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('users/', include('users.urls')),
    path('courses/', include('courses.urls')),
    path('lessons/', include('lessons.urls')),
    path('assignments/', include('assignments.urls')),
    path('gamification/', include('gamification.urls')),
    path('ai/', include('ai_assistant.urls')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('dashboard/', include('dashboard.urls')),
    path('olympiads/', include('olympiads.urls', namespace='olympiads')),
]

# Добавляем обработку медиа-файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
