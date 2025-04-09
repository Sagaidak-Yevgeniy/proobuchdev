from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Profile, UserInterface
from notifications.models import Notification

@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    """Создает профиль пользователя при создании нового пользователя"""
    # Если профиль уже создан в форме регистрации, не будем его пересоздавать
    if created:
        # Проверяем, существует ли уже профиль для этого пользователя
        if not Profile.objects.filter(user=instance).exists():
            # Только если профиль ещё не создан, создаем его с ролью студента по умолчанию
            print(f"DEBUG Signal: Creating default profile for user {instance.username}")
            Profile.objects.create(user=instance, role=Profile.STUDENT)
        else:
            print(f"DEBUG Signal: Profile already exists for user {instance.username}, not creating default")

@receiver(post_save, sender=CustomUser)
def save_profile(sender, instance, **kwargs):
    """Сохраняет профиль пользователя при обновлении пользователя"""
    # Проверяем, существует ли профиль, чтобы не перезаписывать его
    if hasattr(instance, 'profile'):
        # Если у нас уже есть связь с профилем, просто сохраняем его
        instance.profile.save()
        print(f"DEBUG Signal: Saving existing profile relation for user {instance.username}")
    else:
        try:
            # Пробуем найти профиль в базе данных
            profile = Profile.objects.get(user=instance)
            # Нашли профиль, сохраняем его
            profile.save()
            print(f"DEBUG Signal: Saving found profile for user {instance.username}")
        except Profile.DoesNotExist:
            # Профиль не найден, создаем новый с ролью студента по умолчанию
            print(f"DEBUG Signal: Creating missing profile for user {instance.username}")
            Profile.objects.create(user=instance, role=Profile.STUDENT)

@receiver(post_save, sender=CustomUser)
def create_user_interface(sender, instance, created, **kwargs):
    """Создает настройки интерфейса при создании нового пользователя"""
    if created:
        UserInterface.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_interface(sender, instance, **kwargs):
    """Сохраняет настройки интерфейса при обновлении пользователя"""
    try:
        instance.interface.save()
    except UserInterface.DoesNotExist:
        UserInterface.objects.create(user=instance)

@receiver(post_save, sender=Profile)
def send_welcome_notification(sender, instance, created, **kwargs):
    """
    Отправляет приветственное уведомление пользователю в зависимости от его роли
    ПРИМЕЧАНИЕ: Функционал отключен по запросу пользователя.
    """
    # Функционал отключен
    return None
