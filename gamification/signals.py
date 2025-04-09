from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from users.models import CustomUser
from .models import Achievement, UserAchievement, Badge, UserBadge, PointsHistory


@receiver(post_save, sender=UserAchievement)
def award_achievement_points(sender, instance, created, **kwargs):
    """Начисляет очки пользователю при получении достижения"""
    if created:
        points = instance.achievement.points
        # Добавляем запись в историю очков
        PointsHistory.objects.create(
            user=instance.user,
            points=points,
            action='achievement',
            description=f'Получено достижение: {instance.achievement.name}'
        )

        # Проверяем, следует ли выдать пользователю новые значки
        check_badges_for_user(instance.user)


def check_badges_for_user(user):
    """Проверяет, следует ли выдать пользователю новые значки"""
    # Получаем все значки, которые пользователь еще не имеет, отсортированные по требуемым очкам
    user_badges = UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    available_badges = Badge.objects.exclude(id__in=user_badges).order_by('required_points')
    
    # Получаем общее количество очков пользователя из истории
    from django.db.models import Sum
    total_points = PointsHistory.objects.filter(user=user).aggregate(total=Sum('points'))['total'] or 0
    
    # Выдаем все значки, для которых у пользователя достаточно очков
    for badge in available_badges:
        if total_points >= badge.required_points:
            UserBadge.objects.create(
                user=user,
                badge=badge
            )
            
            # Добавляем запись в историю очков о получении значка
            PointsHistory.objects.create(
                user=user,
                points=0,  # Значок сам по себе не дает очков
                action='other',
                description=f'Получен значок: {badge.name}'
            )