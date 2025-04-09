from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Widget, DashboardLayout

User = get_user_model()


@receiver(post_save, sender=User)
def create_default_dashboard_layout(sender, instance, created, **kwargs):
    """Создает стандартный макет дашборда для нового пользователя"""
    if created:
        DashboardLayout.objects.create(
            user=instance,
            theme='light',
            animation_speed='normal',
            layout={'widgets': []}
        )