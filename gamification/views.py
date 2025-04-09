from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count

from users.models import CustomUser
from .models import Achievement, UserAchievement, Badge, UserBadge, PointsHistory


@login_required
def achievement_list(request):
    """Отображает список достижений пользователя и доступных достижений"""
    # Получаем достижения пользователя
    user_achievements = UserAchievement.objects.filter(user=request.user)
    user_achievement_ids = user_achievements.values_list('achievement_id', flat=True)
    
    # Получаем видимые достижения, которых у пользователя еще нет
    available_achievements = Achievement.objects.filter(is_hidden=False).exclude(id__in=user_achievement_ids)
    
    # Получаем количество очков пользователя
    total_points = PointsHistory.objects.filter(user=request.user).aggregate(total=Sum('points'))['total'] or 0
    
    # Получаем значки пользователя
    user_badges = UserBadge.objects.filter(user=request.user)
    
    context = {
        'user_achievements': user_achievements,
        'available_achievements': available_achievements,
        'total_points': total_points,
        'user_badges': user_badges,
    }
    
    return render(request, 'gamification/achievement_list.html', context)


@login_required
def achievement_detail(request, pk):
    """Отображает детальную информацию о достижении"""
    achievement = get_object_or_404(Achievement, pk=pk)
    
    # Проверяем, если это скрытое достижение, которого нет у пользователя, то редиректим на список
    if achievement.is_hidden and not UserAchievement.objects.filter(user=request.user, achievement=achievement).exists():
        return redirect('achievement_list')
    
    # Получаем пользователей, которые получили это достижение
    achievement_users = UserAchievement.objects.filter(achievement=achievement).order_by('-earned_at')[:10]
    
    # Проверяем, есть ли это достижение у текущего пользователя
    user_has_achievement = UserAchievement.objects.filter(user=request.user, achievement=achievement).exists()
    
    context = {
        'achievement': achievement,
        'achievement_users': achievement_users,
        'user_has_achievement': user_has_achievement,
    }
    
    return render(request, 'gamification/achievement_detail.html', context)


@login_required
def leaderboard(request):
    """Отображает таблицу лидеров по очкам и достижениям"""
    # Получаем топ пользователей по очкам
    top_users_by_points = PointsHistory.objects.values('user').annotate(
        total_points=Sum('points')
    ).order_by('-total_points')[:20]
    
    # Добавляем информацию о пользователях и количестве достижений
    leaderboard_users = []
    for entry in top_users_by_points:
        user = CustomUser.objects.get(id=entry['user'])
        achievement_count = UserAchievement.objects.filter(user=user).count()
        badge_count = UserBadge.objects.filter(user=user).count()
        
        leaderboard_users.append({
            'user': user,
            'total_points': entry['total_points'],
            'achievement_count': achievement_count,
            'badge_count': badge_count,
        })
    
    # Определяем позицию текущего пользователя
    current_user_points = PointsHistory.objects.filter(user=request.user).aggregate(
        total=Sum('points')
    )['total'] or 0
    
    # Находим позицию пользователя (количество пользователей с большим количеством очков + 1)
    current_user_position = PointsHistory.objects.values('user').annotate(
        total_points=Sum('points')
    ).filter(total_points__gt=current_user_points).count() + 1
    
    context = {
        'leaderboard_users': leaderboard_users,
        'current_user_points': current_user_points,
        'current_user_position': current_user_position,
    }
    
    return render(request, 'gamification/leaderboard.html', context)


@login_required
def badge_list(request):
    """Отображает список значков пользователя и доступных значков"""
    # Получаем значки пользователя
    user_badges = UserBadge.objects.filter(user=request.user)
    user_badge_ids = user_badges.values_list('badge_id', flat=True)
    
    # Получаем значки, которых у пользователя еще нет
    available_badges = Badge.objects.exclude(id__in=user_badge_ids).order_by('required_points')
    
    # Получаем количество очков пользователя
    total_points = PointsHistory.objects.filter(user=request.user).aggregate(total=Sum('points'))['total'] or 0
    
    context = {
        'user_badges': user_badges,
        'available_badges': available_badges,
        'total_points': total_points,
    }
    
    return render(request, 'gamification/badge_list.html', context)


@login_required
def user_gamification_profile(request, user_id):
    """Отображает игровой профиль пользователя"""
    user = get_object_or_404(CustomUser, pk=user_id)
    
    # Получаем достижения пользователя
    user_achievements = UserAchievement.objects.filter(user=user)
    
    # Получаем значки пользователя
    user_badges = UserBadge.objects.filter(user=user)
    
    # Получаем количество очков пользователя
    total_points = PointsHistory.objects.filter(user=user).aggregate(total=Sum('points'))['total'] or 0
    
    # Получаем статистику по типам достижений
    achievement_stats = UserAchievement.objects.filter(user=user).values(
        'achievement__type'
    ).annotate(count=Count('id')).order_by('achievement__type')
    
    # Получаем историю очков
    points_history = PointsHistory.objects.filter(user=user).order_by('-created_at')[:10]
    
    context = {
        'profile_user': user,
        'user_achievements': user_achievements,
        'user_badges': user_badges,
        'total_points': total_points,
        'achievement_stats': achievement_stats,
        'points_history': points_history,
    }
    
    return render(request, 'gamification/user_gamification_profile.html', context)