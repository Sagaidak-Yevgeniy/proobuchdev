from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from .models import Notification, NotificationSettings, DeviceToken

import logging
import json

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для работы с уведомлениями"""
    
    @classmethod
    def create_notification(cls, user, title, message, notification_type='info', 
                           importance='normal', is_high_priority=False, url=None, 
                           icon=None, extra_data=None, content_object=None):
        """
        Создает новое уведомление и отправляет его через настроенные каналы
        
        Args:
            user: Пользователь
            title (str): Заголовок уведомления
            message (str): Текст уведомления
            notification_type (str): Тип уведомления
            importance (str): Важность уведомления (low, normal, high, critical)
            is_high_priority (bool): Является ли уведомление высокоприоритетным
            url (str, optional): URL для перехода по уведомлению
            icon (str, optional): Иконка уведомления
            extra_data (dict, optional): Дополнительные данные
            content_object (Model, optional): Связанный объект
            
        Returns:
            Notification: Созданное уведомление или None в случае ошибки
        """
        try:
            # Получаем настройки пользователя
            try:
                settings = NotificationSettings.objects.get(user=user)
            except NotificationSettings.DoesNotExist:
                settings = NotificationSettings.objects.create(user=user)
            
            # Проверяем, должен ли пользователь получать это уведомление
            if not settings.should_receive(notification_type, importance):
                logger.info(f"Пользователь {user.username} отключил получение уведомлений типа {notification_type}")
                return None
            
            # Создаем уведомление
            notification_data = {
                'user': user,
                'title': title,
                'message': message,
                'notification_type': notification_type,
                'importance': importance,
                'is_high_priority': is_high_priority,
                'url': url,
                'icon': icon,
                'extra_data': extra_data,
            }
            
            # Если есть связанный объект, добавляем его
            if content_object:
                notification_data['content_type'] = ContentType.objects.get_for_model(content_object)
                notification_data['object_id'] = content_object.pk
            
            # Создаем уведомление в базе данных
            with transaction.atomic():
                notification = Notification.objects.create(**notification_data)
                
                # Отправляем уведомление через настроенные каналы
                cls.send_notification(notification, settings)
                
                return notification
                
        except Exception as e:
            logger.error(f"Ошибка при создании уведомления: {str(e)}")
            return None
    
    @classmethod
    def send_notification(cls, notification, settings=None):
        """
        Отправляет уведомление через настроенные каналы
        
        Args:
            notification: Уведомление для отправки
            settings: Настройки пользователя (если None, будет загружено из базы)
            
        Returns:
            dict: Результат отправки уведомления по каналам
        """
        try:
            # Если настройки не переданы, загружаем их
            if settings is None:
                try:
                    settings = NotificationSettings.objects.get(user=notification.user)
                except NotificationSettings.DoesNotExist:
                    settings = NotificationSettings.objects.create(user=notification.user)
            
            results = {'success': True, 'channels': {}}
            
            # Получаем список активных каналов
            channels = settings.get_active_channels()
            
            # Для каждого канала вызываем соответствующий метод отправки
            for channel in channels:
                try:
                    if channel == 'email':
                        # Для email проверяем, что уведомление достаточно важное
                        if notification.importance in ('high', 'critical') or not settings.notify_only_high_priority:
                            success = cls.send_email_notification(notification, settings)
                            results['channels']['email'] = success
                    elif channel == 'push':
                        # Для push-уведомлений проверяем тихие часы
                        if not settings.is_quiet_hours_now() or notification.importance == 'critical':
                            success = cls.send_push_notification(notification, settings)
                            results['channels']['push'] = success
                    elif channel == 'telegram':
                        success = cls.send_telegram_notification(notification, settings)
                        results['channels']['telegram'] = success
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления через канал {channel}: {str(e)}")
                    results['channels'][channel] = False
                    results['success'] = False
            
            return results
        
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_email_notification(notification, settings):
        """Отправляет уведомление по email"""
        user = notification.user
        
        if not user.email or not settings.email_notifications:
            logger.info(f"Email-уведомления отключены или не указан email для пользователя {user.username}")
            return False
        
        try:
            # Если включен дайджест, добавляем уведомление в очередь дайджеста
            if settings.email_digest:
                logger.info(f"Уведомление {notification.id} добавлено в очередь дайджеста для пользователя {user.username}")
                # Здесь может быть логика для сохранения уведомления в очередь дайджеста
                return True
            
            subject = notification.title
            
            # Подготавливаем контекст для шаблона
            context = {
                'notification': notification,
                'user': user,
                'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'ПроОбучение',
                'base_url': settings.BASE_URL if hasattr(settings, 'BASE_URL') else '',
            }
            
            # Рендерим HTML и текстовую версии письма
            html_content = render_to_string('notifications/email/notification.html', context)
            text_content = strip_tags(html_content)
            
            # Отправляем email
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=True
            )
            
            logger.info(f"Email-уведомление отправлено пользователю {user.username}: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке email-уведомления: {str(e)}")
            return False
    
    @staticmethod
    def send_push_notification(notification, settings):
        """Отправляет push-уведомление на устройства пользователя"""
        user = notification.user
        
        if not settings.push_notifications:
            logger.info(f"Push-уведомления отключены для пользователя {user.username}")
            return False
        
        try:
            # Получаем список активных устройств пользователя
            device_tokens = DeviceToken.objects.filter(user=user, is_active=True)
            
            if not device_tokens.exists():
                logger.info(f"У пользователя {user.username} нет зарегистрированных устройств для push-уведомлений")
                return False
            
            # Подготавливаем данные для отправки
            push_data = {
                'title': notification.title,
                'body': notification.message,
                'icon': notification.icon or 'default-icon.png',
                'url': notification.url or reverse('notifications:notification_list'),
                'notification_id': notification.id,
                'timestamp': int(notification.created_at.timestamp()),
                'notification_type': notification.notification_type,
                'importance': notification.importance,
            }
            
            # Если есть дополнительные данные, добавляем их
            if notification.extra_data:
                push_data.update(notification.extra_data)
            
            # Здесь может быть логика для отправки через различные сервисы (FCM, APNS и т.д.)
            # Для примера просто логируем
            logger.info(f"Push-уведомление для {device_tokens.count()} устройств пользователя {user.username}: {json.dumps(push_data)}")
            
            # Имитация успешной отправки
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке push-уведомления: {str(e)}")
            return False
    
    @staticmethod
    def send_telegram_notification(notification, settings):
        """Отправляет уведомление в Telegram"""
        # Этот метод зависит от наличия Telegram API ключа и дополнительной настройки
        user = notification.user
        
        logger.info(f"Отправка в Telegram для пользователя {user.username} не реализована")
        return False
    
    @classmethod
    def mark_all_as_read(cls, user):
        """Отмечает все уведомления пользователя как прочитанные"""
        try:
            count = Notification.objects.filter(user=user, is_read=False).update(
                is_read=True,
                updated_at=timezone.now()
            )
            logger.info(f"Отмечено {count} уведомлений как прочитанные для пользователя {user.username}")
            return count
        except Exception as e:
            logger.error(f"Ошибка при пометке уведомлений как прочитанные: {str(e)}")
            return 0
    
    @classmethod
    def delete_old_notifications(cls, days=30):
        """Удаляет старые уведомления"""
        try:
            threshold_date = timezone.now() - timezone.timedelta(days=days)
            count, _ = Notification.objects.filter(created_at__lt=threshold_date, is_read=True).delete()
            logger.info(f"Удалено {count} старых уведомлений")
            return count
        except Exception as e:
            logger.error(f"Ошибка при удалении старых уведомлений: {str(e)}")
            return 0