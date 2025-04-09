from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import NotificationSettings
from gamification.models import Achievement, Badge
from courses.models import Course, Lesson, Enrollment, LessonCompletion
from assignments.models import Assignment, AssignmentSubmission

User = get_user_model()


@receiver(post_save, sender=User)
def create_notification_settings(sender, instance, created, **kwargs):
    """Создает настройки уведомлений для нового пользователя"""
    if created:
        NotificationSettings.objects.create(user=instance)


@receiver(post_save, sender=Achievement)
def notify_achievement(sender, instance, created, **kwargs):
    """Отправляет уведомление о получении достижения"""
    from .models import Notification
    
    if created:  # Только для новых достижений
        # Получаем настройки уведомлений пользователя
        try:
            settings = NotificationSettings.objects.get(user=instance.user)
            
            # Проверяем, может ли пользователь получить уведомление этого типа
            if settings.can_receive_notification('achievement', instance.is_significant):
                # Создаем уведомление
                Notification.objects.create(
                    user=instance.user,
                    title=_('Новое достижение получено!'),
                    message=f'Вы получили достижение "{instance.title}". {instance.description}',
                    notification_type='achievement',
                    is_high_priority=instance.is_significant,
                    content_type=instance.content_type,
                    object_id=instance.object_id
                )
        except NotificationSettings.DoesNotExist:
            # Если настроек нет, просто создаем их, но уведомление не отправляем
            NotificationSettings.objects.create(user=instance.user)


@receiver(post_save, sender=Badge)
def notify_badge(sender, instance, created, **kwargs):
    """Отправляет уведомление о получении значка"""
    from .models import Notification
    
    if instance.is_awarded and not instance.notification_sent:
        # Получаем настройки уведомлений пользователя
        try:
            settings = NotificationSettings.objects.get(user=instance.user)
            
            # Проверяем, может ли пользователь получить уведомление этого типа
            if settings.can_receive_notification('achievement', True):  # Значки всегда высокоприоритетны
                # Создаем уведомление
                Notification.objects.create(
                    user=instance.user,
                    title=_('Новый значок получен!'),
                    message=f'Вы получили значок "{instance.title}". {instance.description}',
                    notification_type='achievement',
                    is_high_priority=True
                )
                
                # Отмечаем, что уведомление о значке отправлено
                instance.notification_sent = True
                instance.save(update_fields=['notification_sent'])
        except NotificationSettings.DoesNotExist:
            # Если настроек нет, просто создаем их, но уведомление не отправляем
            NotificationSettings.objects.create(user=instance.user)


@receiver(post_save, sender=Course)
def notify_course_update(sender, instance, created, **kwargs):
    """Отправляет уведомление об обновлении курса всем учащимся"""
    from .models import Notification
    from django.db.models import Q
    
    # Если курс не опубликован, уведомления не отправляем
    if not instance.is_published:
        return
        
    # Определяем тип события
    if created:
        title = _('Новый курс доступен')
        message = f'Опубликован новый курс "{instance.title}". {instance.short_description}'
    else:
        # Если это не новый курс, проверяем, отмечен ли он как обновленный
        if not getattr(instance, 'updated_flag', False):
            return
            
        title = _('Курс обновлен')
        message = f'Курс "{instance.title}" был обновлен. Проверьте новое содержимое.'
    
    # Получаем всех пользователей, записанных на курс
    enrollments = Enrollment.objects.filter(course=instance, is_active=True)
    
    # Отправляем уведомление каждому пользователю
    for enrollment in enrollments:
        try:
            settings = NotificationSettings.objects.get(user=enrollment.student)
            
            # Проверяем, может ли пользователь получить уведомление этого типа
            if settings.can_receive_notification('course', False):
                # Создаем уведомление
                Notification.objects.create(
                    user=enrollment.student,
                    title=title,
                    message=message,
                    notification_type='course',
                    is_high_priority=False,
                    content_type=instance.content_type,
                    object_id=instance.id,
                    url=f'/courses/{instance.id}/'
                )
        except NotificationSettings.DoesNotExist:
            # Если настроек нет, просто создаем их, но уведомление не отправляем
            NotificationSettings.objects.create(user=enrollment.student)


@receiver(post_save, sender=Lesson)
def notify_lesson_update(sender, instance, created, **kwargs):
    """Отправляет уведомление о новом уроке всем учащимся курса"""
    from .models import Notification
    
    # Если урок не опубликован или курс не опубликован, уведомления не отправляем
    if not instance.is_published or not instance.course.is_published:
        return
        
    # Определяем тип события
    if created:
        title = _('Новый урок доступен')
        message = f'В курсе "{instance.course.title}" добавлен новый урок "{instance.title}".'
    else:
        # Если это не новый урок, проверяем, отмечен ли он как обновленный
        if not getattr(instance, 'updated_flag', False):
            return
            
        title = _('Урок обновлен')
        message = f'Урок "{instance.title}" в курсе "{instance.course.title}" был обновлен.'
    
    # Получаем всех пользователей, записанных на курс
    enrollments = Enrollment.objects.filter(course=instance.course, is_active=True)
    
    # Отправляем уведомление каждому пользователю
    for enrollment in enrollments:
        try:
            settings = NotificationSettings.objects.get(user=enrollment.student)
            
            # Проверяем, может ли пользователь получить уведомление этого типа
            if settings.can_receive_notification('lesson', False):
                # Создаем уведомление
                Notification.objects.create(
                    user=enrollment.student,
                    title=title,
                    message=message,
                    notification_type='lesson',
                    is_high_priority=False,
                    content_type=instance.content_type,
                    object_id=instance.id,
                    url=f'/courses/{instance.course.id}/lessons/{instance.id}/'
                )
        except NotificationSettings.DoesNotExist:
            # Если настроек нет, просто создаем их, но уведомление не отправляем
            NotificationSettings.objects.create(user=enrollment.student)


@receiver(post_save, sender=AssignmentSubmission)
def notify_assignment_submission(sender, instance, created, **kwargs):
    """Отправляет уведомление о проверке решения задания"""
    from .models import Notification
    
    # Нас интересуют только изменения статуса существующих отправок
    if created:
        return
        
    # Проверяем, изменился ли статус (например, на "проверено")
    if not getattr(instance, 'status_changed', False):
        return
        
    # Определяем сообщение в зависимости от статуса
    if instance.status == 'approved':
        title = _('Решение задания одобрено')
        message = f'Ваше решение задания "{instance.assignment.title}" было одобрено!'
        is_high_priority = True
    elif instance.status == 'rejected':
        title = _('Решение задания требует доработки')
        message = f'Ваше решение задания "{instance.assignment.title}" требует доработки. Проверьте комментарии преподавателя.'
        is_high_priority = True
    elif instance.status == 'checking':
        title = _('Решение задания на проверке')
        message = f'Ваше решение задания "{instance.assignment.title}" принято на проверку.'
        is_high_priority = False
    else:
        # Для других статусов уведомления не отправляем
        return
    
    try:
        settings = NotificationSettings.objects.get(user=instance.user)
        
        # Проверяем, может ли пользователь получить уведомление этого типа
        if settings.can_receive_notification('assignment', is_high_priority):
            # Создаем уведомление
            Notification.objects.create(
                user=instance.user,
                title=title,
                message=message,
                notification_type='assignment',
                is_high_priority=is_high_priority,
                content_type=instance.content_type,
                object_id=instance.id,
                url=f'/assignments/{instance.assignment.id}/submissions/{instance.id}/'
            )
    except NotificationSettings.DoesNotExist:
        # Если настроек нет, просто создаем их, но уведомление не отправляем
        NotificationSettings.objects.create(user=instance.user)


# Функция отправки email-уведомлений
def send_email_notification(notification):
    """Отправляет уведомление на email пользователя"""
    from django.core.mail import send_mail
    from django.conf import settings as django_settings
    
    # Проверяем настройки уведомлений пользователя
    try:
        user_settings = NotificationSettings.objects.get(user=notification.user)
        
        # Если email-уведомления отключены, ничего не делаем
        if not user_settings.email_notifications:
            return
            
        # Если уведомления только для важных, и это не важное, ничего не делаем
        if user_settings.notify_only_high_priority and not notification.is_high_priority:
            return
    except NotificationSettings.DoesNotExist:
        # Если настроек нет, ничего не делаем
        return
    
    # Получаем email пользователя
    user_email = notification.user.email
    
    # Если email не указан, ничего не делаем
    if not user_email:
        return
    
    # Формируем тему и текст письма
    subject = f'ПроОбучение: {notification.title}'
    
    # Формируем текст письма
    message = f"""
    Здравствуйте, {notification.user.get_full_name() or notification.user.username}!
    
    {notification.message}
    
    ------------------------------
    Это автоматическое уведомление от платформы ПроОбучение.
    Для изменения настроек уведомлений перейдите по ссылке: {django_settings.SITE_URL}/notifications/settings/
    """
    
    # Отправляем письмо
    try:
        # Если настроен SendGrid, используем его
        if hasattr(django_settings, 'SENDGRID_API_KEY') and django_settings.SENDGRID_API_KEY:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            message = Mail(
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                to_emails=user_email,
                subject=subject,
                plain_text_content=message
            )
            
            try:
                sg = SendGridAPIClient(django_settings.SENDGRID_API_KEY)
                sg.send(message)
            except Exception as e:
                # Логгируем ошибку, но не прерываем выполнение
                print(f"Ошибка отправки через SendGrid: {e}")
        else:
            # Используем стандартную отправку Django
            send_mail(
                subject=subject,
                message=message,
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email]
            )
    except Exception as e:
        # Логгируем ошибку, но не прерываем выполнение
        print(f"Ошибка отправки email: {e}")


# Регистрируем сигнал для отправки email при создании уведомления
@receiver(post_save, sender='notifications.Notification')
def send_notification_email(sender, instance, created, **kwargs):
    """Отправляет email при создании нового уведомления"""
    if created:
        # Отправляем email
        send_email_notification(instance)