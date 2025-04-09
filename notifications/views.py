from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from .models import Notification, NotificationSettings
from .forms import NotificationSettingsForm


@login_required
def notification_list(request):
    """Отображает список уведомлений пользователя"""
    # Получаем все уведомления пользователя, отсортированные по дате (новые сверху)
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Подсчитываем количество непрочитанных уведомлений
    unread_count = notifications.filter(is_read=False).count()
    
    # Если запрос требует JSON-ответа (для API)
    if request.GET.get('format') == 'json':
        notifications_data = []
        
        # Конвертируем уведомления в JSON
        for notification in notifications[:10]:  # Возвращаем только 10 последних уведомлений
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'is_read': notification.is_read,
                'is_high_priority': notification.is_high_priority,
                'url': notification.url,
                'created_at': notification.created_at.isoformat(),
            })
        
        # Возвращаем JSON-ответ
        return JsonResponse({
            'notifications': notifications_data,
            'unread_count': unread_count,
        })
    
    # Пагинация для обычного HTML-ответа
    paginator = Paginator(notifications, 10)  # 10 уведомлений на страницу
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Отображение шаблона
    return render(request, 'notifications/notification_list.html', {
        'notifications': page_obj,
        'unread_count': unread_count,
        'has_unread': unread_count > 0,
    })


@login_required
def notification_count(request):
    """Возвращает количество непрочитанных уведомлений для API"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return JsonResponse({
        'count': count
    })


@login_required
@require_POST
def mark_notification_as_read(request, notification_id):
    """Отмечает уведомление как прочитанное"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    # Отмечаем как прочитанное
    notification.is_read = True
    notification.save(update_fields=['is_read', 'updated_at'])
    
    # Возвращаем обновленное количество непрочитанных уведомлений
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return JsonResponse({
        'success': True,
        'unread_count': unread_count
    })


@login_required
@require_POST
def mark_all_as_read(request):
    """Отмечает все уведомления пользователя как прочитанные"""
    # Получаем все непрочитанные уведомления и отмечаем их как прочитанные
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    notifications.update(is_read=True, updated_at=timezone.now())
    
    return JsonResponse({
        'success': True,
        'count': notifications.count()
    })


@login_required
@require_POST
def delete_notification(request, notification_id):
    """Удаляет уведомление"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    # Удаляем уведомление
    notification.delete()
    
    # Возвращаем обновленное количество непрочитанных уведомлений
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return JsonResponse({
        'success': True,
        'unread_count': unread_count
    })


@login_required
def notification_settings(request):
    """Страница настроек уведомлений пользователя"""
    # Получаем или создаем настройки уведомлений пользователя
    settings, created = NotificationSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = NotificationSettingsForm(request.POST, instance=settings)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки уведомлений успешно сохранены')
            return redirect('notifications:notification_settings')
        
    else:
        form = NotificationSettingsForm(instance=settings)
    
    return render(request, 'notifications/notification_settings.html', {
        'form': form
    })