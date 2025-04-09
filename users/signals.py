from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Profile, UserInterface

@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    """Создает профиль пользователя при создании нового пользователя"""
    # Если профиль уже создан в форме регистрации, не будем его пересоздавать
    if created and not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_profile(sender, instance, **kwargs):
    """Сохраняет профиль пользователя при обновлении пользователя"""
    # Проверяем, существует ли профиль, чтобы не перезаписывать его
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        try:
            profile = Profile.objects.get(user=instance)
            profile.save()
        except Profile.DoesNotExist:
            Profile.objects.create(user=instance)

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
