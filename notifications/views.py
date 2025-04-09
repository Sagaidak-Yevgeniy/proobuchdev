from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST

from .models import Notification, NotificationSettings
from .forms import NotificationSettingsForm


@login_required
def notification_list(request):
    """Отображает страницу со списком уведомлений пользователя"""
    # Получаем уведомления текущего пользователя
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Получаем количество непрочитанных уведомлений
    unread_count = notifications.filter(is_read=False).count()
    
    # Пагинация
    page = request.GET.get('page', 1)
    paginator = Paginator(notifications, 10)  # 10 уведомлений на страницу
    
    try:
        notifications_page = paginator.page(page)
    except PageNotAnInteger:
        notifications_page = paginator.page(1)
    except EmptyPage:
        notifications_page = paginator.page(paginator.num_pages)
    
    # Если запрос требует JSON-ответа
    if request.GET.get('format') == 'json':
        notifications_data = []
        
        for notification in notifications_page:
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
        
        return JsonResponse({
            'notifications': notifications_data,
            'unread_count': unread_count,
            'has_next': notifications_page.has_next(),
            'has_previous': notifications_page.has_previous(),
            'total_pages': paginator.num_pages,
            'current_page': notifications_page.number,
        })
    
    # Если обычный запрос HTML-страницы
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications_page,
        'unread_count': unread_count,
    })


@login_required
def notification_count(request):
    """Возвращает количество непрочитанных уведомлений для AJAX-запроса"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Отмечает уведомление как прочитанное"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    # Возвращаем обновленное количество непрочитанных уведомлений
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return JsonResponse({'success': True, 'unread_count': unread_count})


@login_required
@require_POST
def mark_all_read(request):
    """Отмечает все уведомления пользователя как прочитанные"""
    Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True, 
        updated_at=timezone.now()
    )
    
    return JsonResponse({'success': True})


@login_required
@require_POST
def delete_notification(request, notification_id):
    """Удаляет уведомление"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    
    # Возвращаем обновленное количество непрочитанных уведомлений
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return JsonResponse({'success': True, 'unread_count': unread_count})


@login_required
def notification_settings(request):
    """Отображает страницу с настройками уведомлений"""
    try:
        settings = NotificationSettings.objects.get(user=request.user)
    except NotificationSettings.DoesNotExist:
        settings = NotificationSettings.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = NotificationSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки уведомлений успешно сохранены.')
            return redirect('notifications:notification_settings')
    else:
        form = NotificationSettingsForm(instance=settings)
    
    return render(request, 'notifications/notification_settings.html', {
        'form': form,
    })