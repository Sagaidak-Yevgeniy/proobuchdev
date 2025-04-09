from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from .models import Notification, NotificationSettings
from users.models import CustomUser
from gamification.models import Achievement, UserAchievement, Badge, UserBadge
from courses.models import Course
# Закомментируем импорт, так как модели пока не используются
# from assignments.models import Assignment, AssignmentSubmission


User = get_user_model()


@receiver(post_save, sender=User)
def create_notification_settings(sender, instance, created, **kwargs):
    """Создает настройки уведомлений для нового пользователя"""
    if created:
        # Проверяем, существуют ли уже настройки
        if not NotificationSettings.objects.filter(user=instance).exists():
            try:
                # Используем наш безопасный метод создания настроек
                NotificationSettings.create_with_defaults(instance)
                print(f"DEBUG: Created safe notification settings for user {instance.username}")
            except Exception as e:
                print(f"ERROR: Failed to create notification settings: {str(e)}")
                # Если произошла ошибка, попробуем традиционный способ создания
                NotificationSettings.objects.create(
                    user=instance,
                    receive_all=True,
                    notify_only_high_priority=False,
                    receive_achievement=True,
                    receive_course=True,
                    receive_lesson=True,
                    receive_assignment=True,
                    receive_message=True,
                    receive_system=True,
                    receive_deadline=True,
                    email_notifications=True,
                    email_digest=False,
                    push_notifications=False,
                    quiet_hours_enabled=False
                )


@receiver(post_save, sender=UserAchievement)
def notify_achievement_earned(sender, instance, created, **kwargs):
    """Отправляет уведомление о получении достижения"""
    if created:
        achievement = instance.achievement
        user = instance.user
        
        # Проверяем настройки пользователя
        try:
            settings = NotificationSettings.objects.get(user=user)
            if not settings.should_receive('achievement', False):
                return
        except NotificationSettings.DoesNotExist:
            pass
        
        Notification.objects.create(
            user=user,
            title=_('Новое достижение!'),
            message=_(f'Вы получили достижение "{achievement.name}": {achievement.description}'),
            notification_type='achievement',
            is_high_priority=False,
            url=f'/gamification/achievements/',
            importance='normal'
        )


@receiver(post_save, sender=UserBadge)
def notify_badge_earned(sender, instance, created, **kwargs):
    """Отправляет уведомление о получении значка"""
    if created:
        badge = instance.badge
        user = instance.user
        
        # Проверяем настройки пользователя
        try:
            settings = NotificationSettings.objects.get(user=user)
            if not settings.should_receive('achievement', True):
                return
        except NotificationSettings.DoesNotExist:
            pass
        
        Notification.objects.create(
            user=user,
            title=_('Новый значок!'),
            message=_(f'Вы получили значок "{badge.name}" за ваши достижения! {badge.description}'),
            notification_type='achievement',
            is_high_priority=True,
            url=f'/gamification/badges/',
            importance='high'
        )


@receiver(post_save, sender=Course)
def notify_course_creation(sender, instance, created, **kwargs):
    """Отправляет уведомление о создании нового курса"""
    if created and instance.is_published:
        # Получаем пользователей, которые должны получать уведомления о курсах
        users_settings = NotificationSettings.objects.filter(receive_course=True).select_related('user')
        
        print(f"Найдено {users_settings.count()} пользователей с настройками получения уведомлений о курсах")
        
        for settings in users_settings:
            # Если пользователь настроил получение только важных, пропускаем
            if settings.notify_only_high_priority:
                print(f"Пользователь {settings.user.username} настроил получение только важных уведомлений")
                continue
                
            print(f"Создаем уведомление для пользователя {settings.user.username} о новом курсе {instance.title}")
            Notification.objects.create(
                user=settings.user,
                title=_('Новый курс!'),
                message=_(f'Появился новый курс "{instance.title}". {instance.description[:100]}...'),
                notification_type='course',
                is_high_priority=False,
                url=f'/courses/{instance.slug}/',
                importance='normal'
            )
            print(f"Уведомление создано для пользователя {settings.user.username}")


@receiver(post_save, sender=Course)
def notify_course_update(sender, instance, created, **kwargs):
    """Отправляет уведомление об обновлении курса его участникам"""
    if not created and instance.is_published:
        # Получаем студентов, которые записаны на этот курс
        enrollments = instance.enrollments.select_related('user').all()
        
        print(f"Найдено {enrollments.count()} записей на курс {instance.title}")
        
        for enrollment in enrollments:
            user = enrollment.user
            try:
                settings = NotificationSettings.objects.get(user=user)
                print(f"Проверяем настройки пользователя {user.username} для уведомлений о курсах")
                if not settings.should_receive('course', False):
                    print(f"Пользователь {user.username} отключил уведомления о курсах")
                    continue
            except NotificationSettings.DoesNotExist:
                print(f"У пользователя {user.username} нет настроек уведомлений")
                continue
            
            print(f"Создаем уведомление для пользователя {user.username} о курсе {instance.title}")
            Notification.objects.create(
                user=user,
                title=_('Обновление курса'),
                message=_(f'Курс "{instance.title}" был обновлен.'),
                notification_type='course',
                is_high_priority=False,
                url=f'/courses/{instance.slug}/',
                importance='normal'
            )
            print(f"Уведомление создано для пользователя {user.username}")


from lessons.models import Lesson

@receiver(post_save, sender=Lesson)
def notify_lesson_creation(sender, instance, created, **kwargs):
    """Отправляет уведомление о создании нового урока студентам курса"""
    print(f"Сигнал notify_lesson_creation сработал. created={created}, lesson={instance.title}")
    
    # Изменили условие: убрали проверку instance.is_published, т.к. урок может быть не опубликован, 
    # но преподаватель добавил его в курс, и студенты должны знать об этом
    if created and hasattr(instance, 'course') and instance.course.is_published:
        print(f"Урок соответствует условиям для отправки уведомлений: course={instance.course.title}, is_published={instance.is_published}")
        
        # Получаем студентов, которые записаны на этот курс
        enrolled_users = instance.course.enrollments.select_related('user').all()
        print(f"Найдено {enrolled_users.count()} студентов, записанных на курс {instance.course.title}")
        
        for enrollment in enrolled_users:
            user = enrollment.user
            try:
                settings = NotificationSettings.objects.get(user=user)
                print(f"Проверяем настройки пользователя {user.username} для уведомлений об уроках")
                if not settings.should_receive('lesson', False):
                    print(f"Пользователь {user.username} отключил уведомления об уроках")
                    continue
            except NotificationSettings.DoesNotExist:
                print(f"У пользователя {user.username} нет настроек уведомлений")
                continue
            
            status_text = "доступен" if instance.is_published else "скоро будет доступен"
            
            print(f"Создаем уведомление для пользователя {user.username} о новом уроке {instance.title}")
            Notification.objects.create(
                user=user,
                title=_('Новый урок в курсе'),
                message=_(f'В курсе "{instance.course.title}" появился новый урок: "{instance.title}" ({status_text})'),
                notification_type='lesson',
                is_high_priority=False,
                url=f'/courses/{instance.course.slug}/lessons/{instance.id}/',
                importance='normal'
            )
            print(f"Уведомление создано для пользователя {user.username}")


@receiver(post_save, sender=Lesson)
def notify_lesson_update(sender, instance, created, **kwargs):
    """Отправляет уведомление об обновлении урока студентам"""
    print(f"Сигнал notify_lesson_update сработал. created={created}, lesson={instance.title}")
    
    # Изменили условие: убрали проверку instance.is_published, т.к. когда урок становится опубликованным
    # это важное обновление, о котором студенты должны узнать
    if not created and hasattr(instance, 'course') and instance.course.is_published:
        print(f"Урок соответствует условиям для отправки уведомлений об обновлении: course={instance.course.title}, is_published={instance.is_published}")
        
        # Получаем студентов, которые записаны на этот курс
        enrolled_users = instance.course.enrollments.select_related('user').all()
        print(f"Найдено {enrolled_users.count()} студентов, записанных на курс {instance.course.title}")
        
        for enrollment in enrolled_users:
            user = enrollment.user
            try:
                settings = NotificationSettings.objects.get(user=user)
                print(f"Проверяем настройки пользователя {user.username} для уведомлений об уроках")
                if not settings.should_receive('lesson', False):
                    print(f"Пользователь {user.username} отключил уведомления об уроках")
                    continue
            except NotificationSettings.DoesNotExist:
                print(f"У пользователя {user.username} нет настроек уведомлений")
                continue
            
            status_info = ""
            # Добавляем информацию о статусе публикации
            status_info = " Урок " + ("доступен" if instance.is_published else "недоступен") + " для прохождения."
            
            print(f"Создаем уведомление для пользователя {user.username} об обновлении урока {instance.title}")
            Notification.objects.create(
                user=user,
                title=_('Обновление урока'),
                message=_(f'Урок "{instance.title}" в курсе "{instance.course.title}" был обновлен.{status_info}'),
                notification_type='lesson',
                is_high_priority=False,
                url=f'/courses/{instance.course.slug}/lessons/{instance.id}/',
                importance='normal'
            )
            print(f"Уведомление создано для пользователя {user.username}")


# Когда модели заданий будут доступны, раскомментируйте этот код
# @receiver(post_save, sender=Assignment)
# def notify_assignment_creation(sender, instance, created, **kwargs):
#     """Отправляет уведомление о создании нового задания студентам"""
#     if created and instance.lesson_content and instance.lesson_content.lesson:
#         lesson = instance.lesson_content.lesson
#         course = lesson.course
#         
#         if course.is_published:
#             # Получаем студентов курса
#             enrolled_users = course.students.all()
#             
#             for user in enrolled_users:
#                 try:
#                     settings = NotificationSettings.objects.get(user=user)
#                     if not settings.should_receive('assignment', True):
#                         continue
#                 except NotificationSettings.DoesNotExist:
#                     continue
#                 
#                 Notification.objects.create(
#                     user=user,
#                     title=_('Новое задание'),
#                     message=_(f'В уроке "{lesson.title}" появилось новое задание: "{instance.title}"'),
#                     notification_type='assignment',
#                     is_high_priority=True,
#                     url=f'/courses/{course.slug}/lessons/{lesson.slug}/#assignment-{instance.id}',
#                     importance='high'
#                 )


# @receiver(post_save, sender=AssignmentSubmission)
# def notify_submission_graded(sender, instance, **kwargs):
#     """Отправляет уведомление студенту о проверке его решения"""
#     if instance.status in ['passed', 'failed'] and not instance.is_auto_checked:
#         # Уведомление отправляется только если статус изменился на "проверено"
#         # и оценка была выставлена преподавателем, а не автоматически
#         
#         user = instance.user
#         assignment = instance.assignment
#         
#         try:
#             settings = NotificationSettings.objects.get(user=user)
#             if not settings.should_receive('assignment', True):
#                 return
#         except NotificationSettings.DoesNotExist:
#             pass
#         
#         lesson_content = assignment.lesson_content
#         lesson = lesson_content.lesson
#         course = lesson.course
#         
#         status_text = _("принято") if instance.status == 'passed' else _("не принято")
#         
#         Notification.objects.create(
#             user=user,
#             title=_('Задание проверено'),
#             message=_(f'Ваше решение задания "{assignment.title}" было проверено. Статус: {status_text}'),
#             notification_type='assignment',
#             is_high_priority=True,
#             url=f'/courses/{course.slug}/lessons/{lesson.slug}/#assignment-{assignment.id}',
#             importance='high'
#         )


# Функции для отправки Email-уведомлений

from django.core.mail import send_mail
from django.conf import settings


def send_email_notification(user, subject, message, html_message=None):
    """Отправляет email уведомление пользователю"""
    try:
        # Проверяем настройки пользователя
        user_settings = NotificationSettings.objects.get(user=user)
        if not user_settings.email_notifications:
            return False
            
        # Если у пользователя нет email, отправка невозможна
        if not user.email:
            return False
            
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {str(e)}")
        return False


# SendGrid для более продвинутых email-уведомлений
def send_sendgrid_email(user, subject, text_content, html_content=None):
    """Отправляет красивое HTML-уведомление через SendGrid"""
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content

        # Проверяем настройки пользователя
        user_settings = NotificationSettings.objects.get(user=user)
        if not user_settings.email_notifications:
            return False
            
        # Если у пользователя нет email, отправка невозможна
        if not user.email:
            return False
        
        # Получаем API ключ из настроек
        if not hasattr(settings, 'SENDGRID_API_KEY') or not settings.SENDGRID_API_KEY:
            # Если нет ключа SendGrid, используем обычную отправку
            return send_email_notification(user, subject, text_content, html_content)
        
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        
        from_email = Email(settings.DEFAULT_FROM_EMAIL)
        to_email = To(user.email)
        
        if html_content:
            content = Content("text/html", html_content)
        else:
            content = Content("text/plain", text_content)
            
        mail = Mail(from_email, to_email, subject, content)
        
        # Отправляем сообщение
        response = sg.client.mail.send.post(request_body=mail.get())
        
        return response.status_code in [200, 201, 202]
    except Exception as e:
        print(f"Ошибка отправки SendGrid email: {str(e)}")
        return False