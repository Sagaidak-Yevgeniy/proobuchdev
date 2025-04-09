from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

import json
import logging

from .models import Notification, NotificationSettings, DeviceToken, NotificationChannel
from .forms import NotificationSettingsForm, DeviceTokenForm, QuietHoursForm
from .services import NotificationService

logger = logging.getLogger(__name__)


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
    
    # Получаем список устройств пользователя
    devices = DeviceToken.objects.filter(user=request.user)
    
    # Получаем список каналов уведомлений
    channels = NotificationChannel.objects.filter(is_active=True)
    
    return render(request, 'notifications/notification_settings.html', {
        'form': form,
        'devices': devices,
        'channels': channels,
        'preferred_channels': list(settings.preferred_channels.all().values_list('id', flat=True)),
    })


@login_required
@csrf_exempt
def register_device(request):
    """Регистрирует новое устройство для получения push-уведомлений"""
    if request.method == 'POST':
        try:
            # Получаем данные из JSON
            data = json.loads(request.body)
            token = data.get('token')
            device_type = data.get('device_type', 'web')
            device_name = data.get('device_name', '')
            
            if not token:
                return JsonResponse({
                    'success': False,
                    'error': 'Необходимо указать токен устройства'
                }, status=400)
            
            # Проверяем, существует ли уже такой токен
            device, created = DeviceToken.objects.get_or_create(
                user=request.user,
                token=token,
                defaults={
                    'device_type': device_type,
                    'device_name': device_name,
                    'is_active': True
                }
            )
            
            # Если устройство уже существует, но неактивно, активируем его
            if not created and not device.is_active:
                device.is_active = True
                device.device_type = device_type
                device.device_name = device_name
                device.save()
            
            # Включаем push-уведомления в настройках пользователя
            try:
                settings = NotificationSettings.objects.get(user=request.user)
                if not settings.push_notifications:
                    settings.push_notifications = True
                    settings.save(update_fields=['push_notifications'])
            except NotificationSettings.DoesNotExist:
                NotificationSettings.objects.create(
                    user=request.user,
                    push_notifications=True
                )
            
            return JsonResponse({
                'success': True,
                'device_id': device.id,
                'message': 'Устройство успешно зарегистрировано'
            })
            
        except Exception as e:
            logger.error(f"Ошибка при регистрации устройства: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при регистрации устройства'
            }, status=500)
    
    # Если запрос не POST, возвращаем форму для регистрации устройства
    form = DeviceTokenForm()
    
    return render(request, 'notifications/register_device.html', {
        'form': form
    })


@login_required
@require_POST
def remove_device(request):
    """Удаляет устройство из списка для push-уведомлений"""
    try:
        # Получаем данные из JSON или POST
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            device_id = data.get('device_id')
            token = data.get('token')
        else:
            device_id = request.POST.get('device_id')
            token = request.POST.get('token')
        
        # Определяем по каким параметрам искать устройство
        if device_id:
            device = get_object_or_404(DeviceToken, id=device_id, user=request.user)
        elif token:
            device = get_object_or_404(DeviceToken, token=token, user=request.user)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Необходимо указать ID устройства или токен'
            }, status=400)
        
        # Деактивируем устройство (не удаляем)
        device.is_active = False
        device.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Устройство успешно удалено'
        })
        
    except Exception as e:
        logger.error(f"Ошибка при удалении устройства: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Произошла ошибка при удалении устройства'
        }, status=500)


@login_required
def device_list(request):
    """Возвращает список устройств пользователя"""
    devices = DeviceToken.objects.filter(user=request.user)
    
    if request.GET.get('format') == 'json':
        devices_data = []
        
        for device in devices:
            devices_data.append({
                'id': device.id,
                'token': device.token[:8] + '...',  # Показываем только начало токена
                'device_type': device.device_type,
                'device_name': device.device_name,
                'is_active': device.is_active,
                'created_at': device.created_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'devices': devices_data
        })
    
    return render(request, 'notifications/device_list.html', {
        'devices': devices
    })


@login_required
def channel_list(request):
    """Отображает и управляет каналами уведомлений"""
    try:
        settings = NotificationSettings.objects.get(user=request.user)
    except NotificationSettings.DoesNotExist:
        settings = NotificationSettings.objects.create(user=request.user)
    
    # Получаем список всех каналов
    channels = NotificationChannel.objects.filter(is_active=True)
    
    # Получаем предпочитаемые каналы пользователя
    preferred_channels = settings.preferred_channels.all()
    
    if request.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'channels': list(channels.values('id', 'name', 'channel_type', 'description')),
            'preferred_channels': list(preferred_channels.values_list('id', flat=True))
        })
    
    return render(request, 'notifications/channel_list.html', {
        'channels': channels,
        'preferred_channels': preferred_channels
    })


@login_required
@require_POST
def toggle_channel(request, channel_type):
    """Включает или выключает канал уведомлений"""
    try:
        settings = NotificationSettings.objects.get(user=request.user)
    except NotificationSettings.DoesNotExist:
        settings = NotificationSettings.objects.create(user=request.user)
    
    # Включаем или выключаем соответствующую настройку
    if channel_type == 'email':
        settings.email_notifications = not settings.email_notifications
        settings.save(update_fields=['email_notifications'])
        state = settings.email_notifications
    elif channel_type == 'push':
        settings.push_notifications = not settings.push_notifications
        settings.save(update_fields=['push_notifications'])
        state = settings.push_notifications
    else:
        # Для других типов каналов
        try:
            channel = NotificationChannel.objects.get(channel_type=channel_type, is_active=True)
            
            # Если канал есть в предпочитаемых - удаляем, иначе добавляем
            if channel in settings.preferred_channels.all():
                settings.preferred_channels.remove(channel)
                state = False
            else:
                settings.preferred_channels.add(channel)
                state = True
        except NotificationChannel.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Указанный канал не найден'
            }, status=404)
    
    return JsonResponse({
        'success': True,
        'channel': channel_type,
        'state': state
    })


@login_required
@require_POST
def toggle_quiet_hours(request):
    """Включает или выключает тихие часы"""
    try:
        settings = NotificationSettings.objects.get(user=request.user)
    except NotificationSettings.DoesNotExist:
        settings = NotificationSettings.objects.create(user=request.user)
    
    settings.quiet_hours_enabled = not settings.quiet_hours_enabled
    settings.save(update_fields=['quiet_hours_enabled'])
    
    return JsonResponse({
        'success': True,
        'quiet_hours_enabled': settings.quiet_hours_enabled
    })


@login_required
@require_POST
def update_quiet_hours(request):
    """Обновляет настройки тихих часов"""
    try:
        settings = NotificationSettings.objects.get(user=request.user)
    except NotificationSettings.DoesNotExist:
        settings = NotificationSettings.objects.create(user=request.user)
    
    form = QuietHoursForm(request.POST)
    
    if form.is_valid():
        settings.quiet_hours_enabled = form.cleaned_data['enabled']
        settings.quiet_hours_start = form.cleaned_data['start_time']
        settings.quiet_hours_end = form.cleaned_data['end_time']
        settings.save()
        
        messages.success(request, 'Настройки тихих часов успешно обновлены.')
    else:
        messages.error(request, 'При обновлении настроек произошла ошибка. Проверьте введенные данные.')
    
    return redirect('notifications:notification_settings')